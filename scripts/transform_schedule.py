"""Private, in-memory CBBD game normalization; never publishes provider records.

Core field names were confirmed in a private /games field report; status values
and timestamp formats were sampled privately; unknown values remain unverified. This module does not fetch or write any data.
"""
from datetime import datetime, timezone

SEASON = 2027

def _text(value):
    return value.strip() if isinstance(value, str) and value.strip() else None

def _first(record, *keys):
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return None

def _date(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            return None  # A time without an offset cannot safely be localized.
        return parsed.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    except ValueError:
        return None

def game_row(record):
    """Normalize a candidate provider-shaped record, failing closed on ambiguity."""
    if not isinstance(record, dict):
        raise ValueError('Invalid game record')
    if record.get('season') != SEASON:
        raise ValueError('Missing or incorrect season')
    game_id = _first(record, 'id', 'gameId')
    if isinstance(game_id, bool) or not isinstance(game_id, (str, int)) or not str(game_id).strip():
        raise ValueError('Missing game ID')
    home = _text(_first(record, 'homeTeam', 'home'))
    away = _text(_first(record, 'awayTeam', 'away'))
    if not home or not away or home == away:
        raise ValueError('Missing or invalid opponents')
    tbd = record.get('startTimeTbd', False)
    if not isinstance(tbd, bool):
        raise ValueError('Invalid startTimeTbd flag')
    raw_start = _first(record, 'startDate', 'startTime', 'date')
    start = _date(raw_start)
    if tbd:
        # A TBD start is not a reliable instant, even if the API supplies one.
        if not isinstance(raw_start, str) or len(raw_start) < 10:
            raise ValueError('Missing date for TBD game')
        try:
            datetime.strptime(raw_start[:10], '%Y-%m-%d')
        except ValueError as error:
            raise ValueError('Invalid date for TBD game') from error
        game_date = raw_start[:10]
        start = None
    elif start is None:
        raise ValueError('Missing or invalid timezone-aware game time')
    else:
        game_date = start[:10]
    status = _text(_first(record, 'status', 'gameStatus'))
    if not status:
        raise ValueError('Missing game status')
    # Only observed CBBD status labels are verified; all others fail closed.
    status_verified = status in ('scheduled', 'final')
    return {'gameId': str(game_id), 'season': SEASON, 'startUtc': start,
            'gameDate': game_date, 'startTimeTbd': tbd, 'statusVerified': status_verified,
            'homeTeam': home, 'awayTeam': away, 'status': status,
            'homeTeamId': _first(record, 'homeTeamId', 'homeId'),
            'awayTeamId': _first(record, 'awayTeamId', 'awayId')}

def private_validate(records):
    """QA only: return counts, not teams, dates, IDs, or raw records."""
    if not isinstance(records, list):
        raise ValueError('Expected a list of games')
    ids = set()
    for record in records:
        row = game_row(record)
        if row['gameId'] in ids:
            raise ValueError('Duplicate game ID')
        ids.add(row['gameId'])
    return {'records': len(records), 'unique_ids': len(ids),
            'publication': 'DISABLED: confirm schema and public redistribution rights'}
