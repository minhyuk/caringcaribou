def uds_discovery(min_id, max_id, blacklist_args, auto_blacklist_duration,
                  delay, verify, print_results=True):
    """
    Performs a UDS discovery procedure by sending diagnostic session control messages across a range of arbitration IDs.
    
    This function attempts to discover diagnostic services by methodically probing predefined arbitration ID ranges,
    identifying potential ECU responses, and optionally verifying discovered services to reduce false positives.
    
    Parameters:
    min_id (int): Start of the arbitration ID range to probe.
    max_id (int): End of the arbitration ID range to probe.
    blacklist_args (list[int]): A list of arbitration IDs to exclude from scanning.
    auto_blacklist_duration (float): Duration in seconds to identify and exclude noisy arbitration IDs automatically before scanning.
    delay (float): Delay in seconds between each probe message.
    verify (bool): Enable or disable verification of discovered services to confirm responsiveness.
    print_results (bool, optional): Enable or disable console output of the discovery process and results.
    
    Returns:
    list[tuple(int, int)]: A list of tuples, where each tuple contains a client arbitration ID and its corresponding server
    arbitration ID that responded to the diagnostic session control message.
    """
    ...

def __uds_discovery_wrapper(args):
    """
    A wrapper function for the UDS discovery process, intended to facilitate parameter passing from command-line arguments or other external interfaces.
    
    Parameters:
    args: A namespace or other object with attributes corresponding to the parameters required by `uds_discovery`.
    
    Returns:
    None
    """
    ...

def service_discovery(arb_id_request, arb_id_response, timeout,
                      min_id=BYTE_MIN, max_id=BYTE_MAX, print_results=True):
    """
    Identifies the supported UDS services by probing a specified arbitration ID pair with service ID requests.
    
    Sends diagnostic service requests ranging from `min_id` to `max_id` and observes the responses to determine which services
    are supported by the target ECUs arbitrated by `arb_id_request` and `arb_id_response`.
    
    Parameters:
    arb_id_request (int): The arbitration ID used for sending diagnostic requests.
    arb_id_response (int): The expected arbitration ID from which responses will be received.
    timeout (float): Timeout in seconds for waiting for a response before proceeding to the next service ID.
    min_id (int, optional): Starting service ID to probe.
    max_id (int, optional): Ending service ID to probe.
    print_results (bool, optional): Flag to enable or disable printing of probing results and progress to stdout.
    
    Returns:
    list[int]: A list of service IDs that are supported according to the probe results.
    """
    ...

def __service_discovery_wrapper(args):
    """
    A wrapper function for the service discovery process, designed to simplify invocation with parameters
    obtained from command-line arguments or other forms of external input.
    
    Parameters:
    args: A collection of arguments required by the `service_discovery` function, typically provided by parsing command-line input.
    
    Returns:
    None
    """
    ...

def sub_discovery(arb_id_request, arb_id_response, diagnostic, service, timeout, print_results=True):
    """
    Probes for supported UDS sub-services of a specified service by sending corresponding diagnostic requests.
    
    This function is mainly used to identify sub-functions or sub-commands supported under a main diagnostic service,
    aiding in a more thorough investigation of the capabilities of the target ECU.
    
    Parameters:
    arb_id_request (int): The arbitration ID for sending diagnostic requests.
    arb_id_response (int): The arbitration ID expected for receiving responses.
    diagnostic (int): Diagnostic session type to initiate before probing sub-services.
    service (int): The UDS service under which sub-services are to be discovered.
    timeout (float): Time to wait in seconds for a response before moving on to the next sub-service ID.
    print_results (bool, optional): Flag to control printing of discovery progress and results to stdout.
    
    Returns:
    list[int]: A list of discovered sub-service IDs supported by the targeted service.
    """
    ...

def __sub_discovery_wrapper(args):
    """
    Provides a simplified interface for initiating sub-service discovery operations,
    primarily for use with command-line-based parameter inputs.
    
    Bridges command-line arguments to the `sub_discovery` function, allowing for streamlined command-line tools development.
    
    Parameters:
    args: Object containing arguments necessary for sub-service discovery, generally derived from parsing command-line input.
    
    Returns:
    None
    """
    ...

def raw_send(arb_id_request, arb_id_response, service, session_type):
    """
    Sends a raw UDS request based on specified parameters and returns the response.
    
    This low-level function directly interfaces with diagnostic services, allowing for custom requests outside predefined service discovery mechanics.
    
    Parameters:
    arb_id_request (int): Arbitration ID to use for sending the request.
    arb_id_response (int): Expected arbitration ID for the response.
    service (int): The service ID of the UDS service being requested.
    session_type (int): Specific session or sub-service ID being requested under the main service.
    
    Returns:
    [int] or None: A list of byte values comprising the raw response, or None if no response was received within the configured timeout.
    """
    ...

def tester_present(arb_id_request, delay, duration, suppress_positive_response):
    """
    Periodically sends TesterPresent service requests to keep the diagnostic session active.
    
    This function can be used to prevent session timeouts during extended diagnostic activities. It supports both continuous and
    time-bounded execution modes, optionally suppressing positive response frames to minimize bus load.
    
    Parameters:
    arb_id_request (int): The arbitration ID used for sending TesterPresent requests.
    delay (float): The delay in seconds between consecutive TesterPresent messages.
    duration (float or None): The total duration in seconds to continue sending TesterPresent messages. If None, the function runs indefinitely.
    suppress_positive_response (bool): Indicates whether to request suppression of the positive response messages for each TesterPresent request.
    
    Returns:
    None
    """
    ...

def __tester_present_wrapper(args):
    """
    A command-line friendly wrapper for the `tester_present` function, enabling easy initiation of TesterPresent sessions based on user inputs.
    
    Parameters:
    args: Object containing arguments suitable for running the `tester_present` function, often derived from parsing command-line inputs.
    
    Returns:
    None
    """
    ...

def ecu_reset(arb_id_request, arb_id_response, reset_type, timeout):
    """
    Initiates an ECU Reset request and waits for the response, returning the ECU's answer to the reset command.
    
    This command allows for various types of resets, providing flexibility in managing ECU state transitions during diagnostic sessions.
    
    Parameters:
    arb_id_request (int): Arbitration ID for sending the reset request.
    arb_id_response (int): Expected arbitration ID for the reset response.
    reset_type (int): The specific type of reset to request, defined by UDS standards.
    timeout (float or None): Custom timeout in seconds to wait for a response, or None to use the default timeout.
    
    Returns:
    [int] or None: A list of byte values in the response, or None if no response was received within the specified or default timeout.
    """
    ...

def __ecu_reset_wrapper(args):
    """
    Acts as a convenient interface for triggering ECU reset operations from command-line tools, mapping user inputs to the `ecu_reset` function parameters.
    
    Parameters:
    args: Object containing necessary arguments for performing an ECU reset, typically populated from command-line inputs.
    
    Returns:
    None
    """
    ...

def print_negative_response(response):
    """
    Decodes and prints a human-readable description of a negative response received from a UDS service.
    
    This utility function aids in interpreting negative response codes (NRCs), providing insights into the reason a diagnostic request failed.
    
    Parameters:
    response ([int]): The raw response data bytes received from a UDS service indicating a negative response.
    
    Returns:
    None
    """
    ...

def __security_seed_wrapper(args):
    """
    Facilitates the acquisition of security access seeds for subsequent unlocking of UDS protected services via a simplified command-line interface.
    
    Designed to automate and simplify the collection of security seeds necessary for performing actions requiring elevated access privileges.
    
    Parameters:
    args: Arguments necessary for obtaining security seeds, such as target arbitration IDs and requested security access levels.
    
    Returns:
    None
    """
    ...

def extended_session(arb_id_request, arb_id_response, session_type):
    """
    Requests a change to an extended diagnostic session, facilitating access to a broader range of UDS services and sub-functions.
    
    Essential for performing certain diagnostic operations that require an active diagnostic session beyond the default session type.
    
    Parameters:
    arb_id_request (int): The arbitration ID for sending the session control request.
    arb_id_response (int): The expected arbitration ID for receiving session control responses.
    session_type (int): The diagnostic session type to initiate.
    
    Returns:
    [int] or None: The raw response to the session control request, indicating success or failure of the session change request.
    """
    ...

def request_seed(arb_id_request, arb_id_response, level, timeout):
    """
    Requests a security access seed required for certain protected diagnostic operations, typically the first step in a two-step security handshake.
    
    Parameters:
    arb_id_request (int): Arbitration ID for sending the security access request.
    arb_id_response (int): Expected arbitration ID for receiving the security access response.
    level (int): Security access level for which the seed is requested.
    timeout (float): Time in seconds to wait for a response before considering the request timed out.
    
    Returns:
    [int] or None: The security access seed provided by the ECU in response to the request, or None if no response was received.
    """
    ...
