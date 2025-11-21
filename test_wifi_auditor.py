import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import wifi_auditor


class TestValidateInterface(unittest.TestCase):
    def test_valid_names(self):
        self.assertTrue(wifi_auditor.validate_interface("wlan0"))
        self.assertTrue(wifi_auditor.validate_interface("wlan0mon"))
        self.assertTrue(wifi_auditor.validate_interface("mon-wlan0"))

    def test_injection_rejected(self):
        self.assertFalse(wifi_auditor.validate_interface("wlan0; rm -rf /"))
        self.assertFalse(wifi_auditor.validate_interface("wlan0 && whoami"))
        self.assertFalse(wifi_auditor.validate_interface(""))
        self.assertFalse(wifi_auditor.validate_interface("../etc/passwd"))


class TestDetectWPS(unittest.TestCase):
    def test_wps_present(self):
        line = "AA:BB:CC:DD:EE:FF  -50  6  WPA2  WPS  HomeNet"
        self.assertTrue(wifi_auditor._detect_wps(line))

    def test_no_wps(self):
        line = "AA:BB:CC:DD:EE:FF  -50  6  WPA2   —   HomeNet"
        self.assertFalse(wifi_auditor._detect_wps(line))


class TestParseAirodumpCSV(unittest.TestCase):
    def test_parses_single_network(self):
        csv_content = (
            "BSSID, First time seen, Last time seen, channel, Speed, "
            "Privacy, Cipher, Authentication, Power, # beacons, # IV, "
            "LAN IP, ID-length, ESSID, Key\n"
            "AA:BB:CC:DD:EE:FF, 2024-01-01 10:00:00, 2024-01-01 10:00:05, "
            "6, 54, WPA2, CCMP, PSK, -41, 10, 0, 0.0.0.0, 8, TestNet,\n"
            "\n"
            "Station MAC, First time seen, Last time seen, Power, "
            "# packets, BSSID, Probed ESSIDs\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            tmp = f.name
        try:
            networks = wifi_auditor.parse_airodump_csv(tmp)
            self.assertEqual(len(networks), 1)
            self.assertEqual(networks[0]["essid"], "TestNet")
            self.assertEqual(networks[0]["bssid"], "AA:BB:CC:DD:EE:FF")
            self.assertEqual(networks[0]["channel"], "6")
            self.assertEqual(networks[0]["power"], -41)
        finally:
            os.remove(tmp)

    def test_signal_sort(self):
        """Stronger signal (less negative dBm) should appear first."""
        csv_content = (
            "BSSID, First time seen, Last time seen, channel, Speed, "
            "Privacy, Cipher, Authentication, Power, # beacons, # IV, "
            "LAN IP, ID-length, ESSID, Key\n"
            "AA:BB:CC:DD:EE:01, 2024-01-01 10:00:00, 2024-01-01 10:00:05, "
            "6, 54, WPA2, CCMP, PSK, -80, 10, 0, 0.0.0.0, 4, Weak,\n"
            "AA:BB:CC:DD:EE:02, 2024-01-01 10:00:00, 2024-01-01 10:00:05, "
            "11, 54, WPA2, CCMP, PSK, -40, 10, 0, 0.0.0.0, 6, Strong,\n"
            "\n"
            "Station MAC, First time seen, Last time seen, Power, "
            "# packets, BSSID, Probed ESSIDs\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            tmp = f.name
        try:
            networks = wifi_auditor.parse_airodump_csv(tmp)
            networks.sort(key=lambda n: n["power"], reverse=True)
            self.assertEqual(networks[0]["essid"], "Strong")
        finally:
            os.remove(tmp)


if __name__ == "__main__":
    unittest.main()
