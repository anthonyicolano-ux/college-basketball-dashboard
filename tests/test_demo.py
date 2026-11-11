"""Regression tests for synthetic demo generation; no API or repository writes."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_demo

class DemoGenerationTests(unittest.TestCase):
    def test_fictional_schedule_and_page_integration(self):
        schedule = json.loads((Path(__file__).resolve().parents[1] / 'data' / 'demo-schedule.json').read_text())
        self.assertTrue(schedule['demo'])
        self.assertEqual(schedule['mode'], 'rolling-fictional-calendar')
        self.assertEqual(schedule['season'], 2027)
        rows = schedule['rows']
        self.assertEqual(len({g['gameId'] for g in rows}), len(rows))
        self.assertGreaterEqual(sum(g['dayOffset'] == 0 for g in rows), 2)
        self.assertTrue(any(g['startTimeTbd'] for g in rows))
        self.assertTrue(any(g['neutralSite'] for g in rows))
        names = {'North Valley', 'Lake Institute', 'Cedar State',
                 'West Metro', 'Pine Coast', 'Red Mesa'}
        self.assertEqual(sum(g['status'] == 'final' for g in rows), 1)
        self.assertEqual(sum(g['status'] == 'scheduled' for g in rows), 7)
        for game in rows:
            self.assertIn(game['homeTeam'], names)
            self.assertIn(game['awayTeam'], names)
            self.assertNotEqual(game['homeTeam'], game['awayTeam'])
            self.assertIn(game['status'], ('scheduled', 'final'))
        self.assertEqual([sum(g['status'] == 'scheduled' and 0 <= g['dayOffset'] < d for g in rows) for d in (1, 3, 5, 7)],
                         [2, 3, 5, 7])
        page = (Path(__file__).resolve().parents[1] / 'matchups.html').read_text()
        self.assertIn("fetch('data/demo-schedule.json'", page)
        self.assertIn("eligibleGames(count)", page)
        self.assertIn("function upcomingGames()", page)
        self.assertIn("const game=upcomingGames().find", page)
        self.assertIn("upcomingGames().forEach", page)
        self.assertIn("!['scheduled','final'].includes(g.status)", page)
        self.assertIn("g.gameId===$('game').value", page)
        self.assertNotIn('const demoGames=[[', page)

    def test_matchup_fields_and_demo_safety(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'data').mkdir()
            with patch.object(build_demo, 'ROOT', root):
                build_demo.main()
            teams = json.loads((root / 'data' / 'teams.json').read_text())
            players = json.loads((root / 'data' / 'players.json').read_text())
            self.assertTrue(teams['demo'])
            self.assertTrue(players['demo'])
            self.assertEqual(len(teams['rows']), 6)
            self.assertEqual(len(players['rows']), 18)
            fields = ('threeMade', 'oppThreeMade', 'oppThreePct', 'oppFgPct',
                      'oppRebounds', 'oppAssists', 'turnoversForced', 'oppTurnovers')
            for team in teams['rows']:
                for field in fields:
                    self.assertIsInstance(team.get(field), (int, float), (team['team'], field))
                self.assertEqual(team['turnoversForced'], team['oppTurnovers'])
                self.assertAlmostEqual(team['netRating'], team['offRating'] - team['defRating'])
                self.assertAlmostEqual(team['scoringMargin'], team['ppg'] - team['oppPpg'])
                self.assertAlmostEqual(team['reboundingMargin'], team['rebounds'] - team['oppRebounds'])
            shooting = ('fgMade', 'fgAttempted', 'threeMade', 'threeAttempted', 'ftMade', 'ftAttempted')
            for player in players['rows']:
                for field in shooting:
                    self.assertIsInstance(player.get(field), int, (player['name'], field))
                self.assertAlmostEqual(player['fgPct'], 100 * player['fgMade'] / player['fgAttempted'])
                self.assertAlmostEqual(player['threePct'], 100 * player['threeMade'] / player['threeAttempted'])
                self.assertAlmostEqual(player['ftPct'], 100 * player['ftMade'] / player['ftAttempted'])
            app = (Path(__file__).resolve().parents[1] / 'assets' / 'app.js').read_text()
            self.assertIn("['netRating','Net/100']", app)
            for key, label in (('fgMade', 'FGM'), ('fgAttempted', 'FGA'), ('threeMade', '3PM'), ('threeAttempted', '3PA'), ('ftMade', 'FTM'), ('ftAttempted', 'FTA')):
                self.assertIn(f"['{key}','{label}']", app)
            self.assertIn("'fgMade','fgAttempted','threeMade','threeAttempted','ftMade','ftAttempted'].includes(key)", app)
            self.assertIn("['scoringMargin','Margin/G']", app)
            self.assertIn("['oppRebounds','Opp REB/G']", app)
            self.assertIn("['reboundingMargin','REB Margin']", app)
            page = (Path(__file__).resolve().parents[1] / 'players.html').read_text()
            self.assertIn('<select id="team">', page)
            self.assertIn('function updateTeamOptions()', app)
            self.assertIn("rows.filter(r=>!conf||r.conference===conf)", app)
            self.assertIn("teams.includes(previous)?previous:''", app)
            self.assertIn("(!team || r.team === team)", app)
            self.assertIn("$('team').addEventListener('change',render)", app)

            self.assertAlmostEqual(teams['rows'][0]['threeMade'], 92 / 9)
            self.assertEqual(teams['rows'][0]['oppThreeMade'], 6.53)
            self.assertEqual(teams['rows'][0]['oppThreePct'], 31.68)
            status = json.loads((root / 'data' / 'refresh-status.json').read_text())
            self.assertIsNone(status['lastSuccessAt'])
            self.assertIn('demo only', status['outcome'])

if __name__ == '__main__':
    unittest.main()
