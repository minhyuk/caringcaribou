from __future__ import print_function
from caringcaribou.utils.can_actions import CanActions
from caringcaribou.utils.common import msg_to_candump_format, parse_int_dec_or_hex
from caringcaribou.modules.send import FILE_LINE_COMMENT_PREFIX
from sys import argv, stdout
import argparse
import datetime


def initiate_dump(handler, whitelist, separator_seconds, candump_format):
    """
    Initializes the process for dumping CAN bus traffic based on specified filters and formats.

    It continuously listens for CAN messages, processes them based on the given parameters, 
    and applies a specific handler function to each message. A time-based separator can be 
    used to visually distinguish periods of message inactivity.

    :param handler: A callback function that defines how each CAN message is handled.
    :param whitelist: A list of message IDs that should be processed. If empty, all messages are processed.
    :param separator_seconds: The time in seconds to wait before printing a separator 
                              to indicate a break in message traffic. If None, no separator is used.
    :param candump_format: A boolean that determines whether messages should be formatted 
                           according to the candump tool's output format.
    """
    if candump_format:
        format_func = msg_to_candump_format
    else:
        format_func = str
    separator_enabled = separator_seconds is not None
    last_message_timestamp = datetime.datetime.min
    messages_since_last_separator = 0

    print("Dumping CAN traffic (press Ctrl+C to exit)".format(whitelist))
    with CanActions(notifier_enabled=False) as can_wrap:
        for msg in can_wrap.bus:
            # Separator handling
            if separator_enabled and messages_since_last_separator > 0:
                if (datetime.datetime.now() - last_message_timestamp).total_seconds() > separator_seconds:
                    # Print separator
                    handler("--- Count: {0}".format(messages_since_last_separator))
                    messages_since_last_separator = 0
            # Message handling
            if len(whitelist) == 0 or msg.arbitration_id in whitelist:
                handler(format_func(msg))
                last_message_timestamp = datetime.datetime.now()
                messages_since_last_separator += 1


def parse_args(args):
    """
    Parses the arguments provided to the script and returns them as a structured namespace.

    This function is responsible for interpreting the command line arguments passed to the 
    dump module. It defines how the script is run and what parameters it expects, such as output 
    file location, message filtering options, and display formatting.

    :param args: The list of arguments passed to the script from the command line.
    :return: An argparse.Namespace object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(prog="cc.py dump",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="CAN traffic dump module for CaringCaribou",
                                     epilog="""Example usage:
  cc.py dump
  cc.py dump -s 1.0
  cc.py dump -f output.txt
  cc.py dump -c -f output.txt 0x733 0x734""")
    parser.add_argument("-f", "--file",
                        metavar="F",
                        help="Write output to file F (default: stdout)")
    parser.add_argument("whitelist",
                        type=parse_int_dec_or_hex,
                        metavar="W",
                        nargs="*",
                        help="Arbitration ID to whitelist")
    parser.add_argument("-c",
                        action="store_true",
                        dest="candump_format",
                        help="Output on candump format")
    parser.add_argument("-s",
                        type=float,
                        metavar="SEC",
                        dest="separator_seconds",
                        help="Print separating line after SEC silent seconds")
    args = parser.parse_args(args)
    return args


def file_header():
    """
    Constructs and returns a header string for the output file.

    This header includes the tool name, current date and time, 
    and the command line arguments used to run the dump. It's intended to provide
    context and metadata about a dump file when reviewing its contents later.

    :return: A formatted string that serves as the header for the dump file.
    """
    argument_str = " ".join(argv)
    lines = ["Caring Caribou dump file",
             str(datetime.datetime.now()),
             argument_str]
    header = "".join(["{0} {1}\n".format(FILE_LINE_COMMENT_PREFIX, line) for line in lines])
    return header


def module_main(args):
    """
    The main entry point for the dump module.

    This function orchestrates the overall process of dumping CAN messages based on 
    the provided command line arguments. It setup the conditions for message collection 
    such as output formatting, message filtering, and whether to dump to stdout or a file.

    :param args: List of arguments passed to the module from the command line.
    """
    args = parse_args(args)
    separator_seconds = args.separator_seconds
    candump_format = args.candump_format
    whitelist = args.whitelist

    # Print to stdout
    if args.file is None:
        initiate_dump(print, whitelist, separator_seconds, candump_format)
    # Print to file
    else:
        try:
            with open(args.file, "w") as output_file:
                global count
                count = 0

                # Write file header
                header = file_header()
                output_file.write(header)

                def write_line_to_file(line):
                    global count
                    count += 1
                    print("\rMessages printed to file: {0}".format(count), end="")
                    output_file.write("{0}\n".format(line))
                    stdout.flush()

                initiate_dump(write_line_to_file, whitelist, separator_seconds, candump_format)
        except IOError as e:
            print("IOError: {0}".format(e))

