from __future__ import print_function
from caringcaribou.utils.constants import ARBITRATION_ID_MAX, ARBITRATION_ID_MAX_EXTENDED, ARBITRATION_ID_MIN, BYTE_MAX, BYTE_MIN
from sys import stdout, version_info
import can
import time

# Handle large ranges efficiently in both python 2 and 3
if version_info[0] == 2:
    range = xrange


MESSAGE_DELAY = 0.1
DELAY_STEP = 0.02
NOTIFIER_STOP_DURATION = 0.5

# Global CAN interface setting, which can be set through the -i flag to cc.py
# The value None corresponds to the default CAN interface (typically can0)
DEFAULT_INTERFACE = None


def auto_blacklist(bus, duration, classifier_function, print_results):
    """Listens for false positives on the CAN bus and generates an arbitration ID blacklist.

    Finds all can.Message <msg> on 'bus' where 'classifier_function(msg)' evaluates to True.
    Terminates after 'duration' seconds and returns a set of all matching arbitration IDs.
    Prints progress, time countdown and list of results if 'print_results' is True.

    :param bus: CAN bus instance
    :param duration: duration in seconds
    :param classifier_function: function which, when called upon a can.Message instance,
                                returns a bool indicating if it should be blacklisted
    :param print_results: whether progress and results should be printed to stdout
    :type bus: can.Bus
    :type duration: float
    :type classifier_function: function
    :type print_results: bool
    :return set of matching arbitration IDs to blacklist
    :rtype set(int)
    """
    if print_results:
        print("Scanning for arbitration IDs to blacklist")
    blacklist = set()
    start_time = time.time()
    end_time = start_time + duration
    while time.time() < end_time:
        if print_results:
            time_left = end_time - time.time()
            num_matches = len(blacklist)
            print("\r{0:> 5.1f} seconds left, {1} found".format(time_left, num_matches), end="")
            stdout.flush()
        # Receive message
        msg = bus.recv(0.1)
        if msg is None:
            continue
        # Classify
        if classifier_function(msg):
            # Add to blacklist
            blacklist.add(msg.arbitration_id)
    if print_results:
        num_matches = len(blacklist)
        print("\r  0.0 seconds left, {0} found".format(num_matches), end="")
        if len(blacklist) > 0:
            print("\n  Detected IDs: {0}".format(" ".join(sorted(list(map(hex, blacklist))))))
        else:
            print()
    return blacklist


class CanActions:

    def __init__(self, arb_id=None, notifier_enabled=True):
        """
        Initializes the CanActions class instance.

        This constructor sets the CAN bus interface and the optional default arbitration ID,
        and optionally enables CAN message notifications.

        :param arb_id: Optional; An integer specifying the default arbitration ID to be used by the instance.
        :param notifier_enabled: Optional; A boolean that specifies whether to enable the notification listener for incoming CAN messages.
        """
        self.bus = can.Bus(context=DEFAULT_INTERFACE)
        self.arb_id = arb_id
        self.bruteforce_running = False
        self.notifier = None
        if notifier_enabled:
            self.enable_notifier()

    def __enter__(self):
        """Enter context manager method, enabling use with the 'with' statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager method, disables the notifier and shuts down the CAN bus upon exiting the 'with' block."""
        if self.notifier is not None:
            self.disable_notifier()
        self.bus.shutdown()

    def enable_notifier(self):
        """Enables the CAN message notifier with no listeners."""
        self.notifier = can.Notifier(self.bus, listeners=[])

    def disable_notifier(self):
        """Disables the CAN message notifier, clearing listeners and stopping it gracefully."""
        self.clear_listeners()
        # Prevent threading errors by stopping notifier gracefully
        self.notifier.stop(NOTIFIER_STOP_DURATION)
        self.notifier = None

    def add_listener(self, listener):
        """Adds a listener to the notifier.

        :param listener: The listener to add, typically a function that processes incoming CAN messages.
        """
        self.notifier.listeners.append(listener)

    def clear_listeners(self):
        """Clears all listeners from the notifier."""
        self.notifier.listeners = []

    def set_listener(self, listener):
        """Sets the specified listener as the sole listener for incoming CAN messages.

        :param listener: The listener to set, typically a function that processes incoming CAN messages.
        """
        self.clear_listeners()
        self.add_listener(listener)

    def send(self, data, arb_id=None, is_extended=None, is_error=False, is_remote=False):
        """Sends a CAN message with the specified parameters and payload.

        :param data: The data payload of the CAN message as a bytearray.
        :param arb_id: Optional; The arbitration ID of the CAN message. Defaults to the instance's arb_id if not specified.
        :param is_extended: Optional; Boolean to indicate if the message uses extended arbitration ID. Determined automatically if not specified.
        :param is_error: Optional; Boolean to indicate if the message is an error frame.
        :param is_remote: Optional; Boolean to indicate if the message is a remote frame.
        """
        if len(data) > 8:
            raise IndexError("Invalid CAN message length: {0}".format(len(data)))
        # Fallback to default arbitration ID (self.arb_id) if no other ID is specified
        if arb_id is None:
            if self.arb_id is None:
                raise ValueError("Arbitration ID must be set through either 'arb_id' argument or self.arb_id")
            arb_id = self.arb_id
        # Force extended flag if it is unspecified and arbitration ID is larger than the standard format allows
        if is_extended is None:
            is_extended = arb_id > ARBITRATION_ID_MAX
        msg = can.Message(arbitration_id=arb_id,
                          data=data,
                          is_extended_id=is_extended,
                          is_error_frame=is_error,
                          is_remote_frame=is_remote)
        self.bus.send(msg)

    def bruteforce_arbitration_id(self, data, callback, min_id, max_id,
                                  callback_end=None):
        """Bruteforce CAN arbitration IDs within the specified range, sending data and executing the callback for each.

        :param data: The data payload to send with each CAN message.
        :param callback: The callback function to execute for each arbitration ID.
        :param min_id: The minimum arbitration ID to start brute-forcing from.
        :param max_id: The maximum arbitration ID to brute-force up to.
        :param callback_end: Optional; The function to call when the bruteforce operation completes.
        """
        # Set limits
        if min_id is None:
            min_id = ARBITRATION_ID_MIN
        if max_id is None:
            if min_id <= ARBITRATION_ID_MAX:
                max_id = ARBITRATION_ID_MAX
            else:
                # If min_id is extended, use an extended default max_id as well
                max_id = ARBITRATION_ID_MAX_EXTENDED
        # Sanity checks
        if min_id > max_id:
            if callback_end:
                callback_end("Invalid range: min > max")
            return
        # Start bruteforce
        self.bruteforce_running = True
        for arb_id in range(min_id, max_id + 1):
            self.notifier.listeners = [callback(arb_id)]
            # Use standard addressing (11 bits arbitration ID) instead of extended (29 bits) when possible
            extended = False
            if arb_id > ARBITRATION_ID_MAX:
                extended = True
            msg = can.Message(arbitration_id=arb_id, data=data, is_extended_id=extended)
            self.bus.send(msg)
            time.sleep(MESSAGE_DELAY)
            # Return if stopped by calling module
            if not self.bruteforce_running:
                self.clear_listeners()
                return
        # Callback if bruteforce finished without being stopped
        if callback_end:
            self.clear_listeners()
            callback_end("Bruteforce of range 0x{0:x}-0x{1:x} completed".format(min_id, max_id))

    def bruteforce_data(self, data, bruteforce_index, callback, min_value=BYTE_MIN, max_value=BYTE_MAX,
                        callback_end=None):
        """Bruteforces the value of one byte in the data payload, sending each mutated message and executing a callback.

        :param data: The data payload of the CAN message as a bytearray.
        :param bruteforce_index: The index of the byte within the data payload to bruteforce.
        :param callback: The function to call for each bruteforced value.
        :param min_value: The minimum value of the byte to start bruteforcing from.
        :param max_value: The maximum value of the byte to bruteforce up to.
        :param callback_end: Optional; The function to call when the bruteforce operation is completed.
        """
        self.bruteforce_running = True
        for value in range(min_value, max_value + 1):
            self.notifier.listeners = [callback(value)]
            data[bruteforce_index] = value
            self.send(data)
            time.sleep(MESSAGE_DELAY)
            if not self.bruteforce_running:
                self.notifier.listeners = []
                return
        if callback_end:
            self.notifier.listeners = []
            callback_end()

    def bruteforce_data_new(self, data, bruteforce_indices, callback,
                            min_value=BYTE_MIN, max_value=BYTE_MAX,
                            callback_done=None):
        """Bruteforces multiple data bytes within a CAN message payload, sending modified messages and executing callbacks.

        :param data: The data payload of the CAN message as a bytearray.
        :param bruteforce_indices: A list of byte indices within the data payload to bruteforce.
        :param callback: The function to call for each unique data mutation.
        :param min_value: The minimum value for each bruteforced byte.
        :param max_value: The maximum value for each bruteforced byte.
        :param callback_done: Optional; The function to call when the bruteforce operation completes.
        """
        def send(msg_data, idxs):
            self.notifier.listeners = [callback(["{0:02x}".format(msg_data[a]) for a in idxs])]
            self.send(msg_data)
            self.current_delay = 0.2
            while self.current_delay > 0.0:
                time.sleep(DELAY_STEP)
                self.current_delay -= DELAY_STEP
            if not self.bruteforce_running:
                self.notifier.listeners = []
                return

        def bruteforce(idx):
            if idx >= len(bruteforce_indices):
                send(data, bruteforce_indices)
                return
            for i in range(min_value, max_value + 1):
                data[bruteforce_indices[idx]] = i
                bruteforce(idx + 1)

        # Make sure that the data array is correctly initialized for the bruteforce
        for idx_i in bruteforce_indices:
            data[idx_i] = 0
        bruteforce(0)
        if callback_done:
            callback_done("Scan finished")

    def send_single_message_with_callback(self, data, callback):
        """Sends a single CAN message and sets a listener for the response.

        :param data: The data payload of the CAN message as a bytearray.
        :param callback: The listener function to process the response to the sent message.
        """
        self.set_listener(callback)
        self.send(data)

    def bruteforce_stop(self):
        """Stops any ongoing bruteforce operation immediately."""
        self.bruteforce_running = False

