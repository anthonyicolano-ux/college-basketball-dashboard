"""Private, manual, three-request integration check. No raw records are logged or saved."""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from transform_cbbd import team_row, player_row

BASE = 'https://api.collegebasketballdata.com'
PATHS = ('/stats/team/season', '/stats/player/season', '/games')
TEAM = 'Duke'
SEASON = 2027

def fetch(key, path):
    url = BASE + path + '?' + urlencode({'season': SEASON, 'team': TEAM})
    request = Request(url, headers={'Authorization': 'Bearer ' + key, 'Accept': 'application/json'})
    with urlopen(request, timeout=20) as response:
        payload = json.load(response)
    if not isinstance(payload, list) or not payload or any(not isinstance(r, dict) for r in payload):
        raise ValueError('Unexpected or empty API records')
    return payload

def validate(team_records, player_records, games):
    teams = [team_row(r) for r in team_records]
    players = [player_row(r) for r in player_records]
    failures = []
    team_fields = ('ppg','oppPpg','offRating','defRating','pace','fgPct','threePct','ftPct',
                   'eFg','tsPct','rebounds','offRebounds','defRebounds','oppRebounds',
                   'reboundingMargin','assists','turnovers')
    player_fields = ('points','rebounds','offRebounds','defRebounds','assists','steals',
                     'blocks','turnovers','fgMade','fgAttempted','threeMade',
                     'threeAttempted','ftMade','ftAttempted','fgPct','threePct','ftPct')
    def coverage(rows, fields):
        return {field: sum(isinstance(r.get(field), (int,float)) and not isinstance(r.get(field),bool)
                           for r in rows) for field in fields}
    def check(condition, code):
        if not condition:
            failures.append(code)
    def close(a,b):
        return a is not None and b is not None and abs(a-b)<1e-6
    for source, row in zip(team_records, teams):
        g = row['games']
        check(g > 0, 'team_games')
        check(close(row['ppg'] * g, source['teamStats']['points']['total']), 'team_ppg')
        check(close(row['offRebounds']+row['defRebounds'],row['rebounds']), 'team_rebound_sum')
        check(close(row['rebounds']-row['oppRebounds'],row['reboundingMargin']), 'team_rebound_margin')
        check(row['fgPct'] is not None and 0<=row['fgPct']<=100, 'team_fg_pct')
    for source, row in zip(player_records, players):
        check(row['games'] >= 0, 'player_games')
        check(close(row['offRebounds']+row['defRebounds'],row['rebounds']), 'player_rebound_sum')
        check(row['points'] == source['points'], 'player_points')
        check(row['fgPct'] is None or 0<=row['fgPct']<=100, 'player_fg_pct')
    statuses = {}
    date_formats = {'utc_z':0,'other':0,'missing':0}
    for game in games:
        status=game.get('status')
        if status not in ('scheduled','final'):
            failures.append('game_status')
        else:
            statuses[status]=statuses.get(status,0)+1
        dt=game.get('startDate')
        fmt='utc_z' if isinstance(dt,str) and dt.endswith('Z') and 'T' in dt else 'missing' if dt is None else 'other'
        date_formats[fmt]+=1
        check(isinstance(game.get('homeTeam'),str) and isinstance(game.get('awayTeam'),str), 'game_teams')
        check(isinstance(game.get('startTimeTbd'),bool), 'game_time_tbd')
    check(date_formats['other']==0 and date_formats['missing']==0,'game_date_format')
    check(bool(teams) and bool(players) and bool(games), 'nonempty')
    check(all(v==len(teams) for v in coverage(teams,team_fields).values()), 'team_required_coverage')
    check(all(v==len(players) for v in coverage(players,player_fields[:14]).values()), 'player_core_coverage')
    return {'result':'PASS' if not failures else 'FAIL',
            'record_counts':{'teams':len(teams),'players':len(players),'games':len(games)},
            'team_field_coverage':coverage(teams,team_fields),
            'player_field_coverage':coverage(players,player_fields),
            'game_status_counts':statuses,'game_date_formats':date_formats,
            'failed_checks':sorted(set(failures)),
            'note':'Private aggregate diagnostics only. No raw provider data published.'}

def main():
    key=os.environ.get('CBBD_API_KEY','').strip()
    if not key:
        print('FAIL: CBBD_API_KEY not configured. No requests made.')
        return 2
    try:
        results=[fetch(key,p) for p in PATHS]
        report=validate(*results)
        print(json.dumps(report,indent=2,sort_keys=True))
        return 0 if report['result']=='PASS' else 1
    except (HTTPError,URLError,TimeoutError,ValueError,KeyError,TypeError,ZeroDivisionError) as error:
        print('FAIL: API or data validation error ('+type(error).__name__+'). No raw data shown.')
        return 1

if __name__=='__main__':
    sys.exit(main())
