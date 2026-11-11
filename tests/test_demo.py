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
        for game in rows:
            self.assertIn(game['homeTeam'], names)
            self.assertIn(game['awayTeam'], names)
            self.assertNotEqual(game['homeTeam'], game['awayTeam'])
            self.assertEqual(game['status'], 'scheduled')
        self.assertEqual([sum(0 <= g['dayOffset'] < d for g in rows) for d in (1, 3, 5, 7)],
                         [2, 3, 5, 7])
        page = (Path(__file__).resolve().parents[1] / 'matchups.html').read_text()
        self.assertIn("fetch('data/demo-schedule.json'", page)
        self.assertIn("eligibleGames(count)", page)
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
            self.assertAlmostEqual(teams['rows'][0]['threeMade'], 92 / 9)
            self.assertEqual(teams['rows'][0]['oppThreeMade'], 6.53)
            self.assertEqual(teams['rows'][0]['oppThreePct'], 31.68)
            status = json.loads((root / 'data' / 'refresh-status.json').read_text())
            self.assertIsNone(status['lastSuccessAt'])
            self.assertIn('demo only', status['outcome'])

if __name__ == '__main__':
    unittest.main()
