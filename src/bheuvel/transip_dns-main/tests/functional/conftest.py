# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Shared fixtures for functional testing."""
import pytest


@pytest.fixture(scope="module")
def default_record():
    """Minimal dns record for testing."""
    return {
        "--record_name": "TESTRECORD",
        "--record_data": "192.0.2.1",
        "--record_ttl": "666",
    }
