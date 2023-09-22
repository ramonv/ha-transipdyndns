# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Various fixtures used in testing."""
from pathlib import Path, PurePath
from typing import Dict

import pytest
from cryptography.hazmat.primitives.serialization import load_pem_private_key

valid_key = "-----BEGIN RSA PRIVATE KEY-----\n validkey\n-----END RSA PRIVATE KEY-----"
valid_key_2 = (
    "-----BEGIN RSA PRIVATE KEY-----\n validkey02\n-----END RSA PRIVATE KEY-----"
)
invalid_key = "-----BEGIN PRIVATE KEY-----\n non_rsa_key\n-----END PRIVATE KEY-----"


def stl(short_list, short_names: Dict = None) -> Dict:
    """Convert a dictionary with short keynames to "real" long names.

    Partly to enhance readability of large test sets

    :param short_list: Dictionary with short key names
    :type short_list: Dict
    :param short_names: Translation dictionary for short to long names, defaults to None
    :type short_names: Dict, optional
    :return: Return the same dictionary, only with the keys "renamed"
    :rtype: Dict
    """
    if short_names is None:
        short_names = {
            "n": "name",
            "t": "rtype",
            "e": "expire",
            "c": "content",
            "z": "zone",
            "q": "query_data",
        }
    res = []
    if isinstance(short_list, list):
        for list_item in short_list:
            res.append(stl(short_list=list_item, short_names=short_names))
    else:
        res = {}
        for k in short_list.keys():
            if k in short_names.keys():
                res[short_names[k]] = short_list[k]
            else:
                res[k] = short_list[k]
    return res


possible_parameters = {
    "user": {
        "name_p": "--user",
        "name_e": "TID_USER",
        "has_value": True,
        "p_value": "someuser_p",
        "e_value": "someuser_e",
    },
    "private_key": {
        "name_p": "--private_key",
        "name_e": "TID_PRIVATE_KEY",
        "has_value": True,
        "p_value": valid_key,
        "e_value": valid_key_2,
    },
    "private_key_file": {
        "name_p": "--private_key_file",
        "name_e": "TID_PRIVATE_KEY_FILE",
        "has_value": True,
        "p_value": "/p/path",
        "e_value": "/e/path",
    },
    "domainname": {
        "name_p": "--domainname",
        "name_e": "TID_DOMAINNAME",
        "has_value": True,
        "p_value": "exempligratia-p.cloud",
        "e_value": "exempligratia-e.cloud",
    },
    "record_name": {
        "name_p": "--record_name",
        "name_e": "TID_RECORD_NAME",
        "has_value": True,
        "p_value": "eg-p",
        "e_value": "eg-e",
    },
    "record_type": {
        "name_p": "--record_type",
        "name_e": "TID_RECORD_TYPE",
        "has_value": True,
        "p_value": "A",
        "e_value": "AAAA",
    },
    "record_ttl": {
        "name_p": "--record_ttl",
        "name_e": "TID_RECORD_TTL",
        "has_value": True,
        "p_value": "120",
        "e_value": "300",
    },
    "record_data": {
        "name_p": "--record_data",
        "name_e": "TID_RECORD_DATA",
        "has_value": True,
        "p_value": "192.0.2.101",
        "e_value": "192.0.2.102",
    },
    "delete": {
        "name_p": "--delete",
        "name_e": "TID_DELETE",
        "has_value": False,
        "e_value": "true",
    },
    "query_ipv4": {
        "name_p": "--query_ipv4",
        "name_e": "TID_QUERY_IPV4",
        "has_value": False,
        "e_value": "true",
        "e_alternative": "https://api4.my-ip.io/ip_e",
        "p_alternative": "https://api4.my-ip.io/ip_p",
    },
    "query_ipv6": {
        "name_p": "--query_ipv6",
        "name_e": "TID_QUERY_IPV6",
        "has_value": False,
        "e_value": "true",
        "e_alternative": "https://api6.my-ip.io/ip_e",
        "p_alternative": "https://api6.my-ip.io/ip_p",
    },
    "log": {
        "name_p": "--log",
        "name_e": "TID_LOG",
        "has_value": True,
        "p_value": "WARNING",
        "e_value": "DEBUG",
    },
}


@pytest.fixture(scope="package")
def options_collection():
    """Generate a colletion of specific parameter sets."""
    collect = {}
    for request_set in [
        "data",
        "delete",
        "query_ipv4",
        "query_ipv6",
        "not_query_ipv4",
        "query_ipv4_new_url",
    ]:
        collect[request_set] = {
            "options": [],
            "env": {},
            "param": [],
        }

    """Standard set for creating a record."""
    collect["data"]["options"] = options_data
    collect["data"]["env"] = environment_generator(options_data)
    collect["data"]["param"] = parameters_generator(options_data)

    """Standard set for deleteing a record."""
    collect["delete"]["options"] = options_delete
    collect["delete"]["env"] = environment_generator(options_delete)
    collect["delete"]["param"] = parameters_generator(options_delete)

    """Standard set for dynamic query for IPv4 address."""
    collect["query_ipv4"]["options"] = options_query_ipv4
    collect["query_ipv4"]["env"] = environment_generator(options_query_ipv4)
    collect["query_ipv4"]["param"] = parameters_generator(options_query_ipv4)

    """Set for creating a record, but dynamic query disabled in environment."""
    collect["not_query_ipv4"]["options"] = options_data
    collect["not_query_ipv4"]["env"] = environment_generator(options_data)
    collect["not_query_ipv4"]["env"]["TID_QUERY_IPV4"] = "false"
    collect["not_query_ipv4"]["param"] = parameters_generator(options_data)

    """Set for dynamically searching for a ipv4 address, alternate url"""
    collect["query_ipv4_new_url"]["options"] = options_query_ipv4
    collect["query_ipv4_new_url"]["env"] = environment_generator(
        options_query_ipv4, ["query_ipv4"]
    )
    collect["query_ipv4_new_url"]["param"] = parameters_generator(
        options_query_ipv4, ["query_ipv4"]
    )

    """Standard set for dynamic query for IPv6 address."""
    collect["query_ipv6"]["options"] = options_query_ipv6
    collect["query_ipv6"]["env"] = environment_generator(options_query_ipv6)
    collect["query_ipv6"]["param"] = parameters_generator(options_query_ipv6)
    return collect


options_data = [
    "user",
    "private_key",
    "domainname",
    "record_name",
    "record_type",
    "record_data",
]
options_delete = [
    "user",
    "private_key",
    "domainname",
    "record_name",
    "record_type",
    "delete",
]
options_query_ipv4 = [
    "user",
    "private_key_file",
    "domainname",
    "record_name",
    "record_type",
    "query_ipv4",
]
options_query_ipv6 = [
    "user",
    "private_key",
    "domainname",
    "record_name",
    "record_type",
    "query_ipv6",
]


def environment_generator(params: list, alternative_values=None) -> dict:
    """Generate a dictionary with parameters as environment variables.

    Args:
        params (list): Set of requested parameters

    Global variable:
        possible_parameters (dict): Set of all parameters and respective names
                                    as environment variable or command line parameter

    Returns:
        dict: dictionary with parameters as environment variables
    """
    result = {}
    for entry in params:
        name = possible_parameters[entry]["name_e"]
        if alternative_values is not None and entry in alternative_values:
            result[name] = possible_parameters[entry]["e_alternative"]
        else:
            result[name] = possible_parameters[entry]["e_value"]
    return result


def parameters_generator(params: list, alternative_values: list = None) -> list:
    """Generate a list with parameters as command line parameters.

    Args:
        params (list): Set of requested parameters

    Global variable:
        possible_parameters (dict): Set of all parameters and respective names
                                    as environment variable or command line parameter

    Returns:
        list: list with parameters as command line parameters
    """
    result = ["programname"]
    for entry in params:
        result.append(possible_parameters[entry]["name_p"])
        if alternative_values is not None and entry in alternative_values:
            result.append(possible_parameters[entry]["p_alternative"])
        elif possible_parameters[entry]["has_value"]:
            result.append(possible_parameters[entry]["p_value"])
    return result


@pytest.fixture(scope="package")
def domain_records_similar_A_records():
    """Test set of similar records."""
    return [
        {"name": "record001", "content": "192.0.2.1", "expire": 300, "type": "A"},
        {"name": "record002", "content": "192.0.2.2", "expire": 300, "type": "A"},
        {"name": "record003", "content": "192.0.2.3", "expire": 300, "type": "A"},
        {"name": "record045", "content": "192.0.2.4", "expire": 300, "type": "A"},
        {"name": "record045", "content": "192.0.2.5", "expire": 300, "type": "A"},
        {"name": "record678", "content": "192.0.2.6", "expire": 300, "type": "A"},
        {"name": "record678", "content": "192.0.2.7", "expire": 300, "type": "A"},
        {"name": "record678", "content": "192.0.2.8", "expire": 300, "type": "A"},
    ]


@pytest.fixture(scope="package")
def domain_records_default_domain():
    """Generate a fairly default domain set."""
    return [
        {"name": "@", "expire": 300, "type": "A", "content": "37.97.254.27"},
        {"name": "@", "expire": 300, "type": "AAAA", "content": "2a01:7c8:3:1337::27"},
        {"name": "@", "expire": 86400, "type": "MX", "content": "10 @"},
        {"name": "@", "expire": 300, "type": "TXT", "content": "v=spf1 ~all"},
        {"name": "ftp", "expire": 86400, "type": "CNAME", "content": "@"},
        {"name": "mail", "expire": 86400, "type": "CNAME", "content": "@"},
        {
            "name": "transip-A._domainkey",
            "expire": 3600,
            "type": "CNAME",
            "content": "_dkim-A.transip.email.",
        },
        {
            "name": "transip-B._domainkey",
            "expire": 3600,
            "type": "CNAME",
            "content": "_dkim-B.transip.email.",
        },
        {
            "name": "transip-C._domainkey",
            "expire": 3600,
            "type": "CNAME",
            "content": "_dkim-C.transip.email.",
        },
        {"name": "www", "expire": 86400, "type": "CNAME", "content": "@"},
        {
            "name": "_dmarc",
            "expire": 86400,
            "type": "TXT",
            "content": "v=DMARC1; p=none;",
        },
    ]


# 32 bit RSA keys
PEM_KEY_RSA = "key_rsa.pem"
PEM_KEY = "key.pem"
PATH_PEM_KEY = Path(PurePath(__file__).parent, "key.pem")
PATH_PEM_KEY_RSA = Path(PurePath(__file__).parent, "key_rsa.pem")


@pytest.fixture
def path_pem_key():
    return PATH_PEM_KEY


@pytest.fixture(
    scope="module", params=[PEM_KEY_RSA, PEM_KEY, PATH_PEM_KEY, PATH_PEM_KEY_RSA]
)
def one_key_of_many(request):
    if Path(request.param).is_absolute():
        key_pem_content = Path(request.param).read_text()
        key_pem = request.param
    else:
        key_pem_content = Path(PurePath(__file__).parent, request.param).read_text()
        key_pem = key_pem_content

    serialized_key = load_pem_private_key(
        key_pem_content.encode(),
        password=None,
    )
    return key_pem, serialized_key
