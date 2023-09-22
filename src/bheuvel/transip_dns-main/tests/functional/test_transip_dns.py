# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Integration testing against the actual TransIP API.

NOTE: This requires actual credentials and will actually create and delete records!
"""
import logging
import re

import pytest
from tests import transip_user
from tests.funcint_shared_tests_transip_dns import (
    create_change_delete_testing,
    create_record_testing,
    delete_record_testing,
    ipv4_query_testing,
)
from tests.support_methods import hash_to_list
from transip_dns.transip_dns import main as transip_dns
from transip_dns.transip_interface import DNS_RECORD_TYPES


@pytest.mark.skipif(
    transip_user is None,
    reason=(
        "Only demo credentials provided. Tests which create, change, delete "
        "and actually check create, change and delete will not work."
    ),
)
class TestTransipDns_Shared_Integration_Functional:  # pragma: not demo account skip demo coverage
    def test_create_change_delete(
        self, mocker, caplog, transip_credentials_env_hash, cycle_record
    ):
        create_change_delete_testing(
            mocker, caplog, transip_credentials_env_hash, cycle_record
        )

    def test_delete_record(
        self, mocker, caplog, delete_record_of_each_type, transip_credentials_env_hash
    ):
        delete_record_testing(
            mocker, caplog, delete_record_of_each_type, transip_credentials_env_hash
        )

    def test_create_record(
        self, mocker, caplog, create_record_of_each_type, transip_credentials_env_hash
    ):
        create_record_testing(
            mocker, caplog, create_record_of_each_type, transip_credentials_env_hash
        )

    def test_ipv4_query(
        self, mocker, caplog, transip_credentials_env_hash, ipv4_query_test_record
    ):
        ipv4_query_testing(
            mocker, caplog, transip_credentials_env_hash, ipv4_query_test_record
        )


class TestTransipDns_Integration_Functional_in_one:
    def test_integration_list_domain(
        self, mocker, caplog, transip_credentials_env_hash
    ):
        """Test the printed output when listing the domain.

        This test is completely valid with either real credentials are the demo
        key. It lists an actual existing domain

        Args:
            mocker (pytest_mock.plugin.MockerFixture):
                Mock environment and command line parameters.
            caplog (pytest.logging.LogCaptureFixture):
                Capture logging output
            transip_credentials_env_hash (Fixture/Dict):
                Hash with connection credentials
        """
        mocker.patch("os.environ", transip_credentials_env_hash)
        mocker.patch("sys.argv", ["transip_dns"] + ["--list"])

        caplog.set_level(logging.INFO)
        transip_dns()
        line_numbers = len(caplog.text.split("\n"))

        # As it is a live listing, it is not known how many records are present.
        # At least we can check that all line have a record type
        record_types = "|".join(DNS_RECORD_TYPES)
        regex_log = fr"[\n ]+({record_types})[\n ]"
        typed_lines = re.findall(regex_log, caplog.text, re.MULTILINE)

        # Compare the number of records in te report with....
        # (assuming) at least 5 fairly common records
        assert len(typed_lines) > 5
        assert len(typed_lines) == line_numbers - 4  # Additional newlines and info

    @pytest.mark.parametrize(
        "comment, exit_code, altered_setting",
        [
            ("Domain not found", 404, {"--domainname": "nonexisting.example.com"}),
            ("Invalid record name", 406, {"--record_name": "invalid_record"}),
            ("Invalid domain name", 406, {"--domainname": "invalid_name.example.com"}),
            ("Invalid record type", 2, {"--record_type": "invalid_type"}),
        ],
    )
    def test_integration_create_A_record_failed(
        self,
        mocker,
        caplog,
        transip_credentials_env_hash,
        default_record,
        comment,
        exit_code,
        altered_setting,
    ):
        """Test for failure on missing or incorrect parameters with record creation.

        Args:
            mocker (pytest_mock.plugin.MockerFixture):
                mock environment and command line parameters
            transip_credentials_env_hash (Fixture/Dict):
                Hash with connection credentials
            exit_code (int): exit code from script
            default_settings ([type]): [description]
            altered_setting ([type]): [description]
        """
        settings = {**default_record, **altered_setting}
        mocker.patch("os.environ", transip_credentials_env_hash)
        mocker.patch("sys.argv", ["transip_dns"] + hash_to_list(settings))

        with pytest.raises(SystemExit) as pytest_wrapped_e:
            transip_dns()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == exit_code
