import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from jose import jwt

from app.auth_extension import create_access_token


class AuthTokenTests(unittest.TestCase):
    def test_token_claims_use_utc_and_honor_zero_expiry_delta(self) -> None:
        fixed_now = datetime(2030, 1, 2, 3, 4, 5, tzinfo=UTC)
        with (
            patch("app.base.config.AuthConfig.JWT_SECRET", "test-secret"),
            patch("app.base.config.AuthConfig.JWT_ALGORITHM", "HS256"),
            patch("app.auth_extension.datetime") as datetime_mock,
        ):
            datetime_mock.now.return_value = fixed_now
            token = create_access_token("person@example.com", timedelta(0))

        claims = jwt.decode(
            token,
            "test-secret",
            algorithms=["HS256"],
            options={"verify_exp": False},
        )
        self.assertEqual(claims["iat"], int(fixed_now.timestamp()))
        self.assertEqual(claims["exp"], claims["iat"])


if __name__ == "__main__":
    unittest.main()
