# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Test the AccessToken class."""
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA512
from transip_dns import __project__, __version__
from transip_dns.accesstoken import (
    AccessToken,
    AccessTokenPrivateKeyInvalidPemFormat,
    AccessTokenPrivateKeyUnrecognized,
)

# Static methods
KEY_ed25519 = "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW\nQyNTUxOQAAACDL8w5rqjRTjCunfu6x2kQo2xuOi+gwdi/yTM0BdxEWVgAAAJAzpYknM6WJ\nJwAAAAtzc2gtZWQyNTUxOQAAACDL8w5rqjRTjCunfu6x2kQo2xuOi+gwdi/yTM0BdxEWVg\nAAAEAiZW8myk3sFlHgKB1DItFUagAPnmxOKqtDkAWvoS4JScvzDmuqNFOMK6d+7rHaRCjb\nG46L6DB2L/JMzQF3ERZWAAAACVRlc3QgQ2VydAECAwQ=\n-----END OPENSSH PRIVATE KEY-----\n"  # noqa


class TestAccessToken:
    @pytest.mark.parametrize("key, file", [(None, None), ("content", "path")])
    def test_init_file_mutually_exclusive(self, key, file):
        pytest.raises(
            ValueError,
            AccessToken,
            login="Joe",
            private_key=key,
            private_key_file=file,
        )

    def test_init(self, one_key_of_many):
        key_pem, key_serialized = one_key_of_many

        if isinstance(key_pem, Path):
            private_key_pem_file = key_pem
            private_key_pem = None
        else:
            private_key_pem_file = None
            private_key_pem = key_pem

        login = "joe"
        expiration_time = 20
        read_only = True
        global_key = True
        label = f"{__project__} {__version__}"
        authentication_url = "http etc"
        connection_timeout = 30
        token = AccessToken(
            login=login,
            private_key=private_key_pem,
            private_key_file=private_key_pem_file,
            expiration_time=expiration_time,
            read_only=read_only,
            global_key=global_key,
            label=label,
            authentication_url=authentication_url,
            connection_timeout=connection_timeout,
        )
        assert token.login == login
        assert token.time_to_live == expiration_time
        assert token.read_only == read_only
        assert token.global_key == global_key
        assert token.label == label
        assert token.authentication_url == authentication_url
        assert token.connection_timeout == connection_timeout

        payload = (
            "Apparently private keys can't be compared directly when extracted (salts?)."
            "But they MUST create the same signature when signing the same data!"
        )
        assert token.private_key.sign(
            str.encode(payload), PKCS1v15(), SHA512()
        ) == key_serialized.sign(str.encode(payload), PKCS1v15(), SHA512())

    @pytest.mark.parametrize(
        "epoch_token_ttl, time_elapsed, token_nearly_expired",
        [
            (100, 0, False),
            (100, 110, True),
            (100, 90, False),
        ],
    )
    def test_token_nearly_expired(
        self,
        mocker,
        path_pem_key,
        epoch_token_ttl,
        time_elapsed,
        token_nearly_expired,
    ):
        token = AccessToken(
            login="Joe",
            private_key_file=path_pem_key,
            expiration_time=epoch_token_ttl,
            label=f"{__project__} {__version__}",
        )
        epoch_token_issued = 1609459200.000000
        token._token_epoch = epoch_token_issued  # Usually set after token retrieval
        mocker.patch(
            "transip_dns.accesstoken.time",
            return_value=epoch_token_issued + time_elapsed,
        )
        assert token_nearly_expired == token._token_nearly_expired()

    @pytest.mark.parametrize(
        "key, raisedexception",
        [
            (KEY_ed25519, AccessTokenPrivateKeyUnrecognized),
            ("Not a key", AccessTokenPrivateKeyInvalidPemFormat),
        ],
    )
    def test_serialize_private_key_exception(self, key, raisedexception):
        pytest.raises(
            raisedexception,
            AccessToken.serialize_private_key,
            key,
        )

    @pytest.fixture(params=["identical_keys", "set01", "set02"])
    def private_key_pem(self, request):
        keys = {
            "identical_keys": {
                "good_key": "-----BEGIN RSA PRIVATE KEY-----\nMC4CAQACBQC5ArihAgMBAAECBQCZBUXtAgMA4csCAwDRwwIDAKKBAgIuqwIDAItA\n-----END RSA PRIVATE KEY-----\n",  # noqa
                "bad_key": "-----BEGIN RSA PRIVATE KEY-----\nMC4CAQACBQC5ArihAgMBAAECBQCZBUXtAgMA4csCAwDRwwIDAKKBAgIuqwIDAItA\n-----END RSA PRIVATE KEY-----\n",  # noqa
            },
            "set01": {
                "good_key": "-----BEGIN RSA PRIVATE KEY-----\nMC4CAQACBQC5ArihAgMBAAECBQCZBUXtAgMA4csCAwDRwwIDAKKBAgIuqwIDAItA\n-----END RSA PRIVATE KEY-----\n",  # noqa
                "bad_key": "BEGIN RSA PRIVATE KEY\nMC4CAQACBQC5ArihAgMBAAECBQCZBUXtAgMA4csCAwDRwwIDAKKBAgIuqwIDAItA\n-----END RSA PRIVATE KEY-----\n",  # noqa
            },
            "set02": {
                "good_key": "-----BEGIN RSA PRIVATE KEY-----\nMC4CAQACBQC5ArihAgMBAAECBQCZBUXtAgMA4csCAwDRwwIDAKKBAgIuqwIDAItA\n-----END RSA PRIVATE KEY-----\n",  # noqa
                "bad_key": "-----BEGIN RSA PRIVATE KEY-----\nMC4CAQACBQC5ArihAgMBAAECBQCZBUXtAgMA4csCAwDRwwIDAKKBAgIuqwIDAItA\n END RSA PRIVATE KEY",  # noqa
            },
        }
        return keys[request.param].values()

    def test_rebuild_private_key(self, private_key_pem):
        good_key, bad_key = private_key_pem

        re_checked_key = AccessToken.rebuild_private_key_pem(bad_key)
        assert good_key == re_checked_key

    def test_rebuild_private_key_with_error(self):
        pytest.raises(
            Exception, AccessToken.rebuild_private_key_pem, "Totally not a key"
        )
