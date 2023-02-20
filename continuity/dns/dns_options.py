from zeroconf import DNSRecord


class DNSOptions(DNSRecord):

    """A DNS OPT record"""

    __slots__ = ('_hash', 'text')

    def __init__(self, class_: int, ttl: int, text: bytes, created=None):
        assert isinstance(text, (bytes, type(None)))
        self.type = 41  # OPT type ID
        self.text = text

        super().__init__("", self.type, class_, ttl, created)

        self._hash = hash((self.key, self.type, self.class_, text))

    def write(self, out: 'DNSOutgoing') -> None:
        """Used in constructing an outgoing packet"""
        out.write_string(self.text)

    def __hash__(self) -> int:
        """Hash to compare like DNSOptions."""
        return self._hash

    def __eq__(self, other) -> bool:
        """Tests equality on text."""
        return isinstance(other, DNSOptions) and self._eq(other)

    def _eq(self, other) -> bool:  # type: ignore[no-untyped-def]
        """Tests equality on text."""
        return self.text == other.text and self._dns_entry_matches(other)

    def __repr__(self) -> str:
        """String representation"""
        if len(self.text) > 10:
            return self.to_string(self.text[:7]) + "..."
        return self.to_string(self.text)
