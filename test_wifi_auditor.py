import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile
import time

# Add current directory to path to import wifi_auditor
sys.path.append(os.getcwd())
import wifi_auditor

class TestWiFiAuditor(unittest.TestCase):
    def setUp(self):
        self.auditor = wifi_auditor.WiFiAuditor()

    @patch('subprocess.run')
    def test_get_interfaces(self, mock_run):
        # Mock successful iwconfig output
        mock_run.return_value.stdout = """
lo        no wireless extensions.

wlan0     IEEE 802.11  ESSID:off/any
          Mode:Managed  Access Point: Not-Associated   Tx-Power=15 dBm
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Encryption key:off
          Power Management:off

eth0      no wireless extensions.
"""
        interfaces = self.auditor.get_interfaces()
        self.assertIn('wlan0', interfaces)
        self.assertNotIn('lo', interfaces)
        self.assertNotIn('eth0', interfaces)

    def test_validate_interface(self):
        self.assertTrue(self.auditor.validate_interface('wlan0'))
        self.assertTrue(self.auditor.validate_interface('wlan0mon'))
        self.assertTrue(self.auditor.validate_interface('mon-wlan0'))
        self.assertFalse(self.auditor.validate_interface('wlan0; rm -rf /'))
        self.assertFalse(self.auditor.validate_interface('wlan0 && whoami'))
        self.assertFalse(self.auditor.validate_interface(''))

    @patch('subprocess.run')
    def test_enable_monitor_mode(self, mock_run):
        # Mock check kill
        # 1. check kill
        # 2. start -> returns output with "monitor mode enabled on 'wlan0mon'"
        # 3. verify wlan0mon -> Mode:Monitor

        mock_run.side_effect = [
            MagicMock(stdout="", stderr=""), # check kill
            MagicMock(stdout="monitor mode enabled on 'wlan0mon'", stderr=""), # start
            MagicMock(stdout="Mode:Monitor", stderr="") # verify
        ]

        mon_interface = self.auditor.enable_monitor_mode('wlan0')
        self.assertEqual(mon_interface, 'wlan0mon')

    @patch('subprocess.run')
    def test_enable_monitor_mode_fallback(self, mock_run):
        # Test fallback when regex fails but naming convention holds

        mock_run.side_effect = [
            MagicMock(stdout="", stderr=""), # check kill
            MagicMock(stdout="Some unknown output", stderr=""), # start
            # verify regex result (skipped because regex fails)
            # verify original interface
            MagicMock(stdout="Mode:Managed", stderr=""),
            # verify interface + mon
            MagicMock(stdout="Mode:Monitor", stderr="")
        ]

        mon_interface = self.auditor.enable_monitor_mode('wlan0')
        self.assertEqual(mon_interface, 'wlan0mon')

    def test_parse_airodump_csv(self):
        # Create a dummy CSV file
        csv_content = """
BSSID, First time seen, Last time seen, channel, Speed, Privacy, Cipher, Authentication, Power, # beacons, # IV, LAN IP, ID-length, ESSID, Key
XX:XX:XX:XX:XX:XX, 2023-10-27 10:00:00, 2023-10-27 10:00:05, 6, 54, WPA2, CCMP, PSK, -50, 10, 0, 0.0.0.0, 9, TestNet,
Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = tmp.name

        try:
            networks = self.auditor.parse_airodump_csv(tmp_path)
            self.assertEqual(len(networks), 1)
            self.assertEqual(networks[0]['essid'], 'TestNet')
            self.assertEqual(networks[0]['bssid'], 'XX:XX:XX:XX:XX:XX')
            self.assertEqual(networks[0]['channel'], '6')
        finally:
            os.remove(tmp_path)

if __name__ == '__main__':
    unittest.main()
