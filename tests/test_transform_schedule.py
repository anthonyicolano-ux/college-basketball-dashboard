"""Offline, fictional schedule mapping tests. No network, no file writes."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from transform_schedule import game_row, private_validate

class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.game = {'id': 1001, 'season': 2027, 'startDate': '2026-11-15T19:30:00-06:00',
                     'homeTeam': 'North Valley', 'awayTeam': 'Cedar State',
                     'homeTeamId': 1, 'awayTeamId': 2, 'status': 'scheduled'}

    def test_normalization(self):
        row = game_row(self.game)
        self.assertEqual(row['gameId'], '1001')
        self.assertEqual(row['startUtc'], '2026-11-16T01:30:00Z')
        self.assertTrue(row['statusVerified'])
        self.assertFalse(row['startTimeTbd'])
        self.assertEqual(row['homeTeam'], 'North Valley')
        self.assertEqual(row['awayTeamId'], 2)

    def test_alternate_candidate_fields(self):
        self.game['gameId'] = self.game.pop('id')
        self.game['startTime'] = self.game.pop('startDate')
        self.assertEqual(game_row(self.game)['gameId'], '1001')

    def test_tbd_tipoff_does_not_claim_precise_start(self):
        self.game['startTimeTbd'] = True
        row = game_row(self.game)
        self.assertIsNone(row['startUtc'])
        self.assertEqual(row['gameDate'], '2026-11-15')
        self.assertTrue(row['startTimeTbd'])

    def test_tbd_date_only_is_supported_without_time(self):
        self.game.update(startTimeTbd=True, startDate='2026-11-15')
        row = game_row(self.game)
        self.assertIsNone(row['startUtc'])
        self.assertEqual(row['gameDate'], '2026-11-15')

    def test_invalid_tbd_flag_and_date_rejected(self):
        for value in ('true', 1, None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    game_row(dict(self.game, startTimeTbd=value))
        with self.assertRaises(ValueError):
            game_row(dict(self.game, startTimeTbd=True, startDate='bad-date'))

    def test_only_observed_status_values_are_verified(self):
        for value in ('scheduled', 'final', 'canceled', 'unrecognized'):
            with self.subTest(status=value):
                row = game_row(dict(self.game, status=value))
                self.assertEqual(row['status'], value)
                self.assertEqual(row['statusVerified'], value in ('scheduled', 'final'))

    def test_wrong_season_rejected(self):
        self.game['season'] = 2026
        with self.assertRaises(ValueError): game_row(self.game)

    def test_missing_or_ambiguous_fields_rejected(self):
        for key, value in [('startDate', '2026-11-15T19:30:00'),
                           ('startDate', 'not-a-date'), ('status', None),
                           ('homeTeam', 'Cedar State'), ('id', True)]:
            with self.subTest(key=key, value=value):
                changed = dict(self.game, **{key: value})
                with self.assertRaises(ValueError): game_row(changed)

    def test_duplicate_id_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            private_validate([self.game, dict(self.game)])

    def test_private_summary_only(self):
        result = private_validate([self.game])
        self.assertEqual(result['records'], 1)
        self.assertNotIn('North Valley', str(result))
        self.assertIn('DISABLED', result['publication'])

if __name__ == '__main__':
    unittest.main()
