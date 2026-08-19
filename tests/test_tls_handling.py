import unittest
from unittest.mock import patch

import requests

from app import (
    TOKEN_SERVICE_TLS_ERROR,
    TOKEN_SERVICE_UNAVAILABLE_ERROR,
    app,
    get_account_from_eat,
)


class TokenVerificationTlsTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch("app.requests.get", side_effect=requests.exceptions.SSLError("certificate failure"))
    def test_tls_failure_keeps_certificate_validation_enabled(self, mocked_get):
        jwt, account, error = get_account_from_eat("diagnostic-token")

        self.assertIsNone(jwt)
        self.assertIsNone(account)
        self.assertEqual(error, TOKEN_SERVICE_TLS_ERROR)
        self.assertEqual(mocked_get.call_args.kwargs.get("verify", True), True)

    @patch("app.requests.get", side_effect=requests.exceptions.SSLError("token=secret-value"))
    def test_verify_route_never_echoes_token_in_tls_error(self, _mocked_get):
        response = self.client.post("/api/verify-token", json={"eat_token": "secret-value"})

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"], TOKEN_SERVICE_TLS_ERROR)
        self.assertNotIn("secret-value", response.get_data(as_text=True))

    @patch("app.requests.get", side_effect=requests.exceptions.ConnectionError("unreachable"))
    def test_network_failure_is_reported_without_raw_exception(self, _mocked_get):
        jwt, account, error = get_account_from_eat("diagnostic-token")

        self.assertIsNone(jwt)
        self.assertIsNone(account)
        self.assertEqual(error, TOKEN_SERVICE_UNAVAILABLE_ERROR)


if __name__ == "__main__":
    unittest.main()
