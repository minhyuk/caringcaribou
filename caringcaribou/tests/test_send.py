from caringcaribou.modules import send
import unittest


class SendFileParserTestCase(unittest.TestCase):

    RESULT_DATA_C0FFEE = [0xc0, 0xff, 0xee]
    RESULT_DATA_DEAD_CAFE = [0xde, 0xad, 0xca, 0xfe]

    def test_parse_candump_line(self):
        """
        Tests parsing of a single candump line format and verifies if the data extracted matches 
        the expected hexadecimal message data.
        """
        line = "(1499197954.029156) can0 123#c0ffee"
        message, timestamp = send.parse_candump_line(line, None, None)
        self.assertListEqual(message.data, self.RESULT_DATA_C0FFEE)

    def test_parse_pythoncan_line_v_20(self):
        """
        Tests parsing of a Python-CAN 2.0 formatted line and checks if the data extracted
        matches the expected hexadecimal message data.
        """
        line = "Timestamp:        0.000000        ID: 017a    000    DLC: 3    c0 ff ee"
        message, timestamp = send.parse_pythoncan_line(line, None, None)
        self.assertListEqual(message.data, self.RESULT_DATA_C0FFEE)

    def test_parse_pythoncan_line_v_21(self):
        """
        Tests parsing of a Python-CAN 2.1 formatted line (without flags) and validates the
        extracted data against the expected hexadecimal message.
        """
        line = "Timestamp:        0.000000        ID: 0000    S          DLC: 3    c0 ff ee"
        message, timestamp = send.parse_pythoncan_line(line, None, None)
        self.assertListEqual(message.data, self.RESULT_DATA_C0FFEE)

    def test_parse_pythoncan_line_v_21_flags(self):
        """
        Tests parsing of a Python-CAN 2.1 formatted line with flags included and checks if the
        extracted message data matches the expected DEAD_CAFE hexadecimal data.
        """
        line = "Timestamp:        0.000000    ID: 00000000    X E R      DLC: 4    de ad ca fe"
        message, timestamp = send.parse_pythoncan_line(line, None, None)
        self.assertListEqual(message.data, self.RESULT_DATA_DEAD_CAFE)

    def test_parse_pythoncan_line_v_30_channel(self):
        """
        Tests the parsing functionality for the Python-CAN 3.0 formatted line that includes
        channel information and verifies if it accurately extracts C0FFEE hexadecimal data.
        """
        line = "Timestamp:        0.000000    ID: 00000000    X                DLC:  3    c0 ff ee " \
               "                   Channel: vcan0"
        message, timestamp = send.parse_pythoncan_line(line, None, None)
        self.assertListEqual(message.data, self.RESULT_DATA_C0FFEE)

    def test_parse_pythoncan_line_v_30_flags(self):
        """
        Tests the Python-CAN 3.0 formatted line parsing with flags and checks if the DEAD_CAFE
        hexadecimal data is accurately extracted from the message.
        """
        line = "Timestamp:        0.000000    ID: 00000000    X   R            DLC:  4    de ad ca fe"
        message, timestamp = send.parse_pythoncan_line(line, None, None)
        self.assertListEqual(message.data, self.RESULT_DATA_DEAD_CAFE)

