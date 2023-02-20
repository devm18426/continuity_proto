from zeroconf import DNSOutgoing


class MyDNSOutgoing(DNSOutgoing):
    """Allow zero-length names"""

    def write_name(self, name: str) -> None:
        if len(name) == 0:
            self.data.append(len(name).to_bytes(1, 'big'))
            self.size += 1
        else:
            super().write_name(name)
