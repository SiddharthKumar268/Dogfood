"""Local acceptance tests matching the run.py checker.
Run with unittest: python -m unittest tests/test_acceptance.py -v
Run with pytest:   pytest tests/test_acceptance.py -v
Requires: app running at http://localhost:8088 with seeded data
"""
import unittest
import requests

BASE = "http://localhost:8088"

# Session cookies for each role matching .dogfood.toml
ORGANIZER = {"session": "org_7f2a"}
JUDGE_A = {"session": "jdg_a_91bc"}
JUDGE_B = {"session": "jdg_b_44de"}
PARTICIPANT = {"session": "prt_2e88"}


class TestT1Gallery(unittest.TestCase):
    """T1: Gallery checks"""
    
    def test_gallery_no_auth_returns_200(self):
        """GET gallery with no auth should return 200"""
        resp = requests.get(f"{BASE}/projects", timeout=5)
        self.assertEqual(resp.status_code, 200)
    
    def test_gallery_contains_fixture_project(self):
        """Gallery body should contain a fixture project title"""
        resp = requests.get(f"{BASE}/projects", timeout=5)
        self.assertIn("HackTrack Pro", resp.text)
    
    def test_submit_closed_event_returns_4xx(self):
        """POST submit as participant with closed event should return 4xx"""
        resp = requests.post(
            f"{BASE}/projects/new",
            cookies=PARTICIPANT,
            json={
                "title": "Post-Deadline Test Project",
                "summary": "Should be rejected because event is closed",
                "description": "Attempted submission after deadline",
                "track": "Web Platform"
            },
            timeout=5
        )
        self.assertTrue(400 <= resp.status_code < 500, f"Expected 4xx, got {resp.status_code}")


class TestT2Judging(unittest.TestCase):
    """T2: Judging checks"""
    
    def test_judge_scores_own_returns_200(self):
        """GET judge_scores as judge_a should return 200"""
        resp = requests.get(f"{BASE}/api/judge/scores", cookies=JUDGE_A, timeout=5)
        self.assertEqual(resp.status_code, 200)
    
    def test_peer_scores_returns_403(self):
        """GET peer_scores as judge_b asking for judge_a's scores must return 401 or 403"""
        resp = requests.get(
            f"{BASE}/api/judge/scores?judge=judge_a",
            cookies=JUDGE_B,
            timeout=5
        )
        self.assertIn(resp.status_code, (401, 403))
    
    def test_participant_scores_returns_403(self):
        """GET judge_scores as participant must return 401 or 403"""
        resp = requests.get(f"{BASE}/api/judge/scores", cookies=PARTICIPANT, timeout=5)
        self.assertIn(resp.status_code, (401, 403))
    
    def test_csv_export_organizer_returns_200(self):
        """GET csv_export as organizer should return 200 with CSV content"""
        resp = requests.get(f"{BASE}/api/export.csv", cookies=ORGANIZER, timeout=5)
        self.assertEqual(resp.status_code, 200)
        first_line = resp.text.split('\n')[0]
        self.assertIn(',', first_line)  # CSV has commas


if __name__ == '__main__':
    unittest.main()
