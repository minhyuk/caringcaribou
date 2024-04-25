from __future__ import print_function
from caringcaribou.utils.iso14229_1 import Constants, Iso14229_1, NegativeResponseCodes, ServiceID, Services
from caringcaribou.tests.mock.mock_ecu_uds import MockEcuIso14229
from caringcaribou.modules import uds
import unittest


class UdsModuleTestCase(unittest.TestCase):
    ARB_ID_REQUEST = 0x300E
    ARB_ID_RESPONSE = 0x300F

    # Timeout (in seconds) when waiting for response during bruteforce
    BRUTEFORCE_TIMEOUT = 0.01

    def setUp(self):
        """Initialize mock ECU and remove response delay before each test."""
        self.ecu = MockEcuIso14229(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE)
        self.ecu.DELAY_BEFORE_RESPONSE = 0.0
        self.ecu.start_server()

    def tearDown(self):
        """Clean up and exit mock ECU after each test."""
        if isinstance(self.ecu, MockEcuIso14229):
            self.ecu.__exit__(None, None, None)

    def test_uds_discovery(self):
        """Tests UDS discovery by scanning for ECU responses within a specified range."""
        start_arb_id = self.ARB_ID_REQUEST - 5
        end_arb_id = self.ARB_ID_REQUEST + 5
        blacklist = []
        auto_blacklist_duration = 0
        timeout = self.BRUTEFORCE_TIMEOUT
        verify = True
        print_results = False
        result = uds.uds_discovery(min_id=start_arb_id,
                                   max_id=end_arb_id,
                                   blacklist_args=blacklist,
                                   auto_blacklist_duration=auto_blacklist_duration,
                                   delay=timeout,
                                   verify=verify,
                                   print_results=print_results)
        expected_result = [(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE)]
        self.assertListEqual(result, expected_result, "UDS discovery gave '{0}', expected '{1}'".format(
            result, expected_result))

    def test_uds_discovery_blacklist(self):
        """Tests UDS discovery with specified arbitration ID in the blacklist."""
        start_arb_id = self.ARB_ID_REQUEST - 5
        end_arb_id = self.ARB_ID_REQUEST + 5
        blacklist = [self.ARB_ID_RESPONSE]
        auto_blacklist_duration = 0
        timeout = self.BRUTEFORCE_TIMEOUT
        verify = True
        print_results = False
        result = uds.uds_discovery(min_id=start_arb_id,
                                   max_id=end_arb_id,
                                   blacklist_args=blacklist,
                                   auto_blacklist_duration=auto_blacklist_duration,
                                   delay=timeout,
                                   verify=verify,
                                   print_results=print_results)
        expected_result = []
        self.assertListEqual(result, expected_result, "UDS discovery gave '{0}', expected '{1}'".format(
            result, expected_result))

    def test_service_discovery(self):
        """Finds supported UDS services within a specified service ID range."""
        range_start = 0x09
        range_end = 0x13
        print_results = False
        result = uds.service_discovery(arb_id_request=self.ARB_ID_REQUEST,
                                       arb_id_response=self.ARB_ID_RESPONSE,
                                       timeout=self.BRUTEFORCE_TIMEOUT,
                                       min_id=range_start,
                                       max_id=range_end,
                                       print_results=print_results)
        expected_result = [ServiceID.DIAGNOSTIC_SESSION_CONTROL, ServiceID.ECU_RESET]
        self.assertListEqual(result, expected_result, "UDS service discovery gave '{0}', expected '{1}'".format(
            result, expected_result))

    def test_service_discovery_empty_range(self):
        """Tests service discovery functionality with a range that should yield no services."""
        range_start = 0x00
        range_end = 0x05
        print_results = False
        result = uds.service_discovery(arb_id_request=self.ARB_ID_REQUEST,
                                       arb_id_response=self.ARB_ID_RESPONSE,
                                       timeout=self.BRUTEFORCE_TIMEOUT,
                                       min_id=range_start,
                                       max_id=range_end,
                                       print_results=print_results)
        expected_result = []
        self.assertListEqual(result, expected_result, "UDS service discovery gave '{0}', expected no hits".format(
            result))

    def test_ecu_reset_hard_reset_success(self):
        """Tests successful ECU hard reset."""
        reset_type = Services.EcuReset.ResetType.HARD_RESET
        timeout = None
        result = uds.ecu_reset(arb_id_request=self.ARB_ID_REQUEST,
                               arb_id_response=self.ARB_ID_RESPONSE,
                               reset_type=reset_type,
                               timeout=timeout)
        expected_response_id = Iso14229_1.get_service_response_id(Services.EcuReset.service_id)
        expected_result = [expected_response_id, reset_type]
        self.assertListEqual(result, expected_result, "ECU Reset gave '{0}', expected '{1}'".format(
            result, expected_result))

    def test_ecu_reset_unsupported_reset_type_failure(self):
        """Tests ECU reset with an unsupported reset type, expecting a negative response code."""
        reset_type = 0x00
        timeout = None
        result = uds.ecu_reset(arb_id_request=self.ARB_ID_REQUEST,
                               arb_id_response=self.ARB_ID_RESPONSE,
                               reset_type=reset_type,
                               timeout=timeout)
        expected_response_id = Services.EcuReset.service_id
        expected_nrc = NegativeResponseCodes.SUB_FUNCTION_NOT_SUPPORTED
        expected_result = [Constants.NR_SI, expected_response_id, expected_nrc]
        self.assertListEqual(result, expected_result, "ECU Reset gave '{0}', expected '{1}'".format(
            result, expected_result))

    def test_security_access_request_seed_send_key_success(self):
        """Requests a security access seed then sends the correct key for access, expecting success."""
        level_seed = 0x01
        data_record = []
        timeout = None
        expected_response_id = Iso14229_1.get_service_response_id(Services.SecurityAccess.service_id)
        seed_result = uds.request_seed(arb_id_request=self.ARB_ID_REQUEST,
                                       arb_id_response=self.ARB_ID_RESPONSE,
                                       level=level_seed,
                                       data_record=data_record,
                                       timeout=timeout)
        expected_seed = self.ecu.SECURITY_ACCESS_SEED
        expected_seed_result = [expected_response_id, level_seed] + expected_seed
        self.assertListEqual(seed_result,
                             expected_seed_result,
                             "Security Access: Request seed gave '{0}', expected '{1}'".format(
                                 seed_result, expected_seed_result))
        level_key = uds.Services.SecurityAccess.RequestSeedOrSendKey().get_send_key_for_request_seed(level_seed)
        key = self.ecu.SECURITY_ACCESS_KEY
        key_result = uds.send_key(arb_id_request=self.ARB_ID_REQUEST,
                                  arb_id_response=self.ARB_ID_RESPONSE,
                                  level=level_key,
                                  key=key,
                                  timeout=timeout)
        expected_key_result = [expected_response_id, level_key]
        self.assertListEqual(key_result,
                             expected_key_result,
                             "Security Access: Send key gave '{0}', expected '{1}'".format(
                                 key_result, expected_key_result))

    def test_security_access_request_seed_invalid_level(self):
        """Attempts to request a seed with an invalid security access level, expecting a ValueError."""
        level = 0x00
        data_record = []
        timeout = None
        with self.assertRaises(ValueError):
            uds.request_seed(arb_id_request=self.ARB_ID_REQUEST,
                             arb_id_response=self.ARB_ID_RESPONSE,
                             level=level,
                             data_record=data_record,
                             timeout=timeout)

    def test_dump_dids(self):
        """Scans for and dumps Data Identifiers (DIDs) from ECU within a specific range."""
        timeout = None
        min_did = 0x0000
        max_did = 0x0101
        print_results = False
        expected_response_cnt = 2
        expected_response = [0x62, 0x72]
        responses = uds.dump_dids(arb_id_request=self.ARB_ID_REQUEST,
                                  arb_id_response=self.ARB_ID_RESPONSE,
                                  timeout=timeout,
                                  min_did=min_did,
                                  max_did=max_did,
                                  print_results=print_results)

        self.assertEqual(expected_response_cnt, len(responses))

        for response in responses:
            self.assertListEqual(expected_response, response[1])
