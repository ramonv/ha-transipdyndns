# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Integration testing against the actual TransIP API.

NOTE: This allows the useage of the demo token
"""


from tests.funcint_shared_tests_transip_dns import (
    create_change_delete_testing,
    create_record_testing,
    delete_record_testing,
    ipv4_query_testing,
)


class TestTransipDns_Shared_Integration_Functional:
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


# def test_ipv4_query(
#     mocker, caplog, transip_credentials_env_hash, ipv4_query_test_record
# ):
#     ipv4_query_testing(
#         mocker, caplog, transip_credentials_env_hash, ipv4_query_test_record
#     )
