# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Methods used to either ease testing or to improve readability/layout."""
from transip_dns.transip_interface import DnsRecord

from tests import transip_demo_token, transip_domain


def hash_to_list(a_hash: dict) -> list:
    """Convert single level hash to list.

    For convenience of manipulation for test sets
    """
    raw_list = list(sum(((k, v) for k, v in a_hash.items()), ()))
    return [val for val in raw_list if val is not None]


def delete_by_name_and_type(
    transip_interface,
    record_name: str,
    record_type: str = "A",
    raise_exception_if_missing: bool = False,
    raise_exception_if_found: bool = False,
):
    """Delete a specified record, if found.

    By arguments raise_exception_if_missing and raise_exception_if_found, a validation,
    assertion, can be performed to test expected outcomes. For example when doing a
    cleanup after a test has created records, then they they should actually be there.

    Args:
        transip_interface ([type]): [description]
        record_name (str): Name of the DNS record
        record_type (str, optional): DNS record type. Defaults to "A".
        raise_exception_if_missing (bool =False): raise exception if should be there
        raise_exception_if_found (bool =False): raise exception if should not be there

    Exception:
        Raise exception if an entry was supposed to be there
    """
    # Destroy record, but should results in error as it should have been deleted
    if transip_interface._token == transip_demo_token:
        return  # pragma: not live account skip live coverage
    else:  # pragma: not demo account skip demo coverage
        record_missing = True
        for record in transip_interface.get_dns_entry(transip_domain).json()[
            "dnsEntries"
        ]:
            if record["name"] == record_name and record["type"] == record_type:
                record_missing = False
                transip_interface.delete_dns_entry(
                    DnsRecord(
                        zone=transip_domain,
                        name=record_name,
                        rtype=record_type,
                        expire=record["expire"],
                        content=record["content"],
                    )
                )
                break
        if (
            raise_exception_if_missing and record_missing
        ):  # pragma: code in case test and/or cleanup failed
            raise Exception("{record_name}, {record_type}, not found for deletion")
        if (
            raise_exception_if_found and not record_missing
        ):  # pragma: code in case test and/or cleanup failed
            raise Exception(
                "{record_name}, {record_type} found, should not be here anymore"
            )
