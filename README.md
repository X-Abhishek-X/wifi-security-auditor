# WiFi Security Auditor 🔐

> **Educational Penetration Testing Tool for Cybersecurity Students**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Termux](https://img.shields.io/badge/platform-Termux-green.svg)](https://termux.com/)

## ⚠️ LEGAL DISCLAIMER

**READ THIS CAREFULLY BEFORE USING THIS TOOL**

This tool is created **STRICTLY FOR EDUCATIONAL PURPOSES** and authorized security testing only.

### 🚨 Legal Warning

Unauthorized access to computer networks is **ILLEGAL** and punishable under:

- **USA**: Computer Fraud and Abuse Act (CFAA) - Up to 20 years imprisonment and $250,000 in fines
- **UK**: Computer Misuse Act 1990 - Up to 10 years imprisonment
- **EU**: Directive 2013/40/EU - Criminal penalties varying by member state
- **India**: IT Act 2000 Section 66 - Up to 3 years imprisonment and fines
- **Australia**: Cybercrime Act 2001 - Up to 10 years imprisonment
- **Canada**: Criminal Code Section 342.1 - Up to 10 years imprisonment

### ✅ Authorized Use Only

You **MUST**:
- ✓ Only test networks you **OWN**
- ✓ Have **WRITTEN PERMISSION** from network owner
- ✓ Comply with **ALL** local, state, and federal laws
- ✓ Use for **EDUCATIONAL** purposes only
- ✓ Document all authorized testing activities
- ✓ Follow responsible disclosure practices

### ❌ Prohibited Use

You **MUST NOT**:
- ✗ Access networks without authorization
- ✗ Use for malicious purposes
- ✗ Distribute captured data
- ✗ Violate privacy laws
- ✗ Cause damage or disruption

### 📋 Liability

**THE AUTHOR AND CONTRIBUTORS:**
- Are **NOT** responsible for any misuse of this tool
- Do **NOT** endorse illegal activities
- Provide this tool **AS-IS** without warranties
- Assume **NO LIABILITY** for your actions

**BY USING THIS TOOL, YOU ACCEPT FULL LEGAL RESPONSIBILITY FOR YOUR ACTIONS.**

---

## 📚 Educational Purpose

This tool is designed for **cybersecurity students** and **ethical hackers** to:

1. **Learn** about WiFi security protocols (WPA/WPA2/WPA3)
2. **Understand** common vulnerabilities in wireless networks
3. **Practice** authorized penetration testing techniques
4. **Develop** skills for defensive security careers
5. **Study** network security auditing methodologies

---

## 🎯 Features

- 🔍 **Network Discovery**: Scan and identify nearby WiFi networks
- 📡 **Monitor Mode**: Enable wireless adapter monitoring capabilities
- 🤝 **Handshake Capture**: Capture WPA/WPA2 4-way handshakes
- 🔓 **Password Auditing**: Test password strength using wordlists
- 🎨 **Colored Output**: Beautiful terminal interface with status indicators
- 📊 **Detailed Reporting**: Comprehensive network information display
- ⚡ **Termux Compatible**: Optimized for rooted Android devices

---

## 🛠️ Installation

### Prerequisites

**Required:**
- Rooted Android device
- Termux installed
- Wireless adapter with monitor mode support
- Root access (via `su` or `tsu`)

### Step 1: Install Termux

Download Termux from [F-Droid](https://f-droid.org/packages/com.termux/) (recommended) or GitHub releases.

### Step 2: Update Termux Packages

```bash
pkg update && pkg upgrade -y
```

### Step 3: Install Required Packages

```bash
# Install Python
pkg install python -y

# Install aircrack-ng suite
pkg install aircrack-ng -y

# Install wireless tools
pkg install wireless-tools -y

# Install root package (if not already installed)
pkg install tsu -y
```

### Step 4: Clone or Download This Repository

```bash
# Using git
pkg install git -y
git clone https://github.com/yourusername/wifi-security-auditor.git
cd wifi-security-auditor

# Or download directly
curl -O https://raw.githubusercontent.com/yourusername/wifi-security-auditor/main/wifi_auditor.py
```

### Step 5: Make Script Executable

```bash
chmod +x wifi_auditor.py
```

---

## 🚀 Usage

### Basic Usage

```bash
# Run with root privileges
sudo python3 wifi_auditor.py
```

### Advanced Options

```bash
# Specify wireless interface
sudo python3 wifi_auditor.py -i wlan0

# Use custom wordlist
sudo python3 wifi_auditor.py -w /path/to/wordlist.txt

# Automated mode
sudo python3 wifi_auditor.py -i wlan0 -w wordlist.txt --auto
```

### Command-Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `-i, --interface` | Specify wireless interface | `-i wlan0` |
| `-w, --wordlist` | Path to password wordlist | `-w rockyou.txt` |
| `--auto` | Automated mode (requires -i and -w) | `--auto` |
| `-h, --help` | Show help message | `-h` |

---

## 📖 Step-by-Step Tutorial

### 1. Prepare Your Environment

```bash
# Gain root access
tsu

# Navigate to tool directory
cd ~/wifi-security-auditor
```

### 2. Run the Tool

```bash
python3 wifi_auditor.py
```

### 3. Acknowledge Legal Warning

Read the legal disclaimer carefully and press ENTER to continue.

### 4. Select Target Network

The tool will:
- Detect wireless interfaces
- Enable monitor mode
- Scan for nearby networks
- Display discovered networks

Select your **authorized** target network by number.

### 5. Capture Handshake

The tool will:
- Focus on the target network
- Capture packets
- Wait for a client to connect (handshake)
- Save the capture file

**Tip**: You may need to wait for a device to connect to the network, or you can deauthenticate a client (advanced).

### 6. Crack Password (Optional)

If you provided a wordlist, the tool will attempt to crack the password.

```bash
# Example with wordlist
python3 wifi_auditor.py -w /path/to/rockyou.txt
```

---

## 📁 Wordlists

Common wordlists for password auditing:

### Download Popular Wordlists

```bash
# RockYou (most popular)
wget https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt

# SecLists
git clone https://github.com/danielmiessler/SecLists.git

# Common WiFi passwords
wget https://raw.githubusercontent.com/berzerk0/Probable-Wordlists/master/Real-Passwords/WPA-Length/Top304Thousand-probable-v2.txt
```

### Create Custom Wordlist

```bash
# Simple numeric passwords
crunch 8 8 0123456789 > numeric.txt

# Phone numbers pattern
crunch 10 10 0123456789 > phones.txt
```

---

## 🔧 Troubleshooting

### Issue: "No wireless interfaces found"

**Solution:**
```bash
# Check if wireless interface exists
iwconfig

# Try enabling it manually
ip link set wlan0 up
```

### Issue: "Monitor mode failed"

**Solution:**
```bash
# Kill interfering processes
airmon-ng check kill

# Manually enable monitor mode
airmon-ng start wlan0
```

### Issue: "Permission denied"

**Solution:**
```bash
# Ensure you're running as root
tsu
# or
sudo python3 wifi_auditor.py
```

### Issue: "Handshake not captured"

**Possible causes:**
- No clients connected to network
- Weak signal strength
- Interference

**Solutions:**
- Move closer to the access point
- Wait for a client to connect
- Use deauthentication (advanced, use responsibly)

---

## 🎓 Educational Resources

### Learn More About WiFi Security

- [WiFi Security Protocols (WPA/WPA2/WPA3)](https://www.wi-fi.org/discover-wi-fi/security)
- [OWASP Wireless Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [Aircrack-ng Documentation](https://www.aircrack-ng.org/documentation.html)
- [Kali Linux WiFi Penetration Testing](https://www.kali.org/docs/wireless/)

### Recommended Courses

- CompTIA Security+
- Certified Ethical Hacker (CEH)
- Offensive Security Wireless Professional (OSWP)
- SANS SEC617: Wireless Penetration Testing

### Practice Legally

- Set up your own test network
- Use platforms like HackTheBox, TryHackMe
- Participate in authorized CTF competitions
- Join bug bounty programs with proper scope

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Open a Pull Request

### Code of Conduct

- Promote ethical hacking practices
- Respect legal boundaries
- Provide educational value
- Document all changes

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**Educational Use Clause**: This software is provided for educational purposes only. Any use of this software for illegal activities is strictly prohibited and not endorsed by the author.

---

## 🙏 Acknowledgments

- **Aircrack-ng Team** - For the excellent wireless security tools
- **Termux Community** - For making Linux tools accessible on Android
- **Cybersecurity Community** - For promoting ethical hacking education

---

## 📞 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/wifi-security-auditor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/wifi-security-auditor/discussions)
- **Security**: Report vulnerabilities privately to [your-email@example.com]

---

## ⚖️ Ethical Hacking Principles

As a cybersecurity professional, always follow these principles:

1. **Get Permission**: Always obtain written authorization
2. **Respect Privacy**: Never access or distribute private data
3. **Minimize Impact**: Avoid disrupting services
4. **Document Everything**: Keep detailed logs of authorized testing
5. **Responsible Disclosure**: Report vulnerabilities ethically
6. **Continuous Learning**: Stay updated on security best practices
7. **Give Back**: Share knowledge with the community

---

## 🎖️ Certifications & Career Path

This tool helps you develop skills for:

- **Penetration Tester**
- **Security Analyst**
- **Network Security Engineer**
- **Wireless Security Specialist**
- **Red Team Operator**
- **Security Researcher**

---

**Remember: With great power comes great responsibility. Use your skills to make the internet safer, not to cause harm.**

---

*Last Updated: November 2025*
*Version: 1.0*
*Maintained by: Cybersecurity Education Community*
