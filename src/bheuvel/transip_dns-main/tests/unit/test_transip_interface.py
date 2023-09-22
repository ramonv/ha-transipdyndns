# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Test the TransipInterface class."""
import logging
import re

import pytest
import requests
from transip_dns.transip_interface import DnsEntry, DnsRecord, TransipInterface
from tests.unit.conftest import stl


class TestDnsEntry:
    """Test the basic DnsEntry class."""

    def test_dnsentry(self):
        content = "192.0.2.1"
        expire = 300
        name = "website"
        rtype = "A"

        dns_entry = DnsEntry(content=content, expire=expire, name=name, rtype=rtype)
        assert dns_entry.__repr__() == {
            "dnsEntry": {
                "name": name,
                "expire": expire,
                "type": rtype,
                "content": content,
            }
        }


class TestDnsRecord:
    """Test the DnsRecord class."""

    # Record property names shortened for readability (perhaps?)
    # Expanded by method tests.unit.conftest.stl
    @pytest.mark.parametrize(
        "record_data",
        [
            ({"n": "A", "t": "A", "e": "C", "c": "D", "z": "E", "q": None}),
            ({"n": "A", "t": "NS", "e": None, "c": "D", "z": "E", "q": None}),
            ({"n": "A", "t": "TXT", "e": "C", "c": None, "z": "E", "q": "F"}),
        ],
    )
    def test_init(self, mocker, record_data: dict):
        """Test the DnsRecord class initialization.

        Args:
            mocker (pytest_mock.plugin.MockerFixture): mocking
            record_data (dict): Dictionary with data for the DnsRecord
        """
        record_data = stl(record_data)
        if record_data["query_data"]:
            mocker.patch(
                "transip_dns.transip_interface.DnsRecord.query_for_content",
                return_value=record_data["query_data"],
            )
        dns_record = DnsRecord(**record_data)

        if record_data["query_data"] is not None:
            # If query, test rdata separate that is has the query_result
            assert dns_record.content == record_data["query_data"]
            # rdata has been tested, take it out of the test
            del record_data["content"]

        # query_data is no attribute so remove it, but used in setting rdata
        del record_data["query_data"]

        for field in record_data:
            assert getattr(dns_record, field) == record_data[field]
        assert dns_record.fqdn == f"{dns_record.name}.{dns_record.zone}"

    @pytest.mark.parametrize(
        "content, expire, name, rtype, error_expected, error_type",
        [
            ("ip", 300, "home", "a", False, None),
            ("ip", 300, "home", "x", True, ValueError),
        ],
    )
    def test_init_errors(
        self, content, expire, name, rtype, error_expected, error_type
    ):
        """Test if (in)correct record types are allowed/raised."""
        if error_expected:
            pytest.raises(error_type, DnsRecord, name, rtype, expire, content, "x.net")
        else:
            entry = DnsRecord(name, rtype, expire, content, "x.net")

            assert entry.content == content
            assert entry.expire == expire
            assert entry.name == name

            assert entry.rtype == rtype

    def test_query_for_content(self, requests_mock):
        """Test query_ip function.

        Fairly simple test that the function will pass on the result of the url request

        Args:
            requests_mock (requests_mock.mocker.Mocker): a mock specifically for the url request
        """
        query_url = "https://ipv4_or_ipv6_address"
        ip_address = "::ffff:198.51.100.1"
        requests_mock.get(query_url, text=ip_address)
        returned_ip = DnsRecord.query_for_content(query_url)

        assert returned_ip == ip_address


class TestTransipInterface:
    def test_init_double_credentials_error(self):
        pytest.raises(
            ValueError,
            TransipInterface,
            login="John",
            private_key_pem="complex key",
            access_token="token",
        )

    @pytest.mark.parametrize(
        "retries, negative_responses",  # negative_responses > retries : expect_exception
        [
            (3, 0),
            (3, 3),
            (3, 4),  # expect_exception
            (2, 4),  # expect_exception
            (0, 2),
        ],
    )
    @pytest.mark.parametrize("method", ["delete", "patch", "post", "get"])
    def test_execute_dns_retry(
        self,
        mocker,
        requests_mock,
        caplog,
        retries,
        negative_responses,
        method,
    ):

        dns_record = DnsRecord("name", "A", 300, "ip", "example.com")

        response_error = {"status_code": 409}
        response_ok = {
            "status_code": 204,
            "text": '{"dnsEntries": "whatever"}',
        }
        mocked_response = []
        # Return a certain number of"negative_responses"
        for _ in range(negative_responses):
            mocked_response.append(response_error)
        # Before a positive response
        mocked_response.append(response_ok)

        # Dynamically mock requests.get, post, patch and delete
        request_mock_action = getattr(requests_mock, method)
        request_mock_action(
            "https://api.transip.nl/v6/domains/example.com/dns", mocked_response
        )

        transip_interface = TransipInterface(
            access_token="complex key",
            retry=retries,
            retry_delay=0.01,
        )

        # Dynamically pick transip_interface.get_dns_entry, post, patch and delete
        transip_interface_test_dns_entry = getattr(
            transip_interface, f"{method}_dns_entry"
        )

        # Post, patch and delete need the full record
        dns_parameter = dns_record
        if method == "get":  # get only needs the zone to list
            dns_parameter = dns_record.zone

        caplog.set_level(logging.DEBUG)
        if negative_responses > retries:
            pytest.raises(
                requests.exceptions.HTTPError,
                transip_interface_test_dns_entry,
                dns_parameter,
            )
            assert (
                len(re.findall(r"(API request returned 409)", caplog.text))
                == retries + 1
            )

        else:
            response = transip_interface_test_dns_entry(dns_parameter)
            if method == "get":  # get "unpacks" the response into actual content
                assert response.json()["dnsEntries"] == "whatever"

            assert response.status_code == 204
            assert (
                len(re.findall(r"(API request returned 409)", caplog.text))
                == negative_responses
            )
            assert len(re.findall(r"(API request returned 204)", caplog.text)) == 1
