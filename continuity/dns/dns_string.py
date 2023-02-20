class DNSString:
    def __init__(self, string: str | list[str] = None):
        if isinstance(string, list):
            self._strings = string
        elif isinstance(string, str):
            self._strings = [string]

    @staticmethod
    def _format(string: str) -> bytes:
        return len(string).to_bytes(1, "big") + string.encode()

    def __bytes__(self):
        return b"".join((self._format(string) for string in self._strings))

    def __add__(self, other):
        created = DNSString(self._strings)
        created += other
        return created

    def __iadd__(self, other):
        if isinstance(other, str):
            self._strings.append(other)

        if isinstance(other, DNSString):
            self._strings += other._strings

        return self
