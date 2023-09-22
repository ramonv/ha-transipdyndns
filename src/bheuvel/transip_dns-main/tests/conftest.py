# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Shared fixtures for testing."""
import pytest
import requests
from transip_dns.transip_interface import DNS_RECORD_TYPES, DnsRecord, TransipInterface

from tests import transip_demo_token, transip_domain, transip_key_file, transip_user
from tests.support_methods import delete_by_name_and_type


@pytest.fixture(scope="session")
def transip_interface():
    """Generate a connection object with TransIP.

    Due to scope module, this will be called (and cached) once.

    """
    if transip_user is None:
        return TransipInterface(  # pragma: not live account skip live coverage
            access_token=transip_demo_token, global_key=True
        )
    else:
        return TransipInterface(  # pragma: not demo account skip demo coverage
            login=transip_user,
            private_key_pem_file=transip_key_file,
            global_key=True,
        )


@pytest.fixture(scope="session")
def transip_credentials_env_hash():
    """Provide credentials as environment variables."""
    if transip_user is None:
        return {  # pragma: not live account skip live coverage
            "TID_TOKEN": transip_demo_token,
            "TID_DOMAINNAME": transip_domain,
        }
    else:
        return {  # pragma: not demo account skip demo coverage
            "TID_USER": transip_user,
            "TID_PRIVATE_KEY_FILE": transip_key_file,
            "TID_DOMAINNAME": transip_domain,
        }


@pytest.fixture(scope="session")
def record_data_for_each_record_type():
    """Provide a valid DNS record for a (each) record type."""

    def _record_data_for_each_record_type(record_type: str, for_create: bool = True):
        if for_create:
            name_addition = "create"
        else:
            name_addition = "delete"
        record_data = {
            "a": {
                "name": f"TESTServer001.test-{name_addition}",
                "value": "192.0.2.1",
                "ttl": "300",
                "hide_value": False,
                "hide_ttl": False,
            },
            "A": {
                "name": f"testserver01.test-{name_addition}",
                "value": "192.0.2.1",
                "ttl": "300",
                "hide_value": False,
                "hide_ttl": False,
            },
            "AAAA": {
                "name": f"testserver02.test-{name_addition}",
                "value": "2001:db8::",
                "ttl": "300",
                "hide_value": True,
                "hide_ttl": False,
            },
            "CNAME": {
                "name": f"refer-back-to-domain.test-{name_addition}",
                "value": f"{transip_domain}.",
                "ttl": "300",
                "hide_value": False,
                "hide_ttl": True,
            },
            "MX": {
                "name": f"subdomain.test-{name_addition}",
                "value": f"10 {transip_domain}.",
                "ttl": "300",
                "hide_value": True,
                "hide_ttl": True,
            },
            "NS": {
                "name": f"subdomain.test-{name_addition}",
                "value": f"{transip_domain}.",
                "ttl": "300",
                "hide_value": False,
                "hide_ttl": False,
            },
            "TXT": {
                "name": f"subdomain.test-{name_addition}",
                "value": "DKM spf etc",
                "ttl": "300",
                "hide_value": False,
                "hide_ttl": False,
            },
            "SRV": {
                "name": f"_ldap._tcp.test-{name_addition}",
                "value": f"10 50 389 {transip_domain}.",
                "ttl": "300",
                "hide_value": False,
                "hide_ttl": False,
            },  # https://tools.ietf.org/html/rfc2782
            "SSHFP": {
                "name": f"sshhost.test-{name_addition}",
                "value": "2 1 123456789abcdef67890123456789abcdef67890",
                "ttl": "300",
                "hide_value": False,
                "hide_ttl": False,
            },  # https://tools.ietf.org/html/rfc4255#section-3.1
            "TLSA": {
                "name": f"_25._tcp.test-{name_addition}",
                "value": (
                    "1 1 1 "
                    "af7fa84d981ed1db2ba2fdc2b85c6f1d654259ef728eed9bf0ebb9789e1efc5f"
                ),
                "ttl": "300",
                "hide_value": False,
                "hide_ttl": False,
            },  # https://tools.ietf.org/html/rfc7671#section-2.1
            # https://www.huque.com/bin/gen_tlsa
            "CAA": {
                "name": f"certs.test-{name_addition}",
                "value": f'0 issue "ca1.{transip_domain}; account=230123"',
                "ttl": "300",
                "hide_value": False,
                "hide_ttl": False,
            },
        }
        return record_data[record_type]

    return _record_data_for_each_record_type


@pytest.fixture
def cycle_record(transip_interface, record_data_for_each_record_type):
    record = record_data_for_each_record_type("A")

    # Build the record(s) locally, messy with the del dict, just privide 3 sets...
    record["name"] = f"cycle-{record['name']}"
    record_type = "A"
    record_name = record["name"]
    record_data = record["value"]
    record_ttl = record["ttl"]

    delete_by_name_and_type(transip_interface, record_name, record_type)
    create_record = {
        "--record_type": record_type,
        "--record_name": record_name,
        "--record_data": record_data,
        "--record_ttl": record_ttl,
    }
    change_record = {
        "--record_type": record_type,
        "--record_name": record_name,
        "--record_data": "192.0.2.111",
        "--record_ttl": record_ttl,
    }
    dynamic_record = {
        "--record_type": record_type,
        "--record_name": record_name,
        "--record_ttl": record_ttl,
        "--query_ipv4": None,
    }
    delete_record = {
        "--record_type": record_type,
        "--record_name": record_name,
        "--record_ttl": record_ttl,
        "--delete": None,
    }

    yield create_record, change_record, dynamic_record, delete_record

    delete_by_name_and_type(transip_interface, record_name, record_type, False, True)


@pytest.fixture(params=DNS_RECORD_TYPES)
def delete_record_of_each_type(
    request, record_data_for_each_record_type, transip_interface
):
    """Loop over each RECORD_TYPEs and delete such a record.

    Args:
        request (pytest.fixtures.SubRequest):
            Provides access to iteration in params; record types.
        record_data_for_each_record_type (fixture/function):
            Hash of valid name/value pairs for a/each DNS record type.
        transip_interface (fixture): Connection with TransIP.

    Yields:
        dns_record [hash]: Command line parameters for the record to be deleted.
        test_string [str]: Expected success string to be produced by the script.
    """
    record_type = request.param
    record = record_data_for_each_record_type(
        record_type=request.param, for_create=False
    )
    record_name = record["name"]
    record_data = record["value"]
    record_ttl = "300"
    dns_record_parameters = {
        "--record_type": record_type,
        "--record_name": record_name,
        "--record_data": record_data,
        "--record_ttl": record_ttl,
    }
    dns_record_object = DnsRecord(
        name=record_name,
        rtype=record_type,
        expire=record_ttl,
        content=record_data,
        zone=transip_domain,
    )
    try:
        transip_interface.post_dns_entry(dns_record_object)
    except requests.exceptions.HTTPError as e:  # pragma: no cover
        if "this exact record already exists" in e.response.content.decode():
            # Record might be left by previous (failed) attempt.
            # If tests run according to plan, this will not be executed
            pass

    partial_record = False
    if record["hide_ttl"]:
        del dns_record_parameters["--record_ttl"]
        partial_record = True
    if record["hide_value"]:
        del dns_record_parameters["--record_data"]
        partial_record = True

    dns_record_parameters["--delete"] = None
    yield (dns_record_parameters, dns_record_object, partial_record)

    # Destroy record, as the test should have delete all the records
    # the exception will never be triggered
    try:
        transip_interface.delete_dns_entry(dns_record_object)
    except Exception as e:
        if (  # pragma: no cover
            e.response.status_code == 404
            and "Dns entry not found" in e.response.content.decode()
        ):
            pass


@pytest.fixture(params=DNS_RECORD_TYPES)
def create_record_of_each_type(
    request, record_data_for_each_record_type, transip_interface
):
    """Loop over each RECORD_TYPEs and create such a record instance.

    Args:
        request (pytest.fixtures.SubRequest):
            Provides access to iteration in params; record types
        record_data_for_each_record_type (fixture/function):
            Hash of valid name/value pairs for a/each DNS record type
        transip_interface (fixture): Connection with TransIP

    Yields:
        dns_record [hash]: Command line parameters for the record to be created
        test_string [str]: Expected success string to be produced by the script
    """
    record_type = request.param
    record = record_data_for_each_record_type(request.param)
    record_name = record["name"]
    record_data = record["value"]
    record_ttl = "300"
    dns_record_parameters = {
        "--record_type": record_type,
        "--record_name": record_name,
        "--record_data": record_data,
        "--record_ttl": record_ttl,
    }

    yield (dns_record_parameters, record)

    rec = DnsRecord(
        content=record_data,
        name=record_name,
        rtype=record_type,
        expire=record_ttl,
        zone=transip_domain,
    )
    # Destroy record
    if transip_interface._token != transip_demo_token:
        transip_interface.delete_dns_entry(  # pragma: not demo account skip demo coverage
            rec
        )


@pytest.fixture
def ipv4_query_test_record(transip_interface):
    """Fixture to provide A DNS record.

    Returns
        [str]: record_type, record_name, record_ttl
    """
    record_type = "A"
    record_name = "ddns-testrecord"
    record_ttl = "300"

    delete_by_name_and_type(transip_interface, record_name, record_type, False, False)
    yield (record_type, record_name, record_ttl)
    delete_by_name_and_type(transip_interface, record_name, record_type, True, False)
