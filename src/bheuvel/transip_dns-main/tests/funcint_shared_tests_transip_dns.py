# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Integration testing against the actual TransIP API."""
import logging
import re

import requests
from transip_dns.transip_dns import main as transip_dns

from tests import transip_demo_token, transip_domain
from tests.support_methods import hash_to_list


def create_change_delete_testing(
    mocker, caplog, transip_credentials_env_hash, cycle_record
):
    mocker.patch("os.environ", transip_credentials_env_hash)
    caplog.set_level(logging.INFO)

    create_record, change_record, dynamic_record, delete_record = cycle_record
    # Create the record
    mocker.patch("sys.argv", ["transip_dns"] + hash_to_list(create_record))
    transip_dns()
    assert (
        re.search(
            fr"Record.*not found.*record.*{create_record['--record_data']}.*created",
            caplog.text,
            re.DOTALL,
        )
        is not None
    )
    caplog.clear()

    # Change the record
    mocker.patch("sys.argv", ["transip_dns"] + hash_to_list(change_record))
    transip_dns()
    record_content = change_record["--record_data"]
    if transip_demo_token is None:
        script_output = (  # pragma: not demo account skip demo coverage
            fr"Update DNS record completed.*{record_content}"
        )
    else:
        script_output = (  # pragma: not live account skip live coverage
            fr"Record.*not found.*record.*{record_content}.*created"
        )

    assert re.search(script_output, caplog.text, re.DOTALL) is not None
    caplog.clear()

    # Auto change the record
    mocker.patch("sys.argv", ["transip_dns"] + hash_to_list(dynamic_record))
    transip_dns()
    ip = requests.get("https://ipv4.icanhazip.com").text.strip()
    if transip_demo_token is None:
        script_output = (  # pragma: not demo account skip demo coverage
            fr"Resolved record data to be used.*{ip}.*Update DNS record completed.*{ip}"
        )
    else:
        script_output = (  # pragma: not live account skip live coverage
            fr"Resolved record data to be used.*{ip}.*"
            fr"Record.*not found.*DNS record.*{ip}.*created"
        )
    assert re.search(script_output, caplog.text, re.DOTALL) is not None
    caplog.clear()

    # delete the record
    mocker.patch("sys.argv", ["transip_dns"] + hash_to_list(delete_record))
    caplog.set_level(logging.INFO)
    transip_dns()
    domain_name = transip_credentials_env_hash["TID_DOMAINNAME"]
    record_name = delete_record["--record_name"]
    fqdn = f"{record_name}.{domain_name}"
    if transip_demo_token is None:
        script_output = fr"DNS record.*{fqdn}.*deleted"  # pragma: not demo account skip demo coverage
    else:
        script_output = fr".*{fqdn}.*not present.*No deletion executed.*"  # pragma: not live account skip live coverage
    assert re.search(script_output, caplog.text, re.DOTALL) is not None
    caplog.clear()


def delete_record_testing(
    mocker, caplog, delete_record_of_each_type, transip_credentials_env_hash
):
    """Create an actual DNS record at TransIP.

    The fixture create_record_of_each_type has a parameter (RECORD_TYPES) which causes
    this test to be run for all (those) record types.

    Args:
        mocker (pytest_mock.plugin.MockerFixture):
            Mock environment and command line parameters.
        caplog (pytest.logging.LogCaptureFixture):
            Capture logging output for analysis.
        create_record_of_each_type (Fixture/Tuple):
            The iterator which generated a valid name/value pair
            for the record to be created.
        transip_credentials_env_hash (Fixture/Dict):
            Hash with connection credentials
    """
    (dns_record_parameters, dns_record, partial_record) = delete_record_of_each_type
    mocker.patch("os.environ", transip_credentials_env_hash)
    mocker.patch("sys.argv", ["transip_dns"] + hash_to_list(dns_record_parameters))

    if partial_record:
        assert len(dns_record_parameters) < 5
    else:
        assert len(dns_record_parameters) == 5
    caplog.set_level(logging.INFO)
    transip_dns()
    if transip_demo_token is None:
        script_output = (  # pragma: not demo account skip demo coverage
            fr"DNS record '{dns_record.fqdn}' \('{dns_record.rtype}'\)"
            fr" '{dns_record.content}' deleted"
        )
    else:
        script_output = (  # pragma: not live account skip live coverage
            fr".*Record.*{dns_record.fqdn}.*{dns_record.rtype}.*not found"
            fr".*{dns_record.fqdn}.*not present. No deletion executed"
        )

    assert re.search(script_output, caplog.text, re.DOTALL) is not None


def create_record_testing(
    mocker, caplog, create_record_of_each_type, transip_credentials_env_hash
):
    """Create an actual DNS record at TransIP.

    The fixture create_record_of_each_type has a parameter (DNS_RECORD_TYPES) which
    causes this test to be run for all (those) record types.

    Args:
        mocker (pytest_mock.plugin.MockerFixture):
            Mock environment and command line parameters.
        caplog (pytest.logging.LogCaptureFixture):
            Capture logging output for analysis.
        create_record_of_each_type (Fixture/Tuple):
            The iterator which generated a valid name/value pair
            for the record to be created.
        transip_credentials_env_hash (Fixture/Dict):
            Hash with connection credentials
    """
    (dns_record_parameters, dns_record) = create_record_of_each_type
    mocker.patch("os.environ", transip_credentials_env_hash)
    mocker.patch("sys.argv", ["transip_dns"] + hash_to_list(dns_record_parameters))

    caplog.set_level(logging.INFO)
    transip_dns()

    script_output = (
        f"DNS record '{dns_record_parameters['--record_name']}.{transip_domain}' "
        f"('{dns_record_parameters['--record_type']}')"
        f" '{dns_record_parameters['--record_data']}' created"
    )
    assert script_output in caplog.text


def ipv4_query_testing(
    mocker, caplog, transip_credentials_env_hash, ipv4_query_test_record
):
    """Test the auto query for IPv4.

    Args:
        mocker ([type]): [description]
        caplog ([type]): [description]
        transip_credentials_env_hash ([type]): [description]
        ipv4_query_test_record ([type]): [description]
    """
    mocker.patch("os.environ", transip_credentials_env_hash)
    query_default = requests.get("https://ipv4.icanhazip.com")
    ip_default = query_default.text.strip()

    alternative_query = requests.get("https://api4.my-ip.io/ip")
    ip_alternative = alternative_query.text.strip()

    record_domain = transip_credentials_env_hash["TID_DOMAINNAME"]
    record_type, record_name, record_ttl = ipv4_query_test_record

    assert (
        ip_default == ip_alternative
    ), "ip addresses should be the same, else there is no real internet access"

    dns_record = {
        "--record_type": record_type,
        "--record_name": record_name,
        "--record_ttl": record_ttl,
        "--query_ipv4": None,
    }
    mocker.patch("sys.argv", ["transip_dns"] + hash_to_list(dns_record))
    # Set record based on query
    transip_dns()
    responses = [
        f"Resolved record data to be used: '{ip_default}'",
        f"Record '{record_name}.{record_domain}', type '{record_type}' not found!",
        (
            f"DNS record '{record_name}.{record_domain}'"
            f" ('{record_type}') '{ip_default}' created"
        ),
    ]
    for response in responses:
        assert response in caplog.text
    caplog.clear()
