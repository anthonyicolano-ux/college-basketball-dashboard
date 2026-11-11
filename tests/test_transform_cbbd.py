import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from transform_cbbd import team_row, player_row, private_validate

class TransformTests(unittest.TestCase):
    def setUp(self):
        self.team = {'season': 2027, 'team': 'Fictional Test U', 'conference': 'Demo', 'games': 2, 'wins': 1, 'losses': 1,
                     'teamStats': {'points': {'total': 160}, 'fieldGoals': {'made': 60, 'attempted': 120},
                                   'threePointFieldGoals': {'made': 20, 'attempted': 50}, 'freeThrows': {'made': 20, 'attempted': 30},
                                   'possessions': 140, 'rebounds': {'total': 70}, 'assists': 32, 'turnovers': {'total': 20}},
                     'opponentStats': {'points': {'total': 150}, 'possessions': 140}}
        self.player = {'season': 2027, 'team': 'Fictional Test U', 'name': 'Demo Player', 'games': 2, 'points': 40,
                       'rebounds': {'total': 12}, 'fieldGoals': {'made': 15, 'attempted': 30},
                       'threePointFieldGoals': {'made': 5, 'attempted': 10}, 'freeThrows': {'made': 5, 'attempted': 6},
                       'usage': None, 'offensiveRating': 112.5}

    def test_team_calculations(self):
        r = team_row(self.team)
        self.assertEqual(r['ppg'], 80)
        self.assertAlmostEqual(r['offRating'], 114.285714, places=5)
        self.assertAlmostEqual(r['eFg'], 58.333333, places=5)
        self.assertEqual(r['rebounds'], 35)

    def test_opponent_matchup_fields(self):
        self.team['opponentStats'].update({
            'threePointFieldGoals': {'made': 14, 'attempted': 40},
            'fieldGoals': {'made': 55, 'attempted': 130},
            'rebounds': {'total': 64}, 'assists': 26,
            'turnovers': {'total': 22}
        })
        r = team_row(self.team)
        self.assertEqual(r['threeMade'], 10)
        self.assertEqual(r['oppThreeMade'], 7)
        self.assertEqual(r['oppThreePct'], 35)
        self.assertAlmostEqual(r['oppFgPct'], 55 / 130 * 100)
        self.assertEqual(r['oppRebounds'], 32)
        self.assertEqual(r['oppAssists'], 13)
        self.assertEqual(r['turnoversForced'], 11)
        self.assertEqual(r['oppTurnovers'], 11)

    def test_missing_opponent_fields_are_not_zero(self):
        r = team_row(self.team)
        for field in ('oppThreeMade', 'oppThreePct', 'oppFgPct',
                      'oppRebounds', 'oppAssists', 'turnoversForced', 'oppTurnovers'):
            self.assertIsNone(r[field], field)

    def test_player_nested_fields(self):
        r = player_row(self.player)
        self.assertEqual(r['rebounds'], 12)
        self.assertEqual(r['fgPct'], 50)
        self.assertEqual(r['fgMade'], 15)
        self.assertEqual(r['fgAttempted'], 30)
        self.assertEqual(r['threeMade'], 5)
        self.assertEqual(r['threeAttempted'], 10)
        self.assertEqual(r['ftMade'], 5)
        self.assertEqual(r['ftAttempted'], 6)
        self.assertIsNone(r['usage'])

    def test_missing_and_zero_denominators(self):
        self.team['teamStats']['fieldGoals']['attempted'] = 0
        self.assertIsNone(team_row(self.team)['fgPct'])
        self.player.pop('rebounds')
        self.assertIsNone(player_row(self.player)['rebounds'])

    def test_reject_wrong_season(self):
        self.team['season'] = 2026
        with self.assertRaises(ValueError): team_row(self.team)

    def test_summary_only(self):
        report = private_validate([self.team], [self.player])
        self.assertEqual(report['teams']['records'], 1)
        self.assertEqual(report['players']['non_null']['usage'], 0)
        self.assertNotIn('Demo Player', str(report))
        self.assertIn('DISABLED', report['publication'])

if __name__ == '__main__': unittest.main()
