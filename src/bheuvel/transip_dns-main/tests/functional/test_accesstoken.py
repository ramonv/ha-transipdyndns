# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
import json
from base64 import urlsafe_b64decode
from time import sleep

import pytest
from tests import transip_key_file, transip_user
from transip_dns import __project__, __version__
from transip_dns.accesstoken import AccessToken


def decode_jwt(jwt):  # pragma: not demo account skip demo coverage
    print(jwt)
    header = json.loads(urlsafe_b64decode(jwt.split(".")[0] + "=====").decode())
    payload = json.loads(urlsafe_b64decode(jwt.split(".")[1] + "=====").decode())
    return header, payload


@pytest.mark.skipif(
    transip_user is None, reason="Credentials for integration testing not provided"
)
class TestAccessToken:  # pragma: not demo account skip demo coverage
    @pytest.mark.parametrize("expiration_time", [10, 60])
    @pytest.mark.parametrize("global_key", [True, False])
    @pytest.mark.parametrize("read_only", [True, False])
    def test_tokengenerator(self, expiration_time, global_key, read_only):
        token = AccessToken(
            login=transip_user,
            private_key_file=transip_key_file,
            expiration_time=expiration_time,
            global_key=global_key,
            read_only=read_only,
            label=f"{__project__} {__version__}",
        )
        _, payload = decode_jwt(str(token))

        assert token.global_key == payload["gk"]
        assert token.read_only == payload["ro"]
        assert expiration_time == payload["exp"] - payload["iat"]
        # https://tools.ietf.org/html/rfc7519#section-4.1.6
        # Taking time difference and rounding (whole seconds) into account:
        assert payload["iat"] + 1 >= int(token._token_epoch) >= payload["iat"] - 1

    def test_token_re_generator(self):
        expiration_time = 5
        token = AccessToken(
            login=transip_user,
            private_key_file=transip_key_file,
            expiration_time=expiration_time,
            label=f"{__project__} {__version__}",
        )

        header1, payload1 = decode_jwt(str(token))

        sleep(4)  # "Refresh" even before safety marging; token stays the same
        header2, payload2 = decode_jwt(str(token))

        sleep(6)  # "Refresh" out of time; results in a new token just the same
        header3, payload3 = decode_jwt(str(token))

        # https://www.iana.org/assignments/jwt/jwt.xhtml
        # JWT IDs are different; different tokens
        assert header1["jti"] == header2["jti"]
        assert header2["jti"] != header3["jti"]

        assert payload1["iat"] == payload2["iat"] < payload3["iat"]
        # The checks themselves are perhaps not so important.
        # The fact that the information is available verifies we have valid JWT tokens
