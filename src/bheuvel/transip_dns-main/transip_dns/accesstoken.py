# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""The instance of the AccessToken class will provide a token.

Each time the instance is referenced, the expiration is checked, and renewed if
needed. By default the token is valid for (only) 60 seconds, yet automatically
"renewed" before actual expiration.
Consider that the generated token is "lost" after the program ends, or the
instance of this class is not in an active scope. Based on this it is assumed
that the token only needs to be valid for a few seconds. Leaving it active for
the (assumed by many people) default 30 minutes is unnecessary.

Unfortunately there doesn't appear to be method in the TransIP REST API to
invalidate or remove the token when done.


"""
import json
import logging
import re
from base64 import b64encode
from pathlib import Path
from time import time
from typing import Dict

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA512
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from requests import post

logger = logging.getLogger(__name__)


class AccessTokenPrivateKey(Exception):
    """Main exception for key errors."""

    pass


class AccessTokenPrivateKeyUnrecognized(AccessTokenPrivateKey):
    """It may be a cryptographic key, but not recognized as such."""

    pass


class AccessTokenPrivateKeyInvalidPemFormat(AccessTokenPrivateKey):
    """The file doesn't appear to be in a valid PEM format.

    BEGIN RSA PRIVATE KEY is PKCS#1; essentially just the key object
    BEGIN PRIVATE KEY is PKCS#8; key object, prepended with version or algorithm
                                 identifier (also encoded in Base64)
    """

    pass


class AccessToken:
    """The instance of this class provides a TransIP access token."""

    def __init__(
        self,
        login: str,
        private_key: str = None,
        private_key_file: Path = None,
        expiration_time: int = 60,
        read_only: bool = False,
        global_key: bool = False,
        label: str = __name__,
        authentication_url: str = "https://api.transip.nl/v6/auth",
        connection_timeout: int = 30,
    ):
        """Initialize the AccessToken.

        :param login: the TransIP login name
        :type login: str
        :param private_key: the private key as string, defaults to None
        :type private_key: str, optional
        :param private_key_file: file location of the private key, defaults to None
        :type private_key_file: Path, optional
        :param expiration_time: expiration time (TTL) of the access token,
                                defaults to 60
        :type expiration_time: int, optional
        :param read_only: key/token allows to change objects or only read,
                          defaults to False
        :type read_only: bool, optional
        :param global_key: key may only be used from whitelisted ip addresses,
                           defaults to False
        :type global_key: bool, optional
        :param label: textual identifier for the access token, defaults to __name__
        :type label: str, optional
        :param authentication_url: TransIP authentication url, defaults to
                                   "https://api.transip.nl/v6/auth"
        :type authentication_url: str, optional
        :param connection_timeout: timeout for the network response, defaults to 30
        :type connection_timeout: int, optional
        :raises ValueError: raised if neither or both parameters for the
                            private key (file) is provided.
        """
        if (private_key and private_key_file) or (
            private_key is None and private_key_file is None
        ):
            raise ValueError(
                (
                    "Either parameter private_key or private_key_file must be"
                    "specified, but also not both."
                )
            )

        self.login = login
        self.global_key = global_key
        self.read_only = read_only
        self.label = label
        self.authentication_url = authentication_url
        self.time_to_live = expiration_time
        self.connection_timeout = connection_timeout
        self.private_key = None

        if private_key_file:
            private_key = Path(private_key_file).read_text()
        self.private_key = AccessToken.serialize_private_key(private_key)

        self._token = None
        self._token_epoch = float(0)

    def __repr__(self):
        """When this object is referenced, return a valid token.

        When the token is about to expire, request a new one.

        :return: TransIP access token
        :rtype: str (JSON Web Token)
        """
        if self._token is None or self._token_nearly_expired():
            self._request_token()
        return self._token

    def _request_token(self) -> None:
        """Request the TransIP access token.

        Generate the payload (claim) for the request for the access token.
        Sign the payload and include it in the headers.
        Make the request and save the token in self._token
        """
        payload = json.dumps(self._token_request_parameters())
        headers = self._generate_signature_header(payload)
        response = post(
            url=self.authentication_url,
            data=payload,
            headers=headers,
            timeout=self.connection_timeout,
        )
        response.raise_for_status()

        self._token = response.json()["token"]
        self._token_epoch = time()

    def _token_request_parameters(self) -> Dict:
        """Generate the payload (claim) for the request for the access token.

        :return: request parameters for the request for the access token
        :rtype: Dict
        """
        return {
            "login": self.login,
            "nonce": time(),
            "read_only": self.read_only,
            "expiration_time": f"{self.time_to_live} seconds",
            "label": f"{self.label} ({time()})",
            "global_key": self.global_key,
        }

    def _generate_signature_header(self, payload: Dict) -> Dict:
        """Sign the payload and include it in the headers.

        :param payload: payload (claim) for the request for the access token
        :type payload: Dict
        :return: headers which include the signature of the payload
        :rtype: Dict
        """
        signature = self.private_key.sign(str.encode(payload), PKCS1v15(), SHA512())
        return {
            "Content-Type": "application/json",
            "Signature": b64encode(signature).decode("ascii"),
        }

    def _token_nearly_expired(self) -> bool:
        """Test if 90% of the lifetime of the access token has passed.

        At token creation, the time has been recorded. Together with specified
        lifetime the calculation takes place.

        :return: if token lifetime is passed 90%
        :rtype: bool
        """
        time_elapsed = time() - self._token_epoch
        max_time_to_elapse_minus_margin = self.time_to_live * 0.9
        return time_elapsed > max_time_to_elapse_minus_margin

    @staticmethod
    def serialize_private_key(private_key_pem: str) -> str:
        """Convert the key from PEM to "native/binary" format.

        If failed, "rebuild" the key and try once more.

        :param private_key_pem: the private key in PEM format
        :type private_key_pem: str
        :raises AccessTokenPrivateKeyUnrecognized: raised if unknown cryptographic key
        :return: RSAPrivateKey (cryptography.hazmat.primitives.asymmetric.rsa)
        :rtype: str
        """
        private_key = None
        for attempt in range(1, 3):
            try:
                private_key = load_pem_private_key(
                    private_key_pem.encode(),
                    password=None,
                )
            except (ValueError, UnsupportedAlgorithm) as e:
                if attempt == 2:
                    raise AccessTokenPrivateKeyUnrecognized(str(e)) from e
                pass
            private_key_pem = AccessToken.rebuild_private_key_pem(private_key_pem)
        return private_key

    @staticmethod
    def rebuild_private_key_pem(private_key_pem: str) -> str:
        """Tokenize the file as if it is a PEM file, and re-assemble.

        :param private_key_pem: the private key in PEM format
        :type private_key_pem: str
        :raises AccessTokenPrivateKeyInvalidPemFormat: private_key_pem parameter
                                    does not appear to be in a valid PEM format
        :return: reassembled private key
        :rtype: str
        """
        pem = (
            r".*?(?P<begin>BEGIN[^-\n\r]+)[-\n\r]*"
            r"(?P<key>.+?[^-]*).*?[- ]+(?P<end>END[^-\n\r]+)"
        )
        pem_components = re.match(pem, private_key_pem, re.M)
        if pem_components is None:
            raise AccessTokenPrivateKeyInvalidPemFormat(
                "Key does not appear to be in a valid PEM format"
            )

        # As TransIP provides the key as copy-paste. Small error may occurwhere leading
        # or trailing dashes are missed. While the RFC (rfc7468) specifies that the key
        # content should be parsed "loosly" (additional/missing newlines), the 5 dashes
        # MUST be EXACTLY present...
        # https://tools.ietf.org/html/rfc7468#section-2
        pem_BEGIN_line = f"{'-'*5}{pem_components['begin'].strip()}{'-'*5}\n"
        pem_KEY = pem_components["key"]
        pem_END_line = f"{'-'*5}{pem_components['end'].strip()}{'-'*5}\n"

        return pem_BEGIN_line + pem_KEY + pem_END_line
