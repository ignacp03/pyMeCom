"""
The package consists of 3 files.

commands.py contains a dictionary parameters which can be get/set
exceptions.py defines the error thrown by this pockage
mecom.py contains the communication logic
lookup_table.py has auxiliary functions for lookup table downloading.

"""

from .mecom import MeCom, VR, VS, TD, Parameter
from .exceptions import ResponseException, WrongChecksum
