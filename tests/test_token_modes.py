import unittest
from unittest.mock import patch

from app import _token_candidates, get_account_from_eat


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class TokenModeTests(unittest.TestCase):
    def test_bare_token_checks_eat_then_access(self):
        self.assertEqual(
            _token_candidates("raw-token"),
            [("eatjwt", "raw-token"), ("access", "raw-token")],
        )

    def test_access_url_uses_access_mode_only(self):
        self.assertEqual(
            _token_candidates("https://example.test/callback?access=raw-access&x=1"),
            [("access", "raw-access")],
        )

    @patch(
        "app.requests.get",
        side_effect=[
            FakeResponse(401, {"status": "error", "message": "Invalid token"}),
            FakeResponse(401, {"status": "error", "message": "Invalid token"}),
            FakeResponse(
                200,
                {
                    "status": "success",
                    "token": "jwt-value",
                    "uid": "123",
                    "region": "IND",
                    "nickname": "Player",
                },
            ),
        ],
    )
    def test_bare_access_token_falls_back_to_access_endpoint(self, mocked_get):
        jwt, account, error = get_account_from_eat("raw-access")

        self.assertEqual(jwt, "jwt-value")
        self.assertEqual(account["uid"], "123")
        self.assertIsNone(error)
        self.assertIn("eatjwt=raw-access", mocked_get.call_args_list[0].args[0])
        self.assertIn("access=raw-access", mocked_get.call_args_list[2].args[0])

    @patch("app.FREEFIRE_API_KEY", "test-key")
    @patch(
        "app.requests.get",
        return_value=FakeResponse(
            200,
            {
                "success": True,
                "BearerAuth": "jwt-value",
                "uid": "123",
                "region": "IND",
                "nickname": "Player",
            },
        ),
    )
    def test_direct_access_token_uses_simbhau_provider(self, mocked_get):
        jwt, account, error = get_account_from_eat("raw-access")

        self.assertEqual(jwt, "jwt-value")
        self.assertEqual(account["uid"], "123")
        self.assertIsNone(error)
        self.assertEqual(
            mocked_get.call_args.kwargs["params"],
            {"access_token": "raw-access", "key": "test-key"},
        )
        self.assertIn("/accesstojwt/token", mocked_get.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
