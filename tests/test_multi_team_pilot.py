import unittest
from scripts.validate_multi_team_pilot import validate_rows

def row(team, conf, points=80):
    return dict(team=team, conference=conf, games=3, wins=2, losses=1,
                ppg=points, oppPpg=70, offRating=115, defRating=100,
                netRating=15, scoringMargin=points-70)

class MultiTeamPilotTests(unittest.TestCase):
    def test_two_conferences(self):
        self.assertEqual(validate_rows([row('Duke','ACC'),row('Kansas','Big 12')])['teams'],2)
    def test_duplicate_casefold(self):
        with self.assertRaises(ValueError):
            validate_rows([row('Duke','ACC'),row('duke','Big 12')])
    def test_single_conference(self):
        with self.assertRaises(ValueError):
            validate_rows([row('Duke','ACC'),row('UNC','ACC')])
    def test_bad_margin(self):
        bad=row('Kansas','Big 12')
        bad['scoringMargin']=100
        with self.assertRaises(ValueError):
            validate_rows([row('Duke','ACC'),bad])
    def test_too_many_teams(self):
        with self.assertRaises(ValueError):
            validate_rows([row('Team'+str(i),'C'+str(i%2)) for i in range(13)])
    def test_no_rows(self):
        with self.assertRaises(ValueError):
            validate_rows([])

if __name__ == '__main__':
    unittest.main()
