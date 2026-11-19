"""Synthetic tests for KV staging. No network calls or real credentials."""
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch
import publish_private_kv as publisher


class MockResponse:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, count=-1):
        return b'{"success":true}'


class KvStagingTests(unittest.TestCase):
    def setUp(self):
        self.teams = Path("/synthetic/teams.json")
        self.players = Path("/synthetic/players.json")
        self.raw = {self.teams: b'{"teams":"fixture"}',
                    self.players: b'{"players":"fixture"}'}
        import hashlib
        self.manifest = {"teamCount":365, "playerCount":365,
                         "keys":{k:{"sha256":hashlib.sha256(self.raw[p]).hexdigest()}
                                 for k,p in (("teams",self.teams),("players",self.players))}}

    def test_staging_writes_two_keys_without_activation(self):
        requests = []
        def fake_open(request, timeout=30):
            requests.append(request)
            return MockResponse()
        def read_bytes(path):
            return self.raw[path]
        with patch.object(publisher, "release_manifest", return_value=self.manifest), \
             patch.object(Path, "read_bytes", read_bytes), \
             patch.object(publisher, "urlopen", side_effect=fake_open):
            result = publisher.publish(self.teams, self.players,
                                       account="test", namespace="test",
                                       token="synthetic")
        self.assertFalse(result["activated"])
        self.assertEqual(len(requests),2)
        self.assertTrue(all("active-release" not in req.full_url for req in requests))
        self.assertTrue(all(req.get_method()=="PUT" for req in requests))

    def test_failed_second_upload_never_activates(self):
        calls = []
        class FailedResponse(MockResponse):
            def read(self, count=-1):
                return b'{"success":false}'
        def fake_open(request, timeout=30):
            calls.append(request.full_url)
            return FailedResponse() if len(calls)==2 else MockResponse()
        with patch.object(publisher,"release_manifest",return_value=self.manifest), \
             patch.object(Path,"read_bytes",lambda path:self.raw[path]), \
             patch.object(publisher,"urlopen",side_effect=fake_open):
            with self.assertRaisesRegex(RuntimeError,"Versioned KV upload failed"):
                publisher.publish(self.teams,self.players,account="test",
                                  namespace="test",token="synthetic")
        self.assertEqual(len(calls),2)
        self.assertFalse(any("active-release" in url for url in calls))


if __name__=="__main__":
    unittest.main()
