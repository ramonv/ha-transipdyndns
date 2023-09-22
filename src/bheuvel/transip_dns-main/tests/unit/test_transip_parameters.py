# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Test the custom commanline processing additions."""
from collections import namedtuple
import pytest

from transip_dns.transip_dns import (
    RecordState,
    process_commandline,
    process_parameters,
)


@pytest.mark.parametrize(
    "dataset, environment_options, parameter_options",
    [
        ("data", True, False),
        ("data", False, True),
        ("data", True, True),
        ("query_ipv4", True, False),
        ("query_ipv4", False, True),
        ("query_ipv4", True, True),
        ("query_ipv6", True, False),
        ("query_ipv6", False, True),
        ("query_ipv6", True, True),
        ("delete", True, True),
        ("not_query_ipv4", True, True),  # Not query only usefull for environment
        ("query_ipv4_new_url", True, False),
        ("query_ipv4_new_url", False, True),
        ("query_ipv4_new_url", True, True),
    ],
)
def test_process_commandline(
    mocker,
    options_collection,
    dataset: str,
    environment_options: bool,
    parameter_options: bool,
):
    """Test the processing of the script parameters.

    This includes testing of command line parameters
    and process_environment_variables.


    Args:
        mocker (pytest_mock.plugin.MockerFixture): for mocking environment variables
                                                       and command line parameters
        options (list): the options to look for (for test convenience)
        environment (dict): the environment variables available to the program
        parameters (list): the command line parameters (sys.argv)
    """
    environment = {}
    parameters = ["programname"]
    if environment_options:
        environment = options_collection[dataset]["env"]
    if parameter_options:
        parameters = options_collection[dataset]["param"]

    mocker.patch("os.environ", environment)
    mocker.patch("sys.argv", parameters[:])

    default_single_options_env = {
        "query_ipv4": "https://ipv4.icanhazip.com",
        "query_ipv6": "https://ipv6.icanhazip.com",
        "delete": True,
    }
    default_single_options_parm = default_single_options_env

    if dataset == "query_ipv4_new_url":
        if environment_options:
            default_single_options_env = {
                "query_ipv4": "https://api4.my-ip.io/ip_e",
                "query_ipv6": "https://api6.my-ip.io/ip_e",
                "delete": True,
            }
        if parameter_options:
            default_single_options_env = {
                "query_ipv4": "https://api4.my-ip.io/ip_p",
                "query_ipv6": "https://api6.my-ip.io/ip_p",
                "delete": True,
            }
    # Actual processing of the commandline
    # and integration with environment variables
    args = process_commandline()

    for option in options_collection[dataset]["options"]:
        # Set expected_value from environment first
        expected_value = None
        env_option = "TID_" + option.upper()
        if env_option in environment:

            if option in ["query_ipv4", "query_ipv6", "delete"]:
                expected_value = None
                if environment[env_option] == "true":
                    expected_value = default_single_options_env[option]
                if (
                    environment[env_option] != "true"
                    and environment[env_option] != "false"
                ):
                    expected_value = environment[env_option]
            else:
                expected_value = environment[env_option]

        # Expected that commandline parameters will override environment variables
        params_option = "--" + option
        if params_option in parameters:
            index = parameters.index(params_option)

            if option in ["query_ipv4", "query_ipv6", "delete"]:
                expected_value = default_single_options_parm[option]
                if ((index + 1) < len(parameters)) and (
                    parameters[index + 1][0:2] != "--"
                ):
                    expected_value = parameters[index + 1]
            else:
                expected_value = parameters[index + 1]

        if option == "query_ipv4" or option == "query_ipv6":
            option = "query_url"

        assert args.__dict__[option] == expected_value


@pytest.mark.parametrize(
    (
        "user, record_name, record_type, "
        "record_ttl, record_data, domainname, query_url, record_state"
    ),
    [
        (
            "user001",
            "record001",
            "A",
            None,
            "192.0.2.1",
            "example1.com",
            None,
            RecordState.FOUND_SAME,
        ),
        (
            "user002",
            "record002",
            "AAAA",
            "TTL002",
            "192.0.2.2",
            "example2.com",
            None,
            RecordState.FOUND_DIFFERENT,
        ),
        (
            "user003",
            "record003",
            "cname",
            "TTL003",
            None,
            "example3.com",
            "http://query3",
            RecordState.NOTFOUND,
        ),
    ],
)
def test_process_parameters(
    mocker,
    path_pem_key,
    domain_records_similar_A_records,
    user: str,
    record_name: str,
    record_type: str,
    record_ttl: str,
    record_data: str,
    domainname: str,
    query_url: str,
    record_state: RecordState,
):
    """Test process_parameters.

    The function has little actual logic other then creating objects and calling other functions.
    This has little more value then a thorough syntax check...

    Args:
        mocker (pytest_mock.plugin.MockerFixture): mocking
        user (str): a user
        private_key (str): a private key
        record_name (str): a record name
        record_type (str): a record type
        record_ttl (str): a record ttl
        record_data (str): record data
        domainname (str): a domain name
        query_url (str): an url
        record_state (RecordState): record state
    """
    args = namedtuple(
        "args",
        [
            "user",
            "private_key",
            "private_key_file",
            "token",
            "record_name",
            "record_type",
            "record_ttl",
            "record_data",
            "domainname",
            "query_url",
            "domains",
        ],
    )

    mocker.patch(
        "transip_dns.transip_dns.DnsRecord.query_for_content",
        return_value="alternate_rdata",
    )

    mock_TransipInterface = mocker.Mock()
    mocker.patch(
        "transip_dns.transip_dns.TransipInterface",
        return_value=mock_TransipInterface,
    )
    mock_Response = mocker.Mock()
    mock_TransipInterface.get_dns_entry.return_value = mock_Response
    mock_Response.json.return_value = {"dnsEntries": domain_records_similar_A_records}
    mocker.patch(
        "transip_dns.transip_dns.record_state_in_domain", return_value=record_state
    )

    args.domains = False
    args.domainname = domainname
    args.private_key_file = path_pem_key
    args.private_key = None
    args.record_name = record_name
    args.record_ttl = record_ttl
    args.record_type = record_type
    args.user = user

    args.query_url = query_url
    args.record_data = record_data

    _, resulting_dns_record, _ = process_parameters(args)

    # assert resulting_transip_interface == mock_TransipInterface
    assert resulting_dns_record.name == record_name
    assert resulting_dns_record.rtype == record_type
    assert resulting_dns_record.expire == record_ttl
    assert resulting_dns_record.zone == domainname
    assert resulting_dns_record.fqdn == f"{record_name}.{domainname}"
    assert resulting_dns_record.record_state == record_state
    if record_data:
        assert resulting_dns_record.content == record_data
    if query_url:
        assert resulting_dns_record.content == "alternate_rdata"
