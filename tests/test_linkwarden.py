import io
import json
import subprocess
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import linkwarden


class LinkwardenTest(unittest.TestCase):
    def test_server_origin(self):
        self.assertEqual(linkwarden.server_origin("EXAMPLE.org:8443/"), "https://example.org:8443")
        self.assertEqual(linkwarden.server_origin("https://[::1]:8443"), "https://[::1]:8443")
        for value in (
            "http://example.org",
            "https://example.org/links",
            "https://example.org?redirect=other",
            "https://example.org@other.example",
            "https://example.org\\@other.example",
            "https://example.org:65536",
        ):
            with self.subTest(value=value):
                self.assertIsNone(linkwarden.server_origin(value))

    @patch("linkwarden.keyring")
    def test_store_keeps_server_and_token_together(self, keyring):
        keyring.return_value = subprocess.CompletedProcess([], 0)
        self.assertEqual(
            linkwarden.store_connection('{"server":"example.org","token":"test-token"}'),
            "stored",
        )
        self.assertEqual(
            json.loads(keyring.call_args.kwargs["secret"]),
            {"server": "https://example.org", "token": "test-token"},
        )

    @patch("linkwarden.keyring")
    @patch("linkwarden.build_opener")
    def test_save_uses_configured_server_and_unorganized(self, build_opener, keyring):
        keyring.return_value = subprocess.CompletedProcess(
            [], 0, '{"server":"https://example.org:8443","token":"test-token"}', ""
        )
        send = build_opener.return_value.open
        send.return_value = io.BytesIO(
            b'{"response":{"id":42,"collection":{"name":"Unorganized"}}}'
        )
        url = "https://example.com/?x=1&y=2"
        self.assertEqual(linkwarden.save_link(url), "saved")
        request = send.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.org:8443/api/v1/links")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        self.assertEqual(json.loads(request.data), {"url": url, "collection": {"name": "Unorganized"}})
        self.assertIsNone(build_opener.call_args.args[0].redirect_request(
            request, None, 302, "", {}, "https://other.example"
        ))

        send.side_effect = HTTPError(request.full_url, 401, "", {}, io.BytesIO())
        self.assertEqual(linkwarden.save_link(url), "unauthorized")

    @patch("linkwarden.keyring")
    @patch("linkwarden.build_opener")
    def test_unsafe_stored_endpoint_never_gets_token(self, build_opener, keyring):
        keyring.return_value = subprocess.CompletedProcess(
            [], 0, '{"server":"http://example.org","token":"test-token"}', ""
        )
        self.assertEqual(linkwarden.save_link("https://example.com"), "missing")
        build_opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
