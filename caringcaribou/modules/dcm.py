from __future__ import print_function
from caringcaribou.utils.can_actions import CanActions
from caringcaribou.utils.common import parse_int_dec_or_hex
from sys import stdout
import argparse
import time

DCM_SERVICE_NAMES = {
    0x10: "DIAGNOSTIC_SESSION_CONTROL",
    0x11: "ECU_RESET",
    0x12: "GMLAN_READ_FAILURE_RECORD",
    0x14: "CLEAR_DIAGNOSTIC_INFORMATION",
    0x19: "READ_DTC_INFORMATION",
    0x1A: "GMLAN_READ_DIAGNOSTIC_ID",
    0x20: "RETURN_TO_NORMAL",
    0x22: "READ_DATA_BY_IDENTIFIER",
    0x23: "READ_MEMORY_BY_ADDRESS",
    0x24: "READ_SCALING_DATA_BY_IDENTIFIER",
    0x27: "SECURITY_ACCESS",
    0x28: "COMMUNICATION_CONTROL",
    0x2A: "READ_DATA_BY_PERIODIC_IDENTIFIER",
    0x2C: "DYNAMICALLY_DEFINE_DATA_IDENTIFIER",
    0x2D: "DEFINE_PID_BY_MEMORY_ADDRESS",
    0x2E: "WRITE_DATA_BY_IDENTIFIER",
    0x2F: "INPUT_OUTPUT_CONTROL_BY_IDENTIFIER",
    0x31: "ROUTINE_CONTROL",
    0x34: "REQUEST_DOWNLOAD",
    0x35: "REQUEST_UPLOAD",
    0x36: "TRANSFER_DATA",
    0x37: "REQUEST_TRANSFER_EXIT",
    0x38: "REQUEST_FILE_TRANSFER",
    0x3B: "GMLAN_WRITE_DID",
    0x3D: "WRITE_MEMORY_BY_ADDRESS",
    0x3E: "TESTER_PRESENT",
    0x7F: "NEGATIVE_RESPONSE",
    0x83: "ACCESS_TIMING_PARAMETER",
    0x84: "SECURED_DATA_TRANSMISSION",
    0x85: "CONTROL_DTC_SETTING",
    0x86: "RESPONSE_ON_EVENT",
    0x87: "LINK_CONTROL",
    0xA2: "GMLAN_REPORT_PROGRAMMING_STATE",
    0xA5: "GMLAN_ENTER_PROGRAMMING_MODE",
    0xA9: "GMLAN_CHECK_CODES",
    0xAA: "GMLAN_READ_DPID",
    0xAE: "GMLAN_DEVICE_CONTROL"
}

NRC = {
    0x10: "generalReject",
    0x11: "serviceNotSupported",
    0x12: "sub-functionNotSupported",
    0x13: "incorrectMessageLengthOrInvalidFormat",
    0x14: "responseTooBig",
    0x21: "busyRepeatRequest",
    0x22: "conditionsNotCorrect",
    0x24: "requestSequenceError",
    0x25: "noResponseFromSub-netComponent",
    0x26: "failurePreventsExecutionOfRequestedAction",
    0x31: "requestOutOfRange",
    0x33: "securityAccessDenied",
    0x35: "invalidKey",
    0x36: "exceededNumberOfAttempts",
    0x37: "requiredTimeDelayNotExpired",
    0x70: "uploadDownloadNotAccepted",
    0x71: "transferDataSuspended",
    0x72: "generalProgrammingFailure",
    0x73: "wrongBlockSequenceCounter",
    0x78: "requestCorrectlyReceivedResponsePending",
    0x7E: "sub-FunctionNotSupportedInActiveSession",
    0x7F: "serviceNotSupportedInActiveSession"
}


def insert_message_length(data, pad=False):
    """
    Inserts a message length byte before the payload data and optionally pads the data to 8 bytes.

    :param data: The payload data as a list of bytes.
    :param pad: Boolean indicating whether the data should be padded to 8 bytes.
    :return: A list of bytes with the length byte prepended and optionally padded to 8 bytes.
    """
    length = len(data)
    if length > 7:
        raise IndexError("Data can only contain up to 7 bytes: {0}".format(len(data)))
    full_data = [length] + data
    if pad:
        full_data += [0x00] * (7-length)
    return full_data


def dcm_dtc(args):
    """
    Sends a request to retrieve or clear Diagnostic Trouble Codes (DTCs) from a vehicle's ECU.

    :param args: A namespace containing the source ID (src), destination ID (dst), and an optional flag to clear DTCs.
    """
    send_arb_id = args.src
    rcv_arb_id = args.dst
    clear = args.clear
    big_data = []
    big_data_size = 0

    # Helper functions omitted for brevity

    with CanActions(arb_id=send_arb_id) as can_wrap:
        # Logic to send the DTC request is omitted for brevity    

def dcm_discovery(args):
    """
    Scans for ECUs in a vehicle that support diagnostic sessions by sending diagnostic session control messages.

    :param args: A namespace containing arguments for the discovery process, including ranges of arbitration IDs to scan.
    """
    min_id = args.min
    max_id = args.max
    no_stop = args.nostop
    blacklist = args.blacklist

    # Logic for discovery is omitted for brevity

def service_discovery(args):
    """
    Discovers diagnostic services supported by an ECU by sending service requests across the diagnostic session.

    :param args: A namespace containing the source and destination arbitration IDs.
    """
    send_arb_id = args.src
    rcv_arb_id = args.dst

    # Logic for service discovery is omitted for brevity

def subfunc_discovery(args):
    """
    Discovers the supported sub-functions for a given diagnostic service by sending service requests with varied sub-function parameters.

    :param args: A namespace containing source and destination IDs, the service ID to probe, and other options.
    """
    send_arb_id = args.src
    rcv_arb_id = args.dst
    service_id = args.service
    show_data = args.show
    bruteforce_indices = args.i

    # Additional logic is omitted for brevity

def tester_present(args):
    """
    Continuously sends the TesterPresent service to keep a diagnostic session active.

    :param args: A namespace with source arbitration ID, delay between messages, and an option to suppress positive responses.
    """
    send_arb_id = args.src
    delay = args.delay
    suppress_positive_response = args.spr

    # The actual sending logic is omitted for brevity

def parse_args(args):
    """
    Parses the command-line arguments provided to the diagnostics module.

    This function defines the CLI (Command Line Interface) structure and calls the appropriate function based on the user's input.

    :param args: List of command-line arguments.
    :return: Parsed arguments in a namespace.
    """
    # Argument parsing logic is omitted for brevity

def module_main(arg_list):
    """
    Entry point for the diagnostics module, handling user commands and invoking the appropriate functionalities.

    :param arg_list: List of arguments provided by the user.
    """
    try:
        args = parse_args(arg_list)
        # The rest of the function logic is omitted for brevity
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
