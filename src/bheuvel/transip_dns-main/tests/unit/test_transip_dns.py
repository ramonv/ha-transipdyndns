# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Test the transip_dns script."""
from pathlib import Path

import pytest
from tests.unit.conftest import stl

from transip_dns.transip_dns import (
    DnsRecord,
    DnsRecordNotFoundAndNoTTL,
    DuplicateDnsRecords,
    RecordState,
    display_domain,
    filter_domain_records,
    pretty_print_domain_list,
    record_state_in_domain,
    set_dns_record,
)


def test_stl():
    a_dict = stl({"n": "name", "t": "rtype", "e": "expire", "foo": "foo", "z": "zone"})
    for x in a_dict.keys():
        assert a_dict[x] == x

    a_list_of_dicts = stl(
        [
            {"n": "name", "t": "rtype"},
            {"bar": "bar", "e": "expire"},
            {"z": "zone", "300": 300},
        ]
    )
    for a_dict in a_list_of_dicts:
        for x in a_dict.keys():
            assert str(a_dict[x]) == x


class TestTransipDns:
    """Test the main module.

    methods process_parameters, process_commandline are tested separately
    in test_transip_parameters

    Note on locker: (tests using) locker will store the exact textual output.
    These tests use the fixture domain_records_default_domain. If that fixture
    has been changed, the textual output may also change. To store the new
    (verified) output and mark it as valid, run the following command:

    pytest -s tests/unit/test_transip_dns.py::TestTransipDns

    This will detect the change and ask to store the new result.


    Missing:
    delete_dns_record, execute_requested_action contain very little logic and doesn't produce anything
    display_domain, pretty_print_domain_list, not important enough, maybe later
    """

    def data_compare(self, new_data: str, test_name: str):
        new_data_file = Path(
            f"{__file__}/../textcompare/{test_name}-newresult"
        ).resolve()
        new_data_file.write_text(new_data)

        expected_data_file = Path(
            f"{__file__}/../textcompare/{test_name}-expected-result"
        ).resolve()
        try:
            expected_data = expected_data_file.read_text()
        except FileNotFoundError:
            expected_data = "Expected data file does not exist yet, first test run?"
        return new_data_file, expected_data_file, expected_data

    def test_pretty_print_domain_list(self, domain_records_default_domain):
        test_result = pretty_print_domain_list(domain_records_default_domain)
        (
            new_data_file,
            expected_data_file,
            expected_result,
        ) = self.data_compare(test_result, "test_pretty_print_domain_list")

        assert test_result == expected_result, (
            f"printed domain list is different.\nIf this is the result of changes"
            " in the domain_records_default_domain fixture,"
            f"replace\n{new_data_file}\nwith\n{expected_data_file}.\n\n\n"
        )
        new_data_file.unlink()

    @pytest.mark.parametrize(
        "filter_record",  # NOTE: Order of records is important for locker!!
        [
            {"n": None, "t": None, "e": None, "c": None, "z": None},
            {"n": None, "t": "CNAME", "e": 3600, "c": None, "z": None},
            {"n": "@", "t": None, "e": None, "c": None, "z": None},
            {"n": None, "t": None, "e": None, "c": "@", "z": None},
        ],
    )
    def test_display_domain(
        self, request, domain_records_default_domain, filter_record
    ):

        record_filter = DnsRecord(**stl(filter_record))
        test_result = display_domain(domain_records_default_domain, record_filter)

        (
            new_data_file,
            expected_data_file,
            expected_result,
        ) = self.data_compare(test_result, request._pyfuncitem.name)

        assert test_result == expected_result, (
            f"printed domain list is different.\nIf this is the result of changes"
            " in the domain_records_default_domain fixture,"
            f"replace\n{new_data_file}\nwith\n{expected_data_file}.\n\n\n"
        )
        new_data_file.unlink()

    @pytest.mark.parametrize(
        "record_state, record_expire, call, expected_exception",
        [
            (RecordState.FOUND_SAME, 300, None, None),
            (RecordState.FOUND_DIFFERENT, 300, "patch_dns_entry", None),
            (RecordState.NOTFOUND, 300, "post_dns_entry", None),
            (RecordState.NOTFOUND, None, "post_dns_entry", DnsRecordNotFoundAndNoTTL),
        ],
    )
    def test_set_dns_record(
        self, mocker, record_state, record_expire, call, expected_exception
    ):
        mock_TransipInterface = mocker.Mock()
        mocker.patch(
            "transip_dns.transip_dns.TransipInterface",
            return_value=mock_TransipInterface,
        )

        dns_record = DnsRecord(
            name="a-name",
            rtype="A",
            content="xxxx",
            expire=record_expire,
            zone="example.com",
        )
        dns_record.record_state = record_state
        if expected_exception:
            pytest.raises(
                expected_exception, set_dns_record, mock_TransipInterface, dns_record
            )
            assert len(mock_TransipInterface.method_calls) == 0
        else:
            if call:
                set_dns_record(mock_TransipInterface, dns_record)
                assert len(mock_TransipInterface.method_calls) == 1
                assert getattr(mock_TransipInterface, call).called
            else:
                assert len(mock_TransipInterface.method_calls) == 0

    @pytest.mark.parametrize(
        "dns_record, record_expected_state",
        [
            (
                DnsRecord("record002", "A", None, "192.0.2.2", "example.com"),
                RecordState.FOUND_SAME,
            ),
            (
                DnsRecord("RECORD002", "a", None, "192.0.2.2", "example.com"),
                RecordState.FOUND_SAME,
            ),
            (
                DnsRecord("reCOrd002", "A", 300, "192.0.2.2", "example.com"),
                RecordState.FOUND_SAME,
            ),
            (
                DnsRecord("record002", "A", 3600, "192.0.2.2", "example.com"),
                RecordState.NOTFOUND,
            ),
            (
                DnsRecord("notrecord002", "A", None, "192.0.2.2", "example.com"),
                RecordState.NOTFOUND,
            ),
            (
                DnsRecord("notrecord002", "A", 300, "192.0.2.2", "example.com"),
                RecordState.NOTFOUND,
            ),
            (
                DnsRecord("record002", "A", 300, "198.51.100.1", "example.com"),
                RecordState.FOUND_DIFFERENT,
            ),
            (
                DnsRecord("record002", "A", None, None, "example.com"),
                RecordState.FOUND_NO_REQUEST_DATA,
            ),
        ],
    )
    def test_record_state_in_domain(
        self,
        domain_records_similar_A_records,
        dns_record: DnsRecord,
        record_expected_state: RecordState,
    ):
        """Test record_state_in_domain function.

        Test different variations of records which should or should not be found.

        Args:
            dns_record (DnsRecord): a dns record
            record_expected_state (RecordState): the expected state/result
            domain_records_similar_A_records (dict): list of dns records ~domain
        """
        record_state = record_state_in_domain(
            dns_record=dns_record, domain_records=domain_records_similar_A_records
        )
        assert record_state == record_expected_state

    @pytest.mark.parametrize(
        "dns_record",
        [
            (DnsRecord("record045", "A", None, "192.0.2.2", "example.com")),
            (DnsRecord("record045", "A", 300, "192.0.2.2", "example.com")),
            (DnsRecord("record678", "A", 300, "192.0.2.2", "example.com")),
        ],
    )
    def test_record_state_in_domain_duplicates(
        self, domain_records_similar_A_records, dns_record: DnsRecord
    ):
        """Test record_state_in_domain function, specifically for duplicates.

        Test if exception DuplicateDnsRecords is raised when multiple records
        with the same name exist.

        Args:
            dns_record (DnsRecord): [description]
            domain_records_similar_A_records (dict): list of dns records ~domain
        """
        pytest.raises(
            DuplicateDnsRecords,
            record_state_in_domain,
            dns_record,
            domain_records_similar_A_records,
        )

    @pytest.mark.parametrize(
        "rname, rtype, rttl, rdata, ignore_content, records_found",
        [
            (None, "CNAME", 3600, None, False, 3),
            ("@", None, 300, None, False, 3),
            (None, None, None, None, False, -1),
            ("mail", "CNAME", 86400, "@", False, 1),
            ("mail", "CNAME", 86400, "any", True, 1),
            ("@", None, 300, "any", True, 3),
            ("@", None, 300, "any", False, 0),
        ],
    )
    # (domain_records: list, dns_record: DnsRecord)
    def test_filter_domain_records(
        self,
        domain_records_default_domain,
        rname,
        rtype,
        rttl,
        rdata,
        ignore_content,
        records_found,
    ):
        """Test the filtering of the domain by using en DnsRecord object."""
        dns_record = DnsRecord(
            name=rname,
            rtype=rtype,
            expire=rttl,
            content=rdata,
            zone="example.com",
        )
        filtered_list = filter_domain_records(
            domain_records=domain_records_default_domain,
            dns_record=dns_record,
            ignore_content=ignore_content,
        )
        # -1 is a moniker for all records
        if records_found == -1:
            records_found = len(domain_records_default_domain)
        assert len(filtered_list) == records_found
