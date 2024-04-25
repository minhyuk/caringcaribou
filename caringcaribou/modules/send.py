from caringcaribou.utils.can_actions import CanActions
from caringcaribou.utils.common import list_to_hex_str, parse_int_dec_or_hex, str_to_int_list
from caringcaribou.utils.constants import ARBITRATION_ID_MAX, ARBITRATION_ID_MAX_EXTENDED
from time import sleep
from sys import exit
import argparse
import re


FILE_LINE_COMMENT_PREFIX = "#"
PADDING_BYTE = 0x00


class CanMessage:
    """
    Message wrapper class used by file parsers.
    """

    def __init__(self, arb_id, data, delay, is_extended=None, is_error=False, is_remote=False):
        """
        Initialize a new CAN message with given parameters.

        :param arb_id: int - The arbitration ID of the CAN message.
        :param data: list of int - The data bytes of the CAN message.
        :param delay: float - The delay in seconds before this message should be sent.
        :param is_extended: bool or None - Specifies if this message uses extended arbitration ID.
        :param is_error: bool - Indicates if this is an error message.
        :param is_remote: bool - Indicates if this message is a remote transmission request.
        """
        self.arb_id = arb_id
        self.data = data
        # Negative delays are not allowed
        self.delay = max([delay, 0.0])
        if is_extended is None:
            self.is_extended = arb_id > ARBITRATION_ID_MAX
        else:
            self.is_extended = is_extended
        self.is_error = is_error
        self.is_remote = is_remote


def parse_messages(msgs, delay, pad):
    """
    Parses a list of message strings into CanMessage objects.

    :param msgs: List of str - Messages in the format 'ARBITRATION_ID#DATA'.
    :param delay: float - Delay to be applied to each message.
    :param pad: bool - Indicates whether messages should be padded to 8 bytes.
    :return: list of CanMessage instances created from the input strings.
    """
    message_list = []
    msg = None
    try:
        for msg in msgs:
            msg_parts = msg.split("#", 1)
            # Check arbitration ID
            arb_id = parse_int_dec_or_hex(msg_parts[0])
            if arb_id is None:
                raise ValueError("Invalid arbitration ID: '{0}'".format(msg_parts[0]))
            if arb_id > ARBITRATION_ID_MAX_EXTENDED:
                raise ValueError("Arbitration ID too large (max is 0x{0:x})".format(ARBITRATION_ID_MAX_EXTENDED))
            # Check data length
            byte_list = msg_parts[1].split(".")
            if not 0 < len(byte_list) <= 8:
                raise ValueError("Invalid data length: {0}".format(len(byte_list)))
            # Validate data bytes
            msg_data = []
            for byte in byte_list:
                byte_int = int(byte, 16)
                if not 0x00 <= byte_int <= 0xff:
                    raise ValueError("Invalid byte value: '{0}'".format(byte))
                msg_data.append(byte_int)
            if pad:
                # Pad to 8 bytes
                msg_data.extend([PADDING_BYTE] * (8 - len(msg_data)))
            fixed_msg = CanMessage(arb_id, msg_data, delay)
            message_list.append(fixed_msg)
        # No delay before sending first message
        return message_list
    except ValueError as e:
        print("Invalid message at position {0}: '{1}'\nFailure reason: {2}".format(len(message_list), msg, e))
        exit()


def parse_candump_line(curr_line, prev_timestamp, force_delay):
    """
    Parses a line from a candump log file into a CanMessage object.

    :param curr_line: str - The current line from the candump log.
    :param prev_timestamp: float or None - The timestamp of the previous message (for delay calculation).
    :param force_delay: float or None - If set, overrides calculated delay with this value.
    :return: A tuple containing the CanMessage and the timestamp of the current message.
    """
    segments = curr_line.strip().split(" ")
    time_stamp = float(segments[0][1:-1])
    msg_segs = segments[2].split("#")
    arb_id = int(msg_segs[0], 16)
    data = str_to_int_list(msg_segs[1])
    if prev_timestamp is None:
        delay = 0
    elif force_delay is not None:
        delay = force_delay
    else:
        delay = time_stamp - prev_timestamp
    message = CanMessage(arb_id, data, delay)
    return message, time_stamp


def parse_pythoncan_line(curr_line, prev_timestamp, force_delay):
    """
    Parses a line from a python-can log format into a CanMessage object.

    :param curr_line: str - The current line from a python-can log.
    :param prev_timestamp: float or None - The timestamp of the previous message (for delay calculation).
    :param force_delay: float or None - If set, overrides calculated delay with this value.
    :return: A tuple containing the CanMessage and the timestamp of the current message.
    """
    line_regex = re.compile(r"Timestamp: +(?P<timestamp>\d+\.\d+) +ID: (?P<arb_id>[0-9a-fA-F]+) +"
                            r"((\d+)|(?P<is_extended>[SX]) (?P<is_error>[E ]) (?P<is_remote>[R ])) +"
                            r"DLC: +[0-8] +(?P<data>(?:[0-9a-fA-F]{2} ?){0,8}) *(Channel: (?P<channel>\w*))?")
    parsed_msg = line_regex.match(curr_line)
    arb_id = int(parsed_msg.group("arb_id"), 16)
    time_stamp = float(parsed_msg.group("timestamp"))
    data = list(int(a, 16) for a in parsed_msg.group("data").split(" ") if a)
    if prev_timestamp is None:
        delay = 0
    elif force_delay is not None:
        delay = force_delay
    else:
        delay = time_stamp - prev_timestamp
    # Parse flags
    is_extended = parsed_msg.group("is_extended") == "X"
    is_error = parsed_msg.group("is_error") == "E"
    is_remote = parsed_msg.group("is_remote") == "R"
    message = CanMessage(arb_id, data, delay, is_extended, is_error, is_remote)
    return message, time_stamp


def parse_file(filename, force_delay):
    """
    Parses a log file containing CAN messages in either candump or python-can format.

    :param filename: str - The path to the log file containing the CAN traffic.
    :param force_delay: float - A fixed delay between messages; if not provided, uses delays from log file.
    :return: A list of CanMessage objects parsed from the file.
    """
    try:
        messages = []
        with open(filename, "r") as f:
            timestamp = None
            line_parser = None
            for line in f:
                # Skip comments and blank lines
                if line.startswith(FILE_LINE_COMMENT_PREFIX) or len(line.strip()) == 0:
                    continue
                # First non-comment line - identify log format
                if line_parser is None:
                    if line.startswith("("):
                        line_parser = parse_candump_line
                    elif line.startswith("Timestamp"):
                        line_parser = parse_pythoncan_line
                    else:
                        raise IOError("Unrecognized file type - could not parse file")
                # Parse line
                try:
                    msg, timestamp = line_parser(line, timestamp, force_delay)
                except (ValueError, AttributeError) as e:
                    raise IOError("Could not parse line:\n  '{0}'\n  Reason: {1}".format(line.rstrip("\n"), e))
                messages.append(msg)
            return messages
    except IOError as e:
        print("ERROR: {0}\n".format(e))
        return None


def send_messages(messages, loop):
    """
    Sends a list of CanMessage objects with the specified delays between them.

    :param messages: List of CanMessage - The messages to be sent.
    :param loop: bool - Whether to continuously loop through the messages list and send messages.
    """
    with CanActions(notifier_enabled=False) as can_wrap:
        loop_counter = 0
        while True:
            for i in range(len(messages)):
                msg = messages[i]
                if i != 0 or loop_counter != 0:
                    sleep(msg.delay)
                print("  Arb_id: 0x{0:08x}, data: {1}".format(msg.arb_id, list_to_hex_str(msg.data, ".")))
                can_wrap.send(msg.data, msg.arb_id, msg.is_extended, msg.is_error, msg.is_remote)
            if not loop:
                break
            loop_counter += 1


def __handle_parse_messages(args):
    """
    Handles the 'message' subcommand to parse message strings from command line arguments.

    :param args: argparse.Namespace - The namespace object containing command line arguments.
    :return: list of CanMessage instances parsed from the command line arguments.
    """
    message_strings = args.msg
    delay = args.delay
    pad = args.pad
    messages = parse_messages(message_strings, delay, pad)
    return messages


def __handle_parse_file(args):
    """
    Handles the 'file' subcommand to parse messages from a file.

    :param args: argparse.Namespace - The namespace object containing command line arguments.
    :return: list of CanMessage instances parsed from the file.
    """
    filename = args.filename
    delay = args.delay
    messages = parse_file(filename, delay)
    return messages


def parse_args(args):
    """
    Parses the arguments passed to the send module.

    :param args: list of str - The list of arguments passed from the command line.
    :return: argparse.Namespace object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(prog="cc.py send",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="Raw message transmission module for CaringCaribou.\n"
                                                 "Messages can be passed as command line arguments or through a file.",
                                     epilog="""Example usage:
  cc.py send message 0x7a0#c0ffee.00.11.22.33.44
  cc.py send message -d 0.5 123#de.ad.be.ef 124#01.23.45
  cc.py send message -p 0x100#11 0x100#22.33
  cc.py send file can_dump.txt
  cc.py send file -d 0.2 can_dump.txt""")
    subparsers = parser.add_subparsers(dest="module_function")
    subparsers.required = True

    # Parser for sending messages from command line
    cmd_msgs = subparsers.add_parser("message")
    cmd_msgs.add_argument("msg", nargs="+",
                          help="message on format ARB_ID#DATA where ARB_ID is interpreted "
                               "as hex if it starts with 0x and decimal otherwise. DATA "
                               "consists of 1-8 bytes written in hex and separated by dots.")
    cmd_msgs.add_argument("--delay", "-d", metavar="D", type=float, default=0,
                          help="delay between messages in seconds")
    cmd_msgs.add_argument("--loop", "-l", action="store_true", help="loop message sequence (re-send over and over)")
    cmd_msgs.add_argument("--pad", "-p", action="store_true", help="automatically pad messages to 8 bytes length")
    cmd_msgs.set_defaults(func=__handle_parse_messages)

    # Parser for sending messages from file
    file_msg = subparsers.add_parser("file")
    file_msg.add_argument("filename", help="path to file")
    file_msg.add_argument("--delay", "-d", metavar="D", type=float, default=None,
                          help="delay between messages in seconds (overrides timestamps in file)")
    file_msg.add_argument("--loop", "-l", action="store_true", help="loop message sequence (re-send over and over)")
    file_msg.set_defaults(func=__handle_parse_file)

    args = parser.parse_args(args)
    return args


def module_main(args):
    """
    Main function for the send module.

    :param args: list of str - The list of arguments for the module.
    Executes the module based on parsed arguments and sends CAN messages as specified.
    """
    args = parse_args(args)
    print("Parsing messages")
    messages = args.func(args)
    if not messages:
        print("No messages parsed")
    else:
        print("  {0} messages parsed".format(len(messages)))
        print("Sending messages")
        send_messages(messages, args.loop)
