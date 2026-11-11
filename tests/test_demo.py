"""Regression tests for synthetic demo generation; no API or repository writes."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_demo

class DemoGenerationTests(unittest.TestCase):
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
