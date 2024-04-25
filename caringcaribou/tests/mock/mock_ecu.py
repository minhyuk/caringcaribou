from __future__ import print_function
from caringcaribou.utils.can_actions import DEFAULT_INTERFACE
import can


class MockEcu:
    """Mock ECU base class, used for running tests over a virtual CAN bus"""

    DELAY_BEFORE_RESPONSE = 0.01

    def __init__(self, bus=None):
        """Initializes the MockEcu object with a CAN bus interface.
        
        If no bus is specified, it defaults to using the DEFAULT_INTERFACE.
        """
        self.message_process = None
        if bus is None:
            self.bus = can.Bus(context=DEFAULT_INTERFACE)
        else:
            self.bus = bus

    def __enter__(self):
        """Enables the MockEcu object to be used as a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensures proper shutdown of the CAN bus when exiting the context."""
        self.bus.shutdown()

