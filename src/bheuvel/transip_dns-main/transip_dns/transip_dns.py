# MIT License, Copyright (c) 2020 Bob van den Heuvel
# https://github.com/bheuvel/transip/blob/main/LICENSE
"""Main script, entrypoint on main()."""

import argparse
import logging
import sys
from typing import List, Tuple

import requests

from transip_dns.env_params import process_environment_variables
from transip_dns.transip_interface import (
    DNS_RECORD_TYPES,
    DnsRecord,
    RecordState,
    TransipInterface,
)

logger = logging.getLogger(__name__.split(".")[0])


class DnsRecordNotFoundAndNoTTL(Exception):
    """Raised when the DNS record is not found and no TTL provided as well."""

    pass


class DuplicateDnsRecords(Exception):
    """Raised when a duplicate DNS record found where only one is expected."""

    pass


def main() -> int:
    """Entrypoint for script and error handling endpoint.

    :return: Error number from respective classes. In case of an
             HTTP error, the returned HTTP status code (e.g. 404),
    :rtype: int
    """
    try:
        transip_dns_main()
        return 0
    except requests.exceptions.HTTPError as e:
        logger.error(e.response.json()["error"])
        sys.exit(e.response.status_code)
    except Exception as e:
        logger.error(e)
        return -1


def transip_dns_main():
    """Functional process of the script.

    This function call out to:
    - process the commandline
    - processses the parameters to create a connection with TransIP, list the
      domain and provide the requested dns record
    - Act on the commandline by
      - List the domain
      - Delete the record
      - Update or Create the record

    :raises DnsRecordNotFoundAndNoTTL: TTL was not provided and the record
                                       didn't exist. For creation TTL is
                                       required.
    """
    args = process_commandline()

    transip_interface, dns_record, domain_records = process_parameters(args)

    execute_requested_action(args, transip_interface, dns_record, domain_records)


def execute_requested_action(
    args: argparse.Namespace,
    transip_interface: TransipInterface,
    dns_record: DnsRecord,
    domain_records: list,
):
    """Execute the task which is requested by the script.

    List and Delete are explicit requests, otherwise a record
    needs to be management

    :param args: The parsed arguments from command line and environment
    :type args: argparse.Namespace
    :param transip_interface: The interface connection with TransIP
    :type transip_interface: TransipInterface
    :param dns_record: The record to be managed
    :type dns_record: DnsRecord
    :param domain_records: Listing of the respective domain
    :type domain_records: list
    """
    if args.list:
        logger.info(display_domain(domain_records, dns_record))
    elif args.delete:
        delete_dns_record(transip_interface=transip_interface, dns_record=dns_record)
    elif args.domains:
        logger.info(display_domains(transip_interface=transip_interface))
    else:
        set_dns_record(transip_interface, dns_record)


def set_dns_record(transip_interface: TransipInterface, dns_record: DnsRecord):
    """Manage the dns record as requested.

    Manage the dns record according to
    the dns_record.record_state

    :param transip_interface: The interface connection with TransIP
    :type transip_interface: TransipInterface
    :param dns_record: The record to be managed
    :type dns_record: DnsRecord
    :raises DnsRecordNotFoundAndNoTTL: If a record is not found it could be
                                       created but that requires the TTL
    """
    if dns_record.record_state == RecordState.FOUND_SAME:
        logger.info(
            (
                f"DNS record '{dns_record.fqdn}' ('{dns_record.rtype}') "
                f"has requested data: '{dns_record.content}'. No change needed"
            )
        )
    if dns_record.record_state == RecordState.FOUND_DIFFERENT:
        transip_interface.patch_dns_entry(dns_record=dns_record)
        logger.info(
            (
                f"Update DNS record completed; '{dns_record.fqdn}' "
                f"('{dns_record.rtype}'): '{dns_record.content}'"
            )
        )
    if dns_record.record_state == RecordState.NOTFOUND:
        if dns_record.expire is None:
            raise DnsRecordNotFoundAndNoTTL(
                (
                    f"Record {dns_record.fqdn} not found. "
                    "Provide TTL parameter to create this record"
                )
            )
        transip_interface.post_dns_entry(dns_record=dns_record)
        logger.info(
            (
                f"DNS record '{dns_record.fqdn}' "
                f"('{dns_record.rtype}') '{dns_record.content}' created"
            )
        )


def display_domains(transip_interface: TransipInterface) -> None:
    """Display a list of available domains for this account.

    :param transip_interface:  The interface connection with TransIP
    :type transip_interface: TransipInterface
    :return: Comma separated list in a string, of domains
    :rtype: str
    """
    domains = ""
    response = transip_interface.domains()
    if response.ok and "domains" in response.json():
        domains = (", ").join([domain["name"] for domain in response.json()["domains"]])
    return domains


def display_domain(domain_records: list, dns_record: DnsRecord) -> None:
    """Display the records in the list.

    The records in the list (domain_records) will be filtered by the attributes
    of the dns_record. E.g. is record type is set to "A", only "A" records will
    be displayed

    :param domain_records: List of domain records
    :type domain_records: list
    :param dns_record: DnsRecord which attributes are used as filter
    :type dns_record: DnsRecord
    """
    filtered_list = []
    message = ""
    record_filters = {
        dns_record.name: "name",
        dns_record.rtype: "rtype",
        dns_record.content: "content",
        dns_record.expire: "expire",
    }
    # Generate message
    for record in record_filters:
        if record:
            message += f"{record_filters[record]}: {record}, "
    # If message is empty, no filter needs to be applied
    if len(message) == 0:
        filtered_list = domain_records
    else:
        message = "Filter domain listing on " + message[:-2]
        logger.info(message)
        filtered_list = filter_domain_records(domain_records, dns_record)

    if len(filtered_list) == 0:
        if len(message) > 0:
            logger.info("No results were returned after filter " + message[:-2])
        else:
            logger.warn("No record returned for domain.")
    if len(filtered_list) > 0:
        # logger.info(pretty_print_domain_list(filtered_list))
        return pretty_print_domain_list(filtered_list)


def pretty_print_domain_list(zone_list: list) -> str:
    """Build a (text) table for printing.

    Build a string "table" where columns of data are aligned

    :param zone_list: list of records in the zone
    :type zone_list: list
    :return: "table" string of records and properties
    :rtype: str
    """
    lengths = {}
    for record in zone_list:
        for record_key_name in record.keys():
            max_length_item_or_name = max(
                len(str(record[record_key_name])) + 1, len(str(record_key_name)) + 1
            )
            if record_key_name not in lengths:
                lengths[record_key_name] = max_length_item_or_name
            else:
                lengths[record_key_name] = max(
                    lengths[record_key_name], max_length_item_or_name
                )

    sorted_tuples = sorted(lengths.items(), key=lambda item: item[1])
    line_report = "\n"
    for column_name in sorted_tuples:
        line_report += f"{column_name[0]:{column_name[1]}}"
    line_report += "\n"

    for record in zone_list:
        for column_value in sorted_tuples:
            line_report += f"{record[column_value[0]]:<{column_value[1]}}"
        line_report += "\n"
    return line_report


def filter_domain_records(
    domain_records: list, dns_record: DnsRecord, ignore_content: bool = False
) -> list:
    """Filter the domain, based on attributes of the passed record.

    This method is used for both filtering the listing of a domain, but also
    for searching for the record which may need to be changed. In the latter
    case the content may be different (ignored) for it to be a match as to
    change it to the desired content (address).

    :param domain_records: List of domain records
    :type domain_records: list
    :param dns_record: Record or filter to search for in the list
    :type dns_record: DnsRecord
    :param ignore_content: Ignore match on content if looking for a record which
                           may have different content, defaults to False
    :type ignore_content: bool, optional
    :return: Filtered list of domain records. Preferably one when looking for
             the record to be changed
    :rtype: list
    """
    return list(
        filter(
            lambda record: (
                dns_record.name is None
                or dns_record.name.casefold() == record["name"].casefold()
            )
            and (
                dns_record.content is None
                or (
                    dns_record.content.casefold() == record["content"].casefold()
                    or ignore_content
                )
            )
            and (dns_record.expire is None or dns_record.expire == record["expire"])
            and (
                dns_record.rtype is None
                or dns_record.rtype.casefold() == record["type"].casefold()
            ),
            domain_records,
        )
    )


def delete_dns_record(
    transip_interface: TransipInterface, dns_record: DnsRecord
) -> None:
    """Delete specified DNS record.

    :param transip_interface: The interface connection with TransIP
    :type transip_interface: TransipInterface
    :param dns_record: The record to be deleted
    :type dns_record: DnsRecord
    """
    if dns_record.record_state == RecordState.NOTFOUND:
        logger.info(f"Record {dns_record.fqdn} not present. No deletion executed.")
        return

    logger.debug(f"Attempt to delete record {dns_record.fqdn}.")

    transip_interface.delete_dns_entry(dns_record=dns_record)

    logger.info(
        (
            f"DNS record '{dns_record.fqdn}' ('{dns_record.rtype}')"
            f" '{dns_record.content}' deleted"
        )
    )


def record_state_in_domain(dns_record: DnsRecord, domain_records: list) -> RecordState:
    """Report if the record is missing or present, different or the same.

    First the record will be searched for, using filter_domain_records.
    Raises an exception if multiple records are found. As this script is not
    designed to handle this, it will raise an exception.

    The single record is tagged with the possible enumerations of the RecordState class
    NOTFOUND: The record is not present
    FOUND_SAME: Record is present and the content is (already) the same
    FOUND_DIFFERENT: Record is present, but with different content
    FOUND_NO_REQUEST_DATA: If the content of the (requested) dns_record is empty.
                           This may occur when deleting a record (just) by name.


    Note on expire/TTL: To create/change/delete a record, type, content and TTL
    must all be present for each of the API calls. If the TTL was not provided
    on the commandline, the (only) )found record will be assumed to be the
    targeted record, therefore it's TTL will be entered in the dns_record if it
    is missing.

    :param dns_record: Record to search for in the domain list
    :type dns_record: DnsRecord
    :param domain_records: List of domain records
    :type domain_records: list
    :raises DuplicateDnsRecords: More the one record was found.
    :return: The state of the record in the domain list
    :rtype: RecordState
    """
    record_list = filter_domain_records(domain_records, dns_record, ignore_content=True)

    if len(record_list) > 1:
        records_data = ", ".join([record["content"] for record in record_list])
        raise DuplicateDnsRecords(
            (
                f"Multiple records found for '{dns_record.fqdn}' "
                f"('{dns_record.rtype}'); '{records_data}'. "
                "Not processing as this may lead to unexpected results"
            )
        )

    if len(record_list) == 0:
        logger.info(f"Record '{dns_record.fqdn}', type '{dns_record.rtype}' not found!")
        return RecordState.NOTFOUND

    if len(record_list) == 1:
        if dns_record.expire is None:
            dns_record.expire = record_list[0]["expire"]

        if dns_record.content is None:
            dns_record.content = record_list[0]["content"]
            return RecordState.FOUND_NO_REQUEST_DATA

        if dns_record.content == record_list[0]["content"]:
            return RecordState.FOUND_SAME

        return RecordState.FOUND_DIFFERENT


def process_commandline() -> argparse.Namespace:
    """Process commandline, enhanced with environment variables.

    The ArgumentParser is split into two parsing moments;
    1. First handle list and delete (and log while we are at it)
    2. Handle the remaining arguments

    The second step may be adjusted by the first; some argument turn from
    required to optional, e.g. record_name becomes optional when requesting
    a list of the domain, of for content/query4/6 not at least one of them is
    required in case of delete.

    Before each parse_known_args, process_environment_variables will
    integrate environment variables into the commandline parsing.

    :return: The parsed arguments object
    :rtype: argparse.Namespace
    """
    loglevel_names = [logging._levelToName[val] for val in logging._levelToName]

    pre_parser = argparse.ArgumentParser(add_help=False)

    pre_parser.add_argument(
        "--list", action="store_true", help="List the records in the domain"
    )
    pre_parser.add_argument(
        "--domains", action="store_true", help="List the available domains"
    )
    group_transip = pre_parser.add_argument_group(title="TransIP connection parameters")
    group_transip.add_argument(
        "--token",
        required=False,
        metavar="token",
        help="TransIP Access Token",
    )  # env_var="TID_TOKEN",
    group_running = pre_parser.add_argument_group(title="Running parameters")  #
    group_running.add_argument(
        "-l",
        "--log",
        default="INFO",
        choices=loglevel_names,
        type=str.upper,
        help="Loglevel (default: %(default)s)",
    )  # env_var="TID_LOG",
    group_running.add_argument(
        "--log_format",
        default="console",
        choices=["console", "fileformat"],
        help="Loglevel (default: %(default)s)",
    )  # env_var="TID_LOG_FORMAT",
    group_running.add_argument(
        "--delete", action="store_true", help="Delete the record"
    )  # env_var="TID_DELETE"
    process_environment_variables(pre_parser)
    args, remaining_argv = pre_parser.parse_known_args(sys.argv[1:])

    logger = logging.getLogger(__name__.split(".")[0])
    logger.setLevel(level=logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(level=args.log)

    # Only stack traces when DEBUG logging
    sys.excepthook = (
        lambda exctype, exc, traceback: sys.debug_hook(exctype, exc, traceback)
        if logging._nameToLevel[args.log] <= logging.DEBUG
        else print(f"{exctype.__name__}: {exc}")
    )

    if args.log_format == "fileformat":
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)

    logger.addHandler(ch)

    required__unless_token_provided = args.token is False
    required__unless_domains_requested = args.domains is False
    required__unless_list_requested = args.list is False and args.domains is False
    required__unless_delete_requested = args.delete is False

    parser = argparse.ArgumentParser(
        parents=[pre_parser], formatter_class=argparse.RawDescriptionHelpFormatter
    )

    group_transip = parser.add_argument_group(title="TransIP connection parameters")
    group_transip.add_argument(
        "-u",
        "--user",
        required=required__unless_token_provided,
        metavar="username",
        help="TransIP user login name",
    )  # env_var="TID_USER",

    group_file = parser.add_mutually_exclusive_group(
        required=required__unless_token_provided
    )
    group_file.add_argument(
        "-p",
        "--private_key",
        metavar="DATA",
        help="TransIP user private key",
    )  # env_var="TID_PRIVATE_KEY",
    group_file.add_argument(
        "-f",
        "--private_key_file",
        metavar="/path/...",
        help="TransIP user private key path to file",
    )  # env_var="TID_PRIVATE_KEY_FILE",

    group_record = parser.add_argument_group(title="Targeted record parameters")
    group_record.add_argument(
        "-d",
        "--domainname",
        required=required__unless_domains_requested,
        help="The domainname (the targeted zone)",
    )  # env_var="TID_DOMAINNAME",
    group_record.add_argument(
        "-n",
        "--record_name",
        required=required__unless_list_requested,
        help="Record name of the targeted record",
    )  # env_var="TID_RECORD_NAME",
    group_record.add_argument(
        "-t",
        "--record_type",
        default=("A" if not args.list else None),
        choices=DNS_RECORD_TYPES,
        type=str.upper,
        help="Record type of the targeted record (default: %(default)s)",
    )  # env_var="TID_RECORD_TYPE",
    group_record.add_argument(
        "-e",
        "--record_ttl",
        type=int,
        metavar="TTL",
        help=(
            "TTL (seconds) of the targeted record, "
            "NOTE: Required when creating a new record"
        ),
    )  # env_var="TID_RECORD_TTL",

    group_query = parser.add_mutually_exclusive_group(
        required=not (
            required__unless_list_requested or required__unless_delete_requested
        )
    )
    group_query.add_argument(
        "-r",
        "--record_data",
        metavar="w.x.y.z",
        help="Override the (autodiscovered) ip address",
    )  # env_var="TID_RECORD_DATA",
    group_query.add_argument(
        "-q",
        "--query_ip",
        "--query_ipv4",
        nargs="?",
        const="https://ipv4.icanhazip.com",
        dest="query_url",
        help="Query for ip (v4) address, and use as record data",
    )  # env_var="TID_QUERY_IPv4",
    group_query.add_argument(
        "--query_ipv6",
        nargs="?",
        const="https://ipv6.icanhazip.com",
        dest="query_url",
        help="Query for ip (v4) address, and use as record data",
    )  # env_var="TID_QUERY_IPv6",

    process_environment_variables(parser)
    args, remaining_argv = parser.parse_known_args()
    if remaining_argv:
        parser.print_usage()
        logger.error(
            (
                "Parameters unknown or not valid with used combination "
                f"{', '.join(remaining_argv)}"
            )
        )
        exit(2)

    return args


def process_parameters(
    args: argparse.Namespace,
) -> Tuple[TransipInterface, DnsRecord, List]:
    """Functionally process the parameters into usable objects.

    Provide a connection with TransIP, a record object of the targeted record
    and a domainlisting.


    :param args: the parsed arguments from command line and environment
    :type args: argparse.Namespace
    :return: [description]
    :rtype: Tuple[TransipInterface, DnsRecord, List]
    """
    dns_record = DnsRecord(
        name=args.record_name,
        rtype=args.record_type,
        expire=args.record_ttl,
        content=args.record_data,
        zone=args.domainname,
        query_data=args.query_url,
    )

    transip_interface = TransipInterface(
        login=args.user,
        private_key_pem=args.private_key,
        private_key_pem_file=args.private_key_file,
        access_token=args.token,
        global_key=True,
    )

    domain_records = []
    if args.domains is False:
        response = transip_interface.get_dns_entry(dns_zone_name=dns_record.zone)
        domain_records = response.json()["dnsEntries"]

        if dns_record.name is not None:
            # Can only occur when list of domain is requested
            dns_record.record_state = record_state_in_domain(dns_record, domain_records)

    return (transip_interface, dns_record, domain_records)
