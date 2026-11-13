"""Focused regression tests for the private, read-only consolidated audit report."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_private_expansion_readiness as audit


class ActionableExceptionTests(unittest.TestCase):
    def test_early_season_is_ranking_only_and_identity_crosscheck_is_safe(self):
        reference = {"schools": []}
        candidates = {"candidates": [
            {"name": "Alpha", "conference": "ACC"},
            {"name": "Bravo", "conference": "ACC"},
            {"name": "Charlie", "conference": "ACC"},
        ]}
        teams = [
            {"season": audit.SEASON, "team": "Alpha", "conference": "ACC", "games": 3},
            {"season": audit.SEASON, "team": "Bravo", "conference": "ACC", "games": 0},
        ]
        players = [
            {"season": audit.SEASON, "team": "Alpha", "name": "Player A", "games": 2},
            {"season": audit.SEASON, "team": "Bravo", "name": "Player B", "games": 1},
        ]

        def fake_prepare(rows):
            source = rows[0]
            return {"rows": [{"games": source["games"], "wins": source["games"], "losses": 0}]}

        with (
            patch.object(audit, "validate_reference", return_value={}),
            patch.object(audit, "validate_candidates"),
            patch.object(audit, "membership_audit", return_value={
                "conference_results": {"ACC": {"status": "ROSTER_ALIGNED_NOT_NCAA_VERIFIED"}},
                "counts": {},
            }),
            patch.object(audit, "player_audit", return_value={}),
            patch.object(audit, "prepare", side_effect=fake_prepare),
            patch.object(audit, "player_row", side_effect=lambda row: row),
        ):
            report = audit.evaluate(teams, players, reference, candidates)

        self.assertEqual(report["statistical_exception_summary"]["schools_requiring_statistical_review"], 2)
        self.assertEqual(report["statistical_exception_summary"]["under_five_games_ranking_only"], 1)
        self.assertEqual(
            [row["school"] for row in report["statistical_exception_report"]],
            ["Bravo", "Charlie"],
        )
        self.assertEqual(report["identity_crosscheck"]["both_team_and_player_identity_missing"], ["Charlie"])
        self.assertEqual(report["identity_crosscheck"]["player_missing_but_team_identity_matched"], [])
        self.assertEqual(report["identity_crosscheck"]["team_missing_but_player_identity_matched"], [])
        bravo = report["statistical_exception_report"][0]
        self.assertTrue(bravo["team_identity_matched"])
        self.assertTrue(bravo["player_identity_matched"])
        self.assertEqual(bravo["valid_team_record_count"], 0)
        self.assertEqual(report["publication"], "DISABLED")
        self.assertEqual(report["separate_coverage_gates"]["counts"]["team_and_player_stats_available_any_games"], 1)
        self.assertNotIn(
            "fewer_than_five_team_games",
            report["staged_school_names_requiring_statistical_review"],
        )


if __name__ == "__main__":
    unittest.main()
