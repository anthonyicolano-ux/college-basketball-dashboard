"""Prepare a private team-stats KV payload from a locally supplied CBBD JSON export.

No API calls, no KV writes, no GitHub publication. Output must be kept outside
the repository and may only be deployed after provider terms are satisfied.
Usage: python scripts/prepare_private_teams.py --input /private/team-records.json --output /private/teams-kv.json
"""
import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from transform_cbbd import SEASON, team_row

REQUIRED = ('team', 'games', 'ppg', 'oppPpg', 'offRating', 'defRating',
            'netRating', 'scoringMargin', 'rebounds', 'offRebounds',
            'defRebounds', 'oppRebounds', 'reboundingMargin')


def prepare(records):
    if not isinstance(records, list) or not records:
        raise ValueError('Expected a nonempty list of team season records')
    rows = [team_row(record) for record in records]
    if len({row['team'] for row in rows}) != len(rows):
        raise ValueError('Duplicate team names')
    for row in rows:
        if row['games'] <= 0 or any(row.get(field) is None for field in REQUIRED):
            raise ValueError('Incomplete required team statistics')
        if any(isinstance(value, float) and not math.isfinite(value)
               for value in row.values()):
            raise ValueError('Nonfinite statistic')
    return {
        'schemaVersion': 1,
        'season': SEASON,
        'seasonLabel': '2026–27',
        'scope': 'Private verified team season statistics',
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'demo': False,
        'rows': rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output == repo or repo in output.parents:
        parser.error('Output must be outside the public GitHub repository')
    if output.exists():
        parser.error('Refusing to overwrite an existing file')
    try:
        records = json.loads(args.input.read_text(encoding='utf-8'))
        dataset = prepare(records)
        output.write_text(json.dumps(dataset, ensure_ascii=False, allow_nan=False),
                          encoding='utf-8')
        output.chmod(0o600)
        print('PASS: private dataset prepared; team count:', len(dataset['rows']))
        print('No API requests, KV writes, or GitHub publication performed.')
    except (OSError, ValueError, TypeError, KeyError) as error:
        print('FAIL: private preparation (' + type(error).__name__ + '). No records printed.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
