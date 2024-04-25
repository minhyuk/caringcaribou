from caringcaribou.utils.can_actions import DEFAULT_INTERFACE
from caringcaribou.utils.constants import ARBITRATION_ID_MAX_EXTENDED, ARBITRATION_ID_MAX
import can
import datetime
import time


class IsoTp:
    """
    Implementation of ISO-15765-2, also known as ISO-TP. This is a multi-frame messaging protocol
    over CAN, which allows message payloads of up to 4095 bytes.
    """

    MAX_SF_LENGTH = 7
    MAX_FF_LENGTH = 6
    MAX_CF_LENGTH = 7

    SF_PCI_LENGTH = 1
    CF_PCI_LENGTH = 1
    FF_PCI_LENGTH = 2
    FC_PCI_LENGTH = 3

    FC_FS_CTS = 0
    FC_FS_WAIT = 1
    FC_FS_OVFLW = 2

    SF_FRAME_ID = 0
    FF_FRAME_ID = 1
    CF_FRAME_ID = 2
    FC_FRAME_ID = 3

    N_BS_TIMEOUT = 1.5

    MAX_FRAME_LENGTH = 8
    MAX_MESSAGE_LENGTH = 4095

    def __init__(self, arb_id_request, arb_id_response, bus=None, padding_value=0x00):
        """
        Initializes the IsoTp object with arbitration IDs for request and response, an optional CAN bus object,
        and an optional padding value for message frames.

        :param arb_id_request: Arbitration ID for request messages.
        :param arb_id_response: Arbitration ID for response messages.
        :param bus: (Optional) CAN bus object to use for message transmission and reception.
        :param padding_value: (Optional) Value used to pad send frames. Defaults to 0x00.
        """
        if bus is None:
            self.bus = can.Bus(context=DEFAULT_INTERFACE)
        else:
            self.bus = bus
        self.arb_id_request = arb_id_request
        self.arb_id_response = arb_id_response
        self.padding_value = padding_value
        if padding_value is None:
            self.padding_enabled = False
        else:
            self.padding_enabled = True
            if not isinstance(padding_value, int):
                raise TypeError("IsoTp: padding must be an integer or None, received '{0}'".format(padding_value))
            if not 0x00 <= padding_value <= 0xFF:
                raise ValueError("IsoTp: padding must be in range 0x00-0xFF (0-255), got '{0}'".format(padding_value))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bus.shutdown()

    def _set_filters(self, filters):
        """
        Sets filters for the CAN bus to specify which messages should be received based on arbitration IDs.

        :param filters: A list of dictionaries, each containing a 'can_id' and 'can_mask', with an optional
                        'extended' flag to indicate filtering for extended arbitration IDs.
        """
        self.bus.set_filters(filters)

    def set_filter_single_arbitration_id(self, arbitration_id):
        """
        Applies a single filter for the CAN bus to allow receiving messages that match the specified arbitration ID.

        :param arbitration_id: The arbitration ID for which messages should be received.
        """
        arbitration_id_filter = [{"can_id": arbitration_id, "can_mask": ARBITRATION_ID_MAX_EXTENDED}]
        self._set_filters(arbitration_id_filter)

    def clear_filters(self):
        """
        Clears all previously set filters on the CAN bus.
        """
        self._set_filters(None)

    def send_message(self, data, arbitration_id, force_extended=False):
        """
        Sends a CAN message with specified data, arbitration ID, and optionally forces extended arbitration ID format.

        :param data: The data bytes of the CAN message to be sent.
        :param arbitration_id: The arbitration ID to use for the message.
        :param force_extended: If True, the arbitration ID is treated as an extended ID.
        """
        is_extended = force_extended or arbitration_id > ARBITRATION_ID_MAX
        msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=is_extended)
        self.bus.send(msg)

    def decode_sf(self, frame):
        """
        Decodes a single frame (SF) to obtain its data and length.

        :param frame: The bytes of the SF frame to decode.
        :return: A tuple of single frame data length (SF_DL) and the data payload if valid, None otherwise.
        """
        if len(frame) >= self.SF_PCI_LENGTH:
            sf_dl = frame[0] & 0xF
            data = frame[1:]
            return sf_dl, list(data)
        else:
            return None, None

    def decode_ff(self, frame):
        """
        Decodes a first frame (FF) to obtain its length and starting data portion.

        :param frame: The bytes of the FF frame to decode.
        :return: A tuple of first frame data length (FF_DL) and the initial data payload if valid, None otherwise.
        """
        if len(frame) >= self.FF_PCI_LENGTH:
            ff_dl = ((frame[0] & 0xF) << 8) | frame[1]
            data = frame[2:]
            return ff_dl, list(data)
        else:
            return None, None

    def decode_cf(self, frame):
        """
        Decodes a consecutive frame (CF) to obtain the next sequence of data.

        :param frame: The bytes of the CF frame to decode.
        :return: A tuple of sequence number (SN) and the data payload if valid, None otherwise.
        """
        if len(frame) >= self.CF_PCI_LENGTH:
            sn = frame[0] & 0xF
            data = frame[1:]
            return sn, list(data)
        else:
            return None, None

    def decode_fc(self, frame):
        """
        Decodes a flow control (FC) frame to obtain flow status, block size, and minimum separation time.

        :param frame: The bytes of the FC frame to decode.
        :return: A tuple of flow status (FS), block size (BS), and minimum separation time (STmin) if valid,
                 None otherwise.
        """
        if len(frame) >= self.FC_PCI_LENGTH:
            fs = frame[0] & 0xF
            block_size = frame[1]
            st_min = frame[2]
            return fs, block_size, st_min
        else:
            return None, None, None

    def encode_fc(self, flow_status, block_size, st_min):
        """
        Encodes a flow control (FC) message with the specified parameters.

        :param flow_status: The flow status to set in the FC message.
        :param block_size: The block size to set, indicating how many frames may be sent before waiting for another FC.
        :param st_min: The minimum separation time between frames.
        :return: A list of bytes representing the encoded FC message.
        """
        return [(self.FC_FRAME_ID << 4) | flow_status, block_size, st_min, 0, 0, 0, 0, 0]

    def send_request(self, message):
        """
        Sends a message as a request, processing it into frames as necessary according to ISO-TP.

        :param message: The message data to be sent as a request.
        """
        frames = self.get_frames_from_message(message, padding_value=self.padding_value)
        self.transmit(frames, self.arb_id_request, self.arb_id_response)

    def send_response(self, message):
        """
        Sends a message as a response, processing it into frames as necessary according to ISO-TP.

        :param message: The message data to be sent as a response.
        """
        frames = self.get_frames_from_message(message, padding_value=self.padding_value)
        self.transmit(frames, self.arb_id_response, self.arb_id_request)

    def indication(self, wait_window=None, trim_padding=True, first_frame_only=False):
        """
        Receives a multi-frame ISO-TP message, processing each frame to reconstruct the full message data.

        :param wait_window: Maximum time in seconds to wait for all frames before giving up.
        :param trim_padding: If True, padding bytes are removed from the message data.
        :param first_frame_only: If True, simulates an overflow condition by only retrieving the first frame.
        :return: A list of bytes representing the received message data, or None if a timeout occurs.
        """
        message = []

        if wait_window is None:
            wait_window = self.N_BS_TIMEOUT
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(seconds=wait_window)
        sn = 0
        message_length = 0

        while True:
            # Timeout check
            current_time = datetime.datetime.now()
            if current_time >= end_time:
                # Timeout
                return None
            # Receive frame
            msg = self.bus.recv(wait_window)
            if msg is not None:
                if msg.arbitration_id == self.arb_id_request:
                    flow_control_arbitration_id = self.arb_id_response
                elif msg.arbitration_id == self.arb_id_response:
                    flow_control_arbitration_id = self.arb_id_request
                else:
                    # Unknown arbitration ID - ignore message
                    continue
                frame = msg.data
                if len(frame) > 0:
                    frame_type = (frame[0] >> 4) & 0xF
                    if frame_type == self.SF_FRAME_ID:
                        # Single frame (SF)
                        dl, message = self.decode_sf(frame)
                        if trim_padding:
                            # Trim padding, in case the data exceeds single frame data length (SF_DL)
                            message = message[:dl]
                        break
                    elif frame_type == self.FF_FRAME_ID:
                        # First frame (FF) of a multi-frame message
                        message_length, message = self.decode_ff(frame)
                        if first_frame_only:
                            # This is a hack to make it possible to only retrieve the first frame of a multi-frame
                            # response, by telling the sender to stop sending data due to overflow
                            ovflw_frame = self.encode_fc(self.FC_FS_OVFLW, 0, 0)
                            # Respond with overflow (OVFLW) message
                            self.send_message(ovflw_frame, flow_control_arbitration_id)
                            # Return the first frame only
                            break
                        fc_frame = self.encode_fc(self.FC_FS_CTS, 0, 0)
                        sn = 0
                        # Respond with flow control (FC) message
                        self.send_message(fc_frame, flow_control_arbitration_id)
                    elif frame_type == self.CF_FRAME_ID:
                        # Consecutive frame (CF)
                        new_sn, data = self.decode_cf(frame)
                        if (sn + 1) % 16 == new_sn:
                            sn = new_sn
                            message += data
                            if len(message) >= message_length:
                                # Last frame received
                                if trim_padding:
                                    # Trim padding of last frame, which may exceed first frame data length (FF_DL)
                                    message = message[:message_length]
                                # Stop listening for more frames
                                break
                            else:
                                pass
                    else:
                        # Invalid frame type
                        return None
        return list(message)

    def transmit(self, frames, arbitration_id, arbitration_id_flow_control):
        """
        Transmits a sequence of frames as a single ISO-TP message, handling flow control for multi-frame messages.

        :param frames: A list of frames to transmit as part of the message.
        :param arbitration_id: The arbitration ID to use for transmitting the frames.
        :param arbitration_id_flow_control: The arbitration ID expected for receiving flow control frames.
        """
        if len(frames) == 0:
            # No data to send
            return None
        elif len(frames) == 1:
            # Single frame
            self.send_message(frames[0], arbitration_id)
        elif len(frames) > 1:
            # Multiple frames
            frame_index = 0
            # Send first frame (FF)
            self.send_message(frames[frame_index], arbitration_id)
            number_of_frames_left_to_send = len(frames) - 1
            number_of_frames_left_to_send_in_block = 0
            frame_index += 1
            st_min = 0
            while number_of_frames_left_to_send > 0:
                receiver_is_ready = False
                while not receiver_is_ready:
                    # Wait for receiver to send flow control (FC)
                    msg = self.bus.recv(self.N_BS_TIMEOUT)
                    if msg is None:
                        # Quit on timeout
                        return None
                    # Verify that msg uses the expected arbitration ID
                    elif msg.arbitration_id != arbitration_id_flow_control:
                        continue
                    fc_frame = msg.data

                    # Decode Flow Status (FS) from FC message
                    fs, block_size, st_min = self.decode_fc(fc_frame)
                    if fs == self.FC_FS_WAIT:
                        # Flow status (FS) wait (WT)
                        continue
                    elif fs == self.FC_FS_CTS:
                        # Continue to send (CTS)
                        receiver_is_ready = True
                        number_of_frames_left_to_send_in_block = block_size

                        if number_of_frames_left_to_send < number_of_frames_left_to_send_in_block or block_size == 0:
                            number_of_frames_left_to_send_in_block = number_of_frames_left_to_send
                        # If STmin is specified in microseconds (0xF1-0xF9) or using reserved ranges (0x80-0xF0 and
                        # 0xFA-0xFF), round up to one millisecond
                        if st_min > 0x7F:
                            st_min = 1
                    elif fs == self.FC_FS_OVFLW:
                        # Overflow - abort transmission
                        return None
                    else:
                        # Timeout - did not receive a CTS message in time
                        return None
                while number_of_frames_left_to_send_in_block > 0:
                    # Send more frames, until it is time to wait for flow control (FC) again
                    self.send_message(frames[frame_index], arbitration_id)
                    frame_index += 1
                    number_of_frames_left_to_send_in_block -= 1
                    number_of_frames_left_to_send -= 1
                    if number_of_frames_left_to_send_in_block > 0:
                        time.sleep(st_min / 1000)

    @staticmethod
    def get_frames_from_message(message, padding_value=0x00):
        """
        Splits a given message into frames suitable for transmission over CAN using the ISO-TP protocol.

        :param message: The message data to be split into frames.
        :param padding_value: The byte value to use for padding frames, if padding is enabled.
        :return: A list of frames, each a list of bytes ready for transmission.
        """
        if padding_value is None:
            padding_enabled = False
            padding_value = 0x00
        else:
            padding_enabled = True

        frame_list = []
        message_length = len(message)
        if message_length > IsoTp.MAX_MESSAGE_LENGTH:
            error_msg = "Message too long for ISO-TP. Max allowed length is {0} bytes, received {1} bytes".format(
                IsoTp.MAX_MESSAGE_LENGTH, message_length)
            raise ValueError(error_msg)
        if message_length <= IsoTp.MAX_SF_LENGTH:
            # Single frame (SF) message
            if padding_enabled:
                frame = [padding_value] * IsoTp.MAX_FRAME_LENGTH
            else:
                frame = [padding_value] * (message_length + 1)
            frame[0] = (IsoTp.SF_FRAME_ID << 4) | message_length
            for i in range(0, message_length):
                frame[1 + i] = message[i]
            frame_list.append(frame)
        else:
            # Multiple frame message
            bytes_left_to_copy = message_length
            # Create first frame (FF)
            frame = [padding_value] * IsoTp.MAX_FRAME_LENGTH
            frame[0] = (IsoTp.FF_FRAME_ID << 4) | (message_length >> 8)
            frame[1] = message_length & 0xFF
            for i in range(0, IsoTp.MAX_FF_LENGTH):
                frame[2 + i] = message[i]
            frame_list.append(frame)
            # Create consecutive frames (CF)
            bytes_copied = IsoTp.MAX_FF_LENGTH
            bytes_left_to_copy -= bytes_copied
            sn = 0
            while bytes_left_to_copy > 0:
                sn = (sn + 1) % 16
                if not padding_enabled and bytes_left_to_copy < 7:
                    # Skip padding on last CF
                    frame = [padding_value] * (bytes_left_to_copy + 1)
                else:
                    frame = [padding_value] * IsoTp.MAX_FRAME_LENGTH
                frame[0] = (IsoTp.CF_FRAME_ID << 4) | sn
                # Fill current CF
                bytes_to_copy_to_current_cf = min(IsoTp.MAX_CF_LENGTH, bytes_left_to_copy)
                for i in range(bytes_to_copy_to_current_cf):
                    frame[1 + i] = message[bytes_copied]
                    bytes_left_to_copy = bytes_left_to_copy - 1
                    bytes_copied = bytes_copied + 1
                frame_list.append(frame)
        return frame_list
