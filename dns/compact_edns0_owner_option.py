import struct
from typing import NamedTuple


class CompactEDNS0OwnerOption(NamedTuple):
    """Implementation of EDNS0 'Owner' Option (compact format) as defined in proposal:

    https://www.ietf.org/archive/id/draft-cheshire-edns0-owner-option-01.txt"""

    opt: int = 4
    """The two-byte EDNS0 Option code 'Opt' for the 'Owner' option is 4."""

    len: int = 8
    """The two-byte length field 'Len' for this option is 24 in the full-length case, or less when using the 
    "compact" variants described below. """

    v: int = 0
    """The one-byte version field 'V' is currently zero.  In the current version of the protocol, senders MUST set 
    this field to zero on transmission, and receivers receiving an EDNS0 option 4 where the version field is not zero 
    MUST ignore the entire option. """

    s: int = 0
    """The one-byte sequence number field 'S' is set to zero the first time this option is used after boot, 
    and then after that incremented each time the machine awakens from sleep. """

    primary_mac: bytes = None
    """The six-byte Primary MAC field identifies the machine.  Typically, the MAC address of the machine's 'primary' 
    interface is used for this purpose. """

    def serialize(self):
        return struct.pack(f">HHBB6s", *self)
