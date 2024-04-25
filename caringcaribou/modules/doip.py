def tester_present(arb_id_request, arb_id_response, delay, duration):
    """
    Continuously sends TesterPresent messages to keep communication alive with the ECU.
    
    Args:
        arb_id_request: Arbitration ID for sending TesterPresent messages.
        arb_id_response: Expected arbitration ID for responses.
        delay: Time in seconds between TesterPresent messages.
        duration: Duration in seconds to continue sending TesterPresent messages. Set to None for indefinite duration.
    """
