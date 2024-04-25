from __future__ import print_function
from sys import version_info, stdout
import argparse
import random
from itertools import product
from caringcaribou.utils.can_actions import CanActions
from caringcaribou.utils.common import hex_str_to_nibble_list, int_from_byte_list, list_to_hex_str, parse_int_dec_or_hex
from caringcaribou.utils.constants import ARBITRATION_ID_MAX, ARBITRATION_ID_MIN, BYTE_MAX, BYTE_MIN
from time import sleep


# Python 2/3 compatibility
if version_info[0] == 2:
    range = xrange
    input = raw_input

# Number of seconds to wait between messages
DELAY_BETWEEN_MESSAGES = 0.01
# Message data length limits
MIN_DATA_LENGTH = 1
MAX_DATA_LENGTH = 8
# Max size of random seed if no seed is provided in arguments
DEFAULT_SEED_MAX = 2 ** 16
# Number of sub-lists to split message list into per round in 'replay' mode
REPLAY_NUMBER_OF_SUB_LISTS = 5


def directive_str(arb_id, data):
    """
    Converts a directive into its string representation.

    :param arb_id: Arbitration ID of the CAN message.
    :param data: Data of the CAN message.
    :return: A string representation of the cansend directive.
    """
    data = list_to_hex_str(data, "")
    directive = "{0:03X}#{1}".format(arb_id, data)
    return directive


def write_directive_to_file_handle(file_handle, arb_id, data):
    """
    Writes a cansend directive to an output file.

    :param file_handle: File handler for the output file.
    :param arb_id: Arbitration ID of the CAN message.
    :param data: Data of the CAN message.
    """
    directive = directive_str(arb_id, data)
    file_handle.write("{0}\n".format(directive))


def set_seed(seed=None):
    """
    Seeds the PRNG with a given seed or generates a random seed if none is provided.

    :param seed: Optional seed value. If None, a random seed is generated.
    """
    if seed is None:
        seed = random.randint(0, DEFAULT_SEED_MAX)
    print("Seed: {0} (0x{0:x})".format(seed))
    random.seed(seed)


def parse_directive(directive):
    """
    Parses a cansend directive into its components.

    :param directive: The string representation of the cansend directive.
    :return: A tuple containing the arbitration ID and a list of data values.
    """
    segments = directive.split("#")
    arb_id = int(segments[0], 16)
    data_str = segments[1]
    data = [int(data_str[i:i + 2], 16) for i in range(0, len(data_str), 2)]
    return arb_id, data


def apply_fuzzed_data(initial_data, fuzzed_nibbles, bitmap):
    """
    Applies fuzzed nibbles onto initial data based on a given bitmap.

    :param initial_data: Initial nibbles to be fuzzed.
    :param fuzzed_nibbles: Fuzzed nibbles to apply on initial_data.
    :param bitmap: A bitmap indicating which parts of initial_data should be replaced by fuzzed_nibbles.
    :return: The result of fuzzing as a list of bytes.
    """
    fuzz_index = 0
    result_bytes = []
    for index in range(0, len(bitmap), 2):
        # Apply fuzzed nibbles on top of initial data
        if bitmap[index]:
            high_nibble = fuzzed_nibbles[fuzz_index]
            fuzz_index += 1
        else:
            high_nibble = initial_data[index]

        if bitmap[index + 1]:
            low_nibble = fuzzed_nibbles[fuzz_index]
            fuzz_index += 1
        else:
            low_nibble = initial_data[index + 1]

        current_byte = (high_nibble << 4) + low_nibble
        result_bytes.append(current_byte)
    return result_bytes


def nibbles_to_bytes(nibbles):
    """
    Converts a list of nibbles to a corresponding list of bytes.

    :param nibbles: A list of nibble values (0x0-0xF).
    :return: A list of bytes represented by the input nibbles.
    """
    result_bytes = []
    for index in range(0, len(nibbles), 2):
        high_nibble = nibbles[index]
        low_nibble = nibbles[index + 1]
        current_byte = (high_nibble << 4) + low_nibble
        result_bytes.append(current_byte)
    return result_bytes


def split_lists(full_list, pieces):
    """
    Splits a list into a specified number of sub-lists.

    :param full_list: The original list to be split.
    :param pieces: The number of sub-lists to generate.
    :return: A generator yielding each sub-list.
    """
    length = len(full_list)
    for i in range(pieces):
        sub_list = full_list[i * length // pieces: (i + 1) * length // pieces]
        if len(sub_list) == 0:
            continue
        yield sub_list


def get_random_arbitration_id(min_id, max_id):
    """
    Generates a random arbitration ID within a specified range.

    :param min_id: Minimum possible value for the arbitration ID.
    :param max_id: Maximum possible value for the arbitration ID.
    :return: A random arbitration ID within the given range.
    """
    arb_id = random.randint(min_id, max_id)
    return arb_id


def get_random_data(min_length, max_length):
    """
    Generates random data within specified length boundaries.

    :param min_length: Minimum length of the data.
    :param max_length: Maximum length of the data.
    :return: A list of random byte values within the specified length.
    """
    data_length = random.randint(min_length, max_length)
    data = [random.randint(BYTE_MIN, BYTE_MAX) for _ in range(data_length)]
    return data


def parse_directives_from_file(filename):
    """
    Reads and parses cansend directives from a file.

    :param filename: Path to the file containing the directives.
    :return: A list of parsed directives.
    """
    print("Parsing messages from {0}".format(filename))
    directives = []
    with open(filename, "r") as fd:
        for line_number, directive in enumerate(fd, 1):
            directive = directive.strip()
            if directive:
                try:
                    directives.append(parse_directive(directive))
                except ValueError:
                    print("  Error: Could not parse message on line {0}: {1}".format(line_number, directive))
    return directives


def pad_to_even_length(original_list, padding=0x0):
    """
    Ensures a list has an even length by potentially prepending a padding value.

    :param original_list: The list to be processed.
    :param padding: The value to prepend if the length of original_list is odd.
    :return: A possibly modified list with an even length.
    """
    if len(original_list) % 2 == 1:
        original_list.insert(0, padding)
    return original_list


def random_fuzz(static_arb_id=None, static_data=None, filename=None, min_id=ARBITRATION_ID_MIN,
                max_id=ARBITRATION_ID_MAX, min_data_length=MIN_DATA_LENGTH, max_data_length=MAX_DATA_LENGTH,
                start_index=0, show_status=True, seed=None):
    """
    A fuzzer function that sends random or specified CAN messages.

    :param static_arb_id: Optional static arbitration ID. Can be set to send fixed ID frames.
    :param static_data: Optional static data. Can be set to send fixed data payloads.
    :param filename: Optional filename to log the sent directives.
    :param min_id: Minimum possible random arbitration ID.
    :param max_id: Maximum possible random arbitration ID.
    :param min_data_length: Minimum length of the random data.
    :param max_data_length: Maximum length of the random data.
    :param start_index: Index from which to start sending messages.
    :param show_status: Whether to display sending status.
    :param seed: Seed value for random number generation.
    """
    # Detailed implementation continues here...

# Further definitions of bruteforce_fuzz, mutate_fuzz, replay_fuzz, identify_fuzz, __handle_random, parse_hex_and_dot_indices, __handle_bruteforce, __handle_mutate, __handle_replay, parse_args etc.
