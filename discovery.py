import codecs
import socket
from ipaddress import ip_address
from platform import node

import psutil
from zeroconf import Zeroconf, ServiceInfo, const, DNSText, current_time_millis, \
    DNSAddress, DNSNsec

from continuity.dns.compact_edns0_owner_option import CompactEDNS0OwnerOption
from continuity.dns.dns_options import DNSOptions
from continuity.dns.dns_string import DNSString
from continuity.dns.outgoing import MyDNSOutgoing
from continuity.discovery_test_data import rpAD, rpHN, rpBA


# https://stackoverflow.com/a/28950776/1124853
def get_primary_net_info():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(("10.254.254.254", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()

    primary_addresses = None
    for interface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.address == ip:
                primary_addresses = snics

    for address in primary_addresses:
        if address.family == psutil.AF_LINK:
            print(address.address)
            return ip_address(ip), codecs.decode(address.address.replace("-", ""), "hex")

    return ip, None


if __name__ == "__main__":
    zeroconf = Zeroconf()

    # https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/NetServices/Articles/NetServicesArchitecture.html
    hostname = node()
    service_name = "_companion-link"
    domain = "local"
    fqdn = f"{hostname}.{service_name}.{const._TCP_PROTOCOL_LOCAL_TRAILER}"

    ip, mac = get_primary_net_info()

    ttl = 4500
    port = 58645  # TCP LISTEN rapportd
    info = ServiceInfo(f"{service_name}.{const._TCP_PROTOCOL_LOCAL_TRAILER}", fqdn, other_ttl=ttl, port=port)

    out = MyDNSOutgoing(const._FLAGS_QR_RESPONSE | const._FLAGS_AA)
    now = current_time_millis()

    pointer_record = info.dns_pointer(created=now)

    model = "model=MacBookPro11,1"
    osxvers = "osxvers=20"

    text_record = DNSText(
        fqdn,
        const._TYPE_TXT,
        const._CLASS_IN,
        ttl,
        text=bytes(DNSString([model, osxvers])),
        created=now,
    )

    out.add_answer_at_time(text_record, 0)
    out.add_answer_at_time(pointer_record, 0)

    # https://www.usenix.org/system/files/sec21fall-stute.pdf
    # We found that the values rpBA and rpAD are used to identify
    # if both devices are linked to the same iCloud account and
    # filter out potentially other devices that might respond via the
    # open AWDL interface. In particular, we found that rpBA (encoded as a MAC address string) is chosen at random and
    # changes at least every 17 minutes. rpAD is an authentication
    # tag generated from the random rpBA and the device’s Bluetooth Identity Resolving Key (IRK) (used to resolve random
    # BLE addresses [15]) as arguments for a SipHash function [10].
    # Since the IRKs are synced via the iCloud keychain, devices
    # logged into the same iCloud account can try all available IRK
    # in the keychain to find other devices.
    rapport_text_record = DNSText(
        fqdn,
        const._TYPE_TXT,
        const._CLASS_IN,
        ttl,
        text=bytes(
            DNSString(f"rpBA={rpBA}") +
            f"rpAD={rpAD}" +
            "rpFl=0x20000" +
            f"rpHN={rpHN}" +
            "rpMac=0" +
            "rpVr=230.1"
        ),
        created=now,
    )

    service_record = info.dns_service(created=now)

    address_record = DNSAddress(f"{hostname}.{domain}", const._TYPE_A, const._CLASS_IN, ttl, ip.packed)

    service_nsec_record = DNSNsec(fqdn, const._TYPE_NSEC, const._CLASS_IN, ttl, fqdn,
                                  rdtypes=[const._TYPE_TXT, const._TYPE_SRV], created=now)
    host_nsec_record = DNSNsec(f"{hostname}.{domain}", const._TYPE_NSEC, const._CLASS_IN, 120, fqdn,
                               rdtypes=[const._TYPE_A], created=now)

    owner_option = CompactEDNS0OwnerOption(primary_mac=mac)
    options_record = DNSOptions(const._CLASS_IN, ttl, owner_option.serialize(), now)

    out.add_additional_answer(rapport_text_record)
    out.add_additional_answer(service_record)
    out.add_additional_answer(address_record)
    out.add_additional_answer(service_nsec_record)
    out.add_additional_answer(host_nsec_record)
    out.add_additional_answer(options_record)

    zeroconf.async_send(out)
