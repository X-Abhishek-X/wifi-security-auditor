# wifi-security-auditor

WPA/WPA2 audit tool for authorised penetration testing. Wraps `aircrack-ng` and `hcxdumptool` with cleaner output — OUI vendor resolution, WPS detection, signal-sorted scan results, and PMKID capture without requiring a connected client.

**Only use on networks you own or have explicit written permission to test.**

---

### What it does differently

Standard `airodump-ng` gives you raw BSSID/channel/signal output. This wraps that with:

- **Vendor resolution** — each BSSID is resolved to its manufacturer via the macvendors.com API, cached locally so you're not hammering the API on every scan
- **WPS detection** — APs with WPS enabled are flagged in red; these are potential Pixie Dust targets
- **Signal sorting** — strongest AP first, so your list isn't random
- **PMKID mode** — captures the modern PMKID hash from the AP's beacon frame, no client deauth needed

---

### Requirements

```bash
# Core
sudo apt install aircrack-ng python3-pip
pip install -r requirements.txt

# PMKID mode only
sudo apt install hcxdumptool hcxtools
```

---

### Usage

```bash
# Scan only — no capture, just a clean sorted list
sudo python wifi_auditor.py --list

# Full audit: scan → pick target → capture 4-way handshake → crack
sudo python wifi_auditor.py -i wlan0 -w /usr/share/wordlists/rockyou.txt

# PMKID capture (no deauth, no connected client needed)
sudo python wifi_auditor.py -i wlan0 --pmkid

# Longer scan window, skip vendor API calls
sudo python wifi_auditor.py --scan-time 30 --no-vendor --list

# Export full scan to JSON
sudo python wifi_auditor.py --list --export scan.json

# Run unit tests without any hardware
python wifi_auditor.py --test
```

---

### Output

```
#   ESSID            BSSID              CH   dBm    ENC    WPS   VENDOR
─────────────────────────────────────────────────────────────────────────
1   HomeNetwork      AA:BB:CC:DD:EE:FF   6   -41   WPA2   WPS   Netgear
2   Office-5G        11:22:33:44:55:66  36   -67   WPA2    —    TP-Link
3   AndroidAP_3F2A   DE:AD:BE:EF:11:22   1   -72   WPA2    —    Unknown
```

WPS entries are highlighted — these may be vulnerable to Pixie Dust via `reaver` or `bully`, independent of password complexity.

---

### PMKID capture

Introduced by Jens Steube (hashcat) in 2018. The PMKID is derived from the AP's PMK and is present in the first EAPOL frame — meaning you can capture it from a passive beacon scan without waiting for a client to connect or sending deauth frames.

```bash
# Capture
sudo python wifi_auditor.py -i wlan0 --pmkid
# → writes target.hc22000

# Crack offline with hashcat
hashcat -m 22000 target.hc22000 /usr/share/wordlists/rockyou.txt
```

This is generally quieter than the classic 4-way handshake capture since it avoids deauth packets.

---

### License

MIT
