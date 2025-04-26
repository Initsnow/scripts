#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Windows Hosts File Manager

This script downloads hosts entries from a specified URL and adds them to the Windows hosts file.
It also supports adding custom hosts entries. All changes are non-invasive and can be easily removed.
"""

import os
import sys
import requests
import datetime
import re
import subprocess

# Constants
HOSTS_FILE_PATH = r"C:\Windows\System32\drivers\etc\hosts"
DEFAULT_URL = "https://a.dove.isdumb.one/list.txt"
MARKER_START = "# === HOSTS MANAGER START ==="
MARKER_END = "# === HOSTS MANAGER END ==="
CUSTOM_MARKER_START = "# === CUSTOM HOSTS START ==="
CUSTOM_MARKER_END = "# === CUSTOM HOSTS END ==="

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return os.getuid() == 0
    except AttributeError:
        # Windows-specific check
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def run_as_admin():
    """Re-run the script with administrator privileges."""
    if not is_admin():
        print("This script requires administrator privileges to modify the hosts file.")
        print("Attempting to run as administrator...")
        
        # Re-run the script with admin privileges
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{item}"' for item in sys.argv[1:]])
        
        try:
            subprocess.run(f'powershell Start-Process -FilePath "{sys.executable}" -ArgumentList "{script} {params}" -Verb RunAs', 
                          shell=True, 
                          check=True)
            sys.exit(0)
        except subprocess.CalledProcessError:
            print("Failed to run as administrator. Please run this script as administrator manually.")
            sys.exit(1)

def fetch_hosts_from_url(url):
    """Fetch hosts entries from the specified URL."""
    try:
        content=requests.get(url, timeout=5).text
        return content
    except Exception as e:
        print(f"Error fetching hosts from {url}: {e}")
        return ""

def read_hosts_file():
    """Read the current hosts file content."""
    try:
        with open(HOSTS_FILE_PATH, 'r', encoding='utf-8') as file:
            return file.read()
        
    except Exception as e:
        print(f"Error reading hosts file: {e}")
        return ""

def write_hosts_file(content):
    """Write content to the hosts file."""
    try:
        with open(HOSTS_FILE_PATH, 'w', encoding='utf-8') as file:
            file.write(content)
        print("Hosts file updated successfully.")
        return True
    except Exception as e:
        print(f"Error writing to hosts file: {e}")
        return False

def extract_original_hosts(content):
    """Extract the original hosts content (excluding our additions)."""
    # If our markers don't exist, the entire content is original
    if MARKER_START not in content:
        return content.rstrip()
    
    # Extract content before our marker
    parts = content.split(MARKER_START, 1)
    return parts[0].rstrip()

def extract_custom_hosts(content):
    """Extract custom hosts entries if they exist."""
    if CUSTOM_MARKER_START not in content or CUSTOM_MARKER_END not in content:
        return ""
    
    # Extract content between custom markers
    pattern = f"{CUSTOM_MARKER_START}(.*?){CUSTOM_MARKER_END}"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        custom_content = match.group(1).strip()
        return custom_content
    return ""

def update_hosts(url=DEFAULT_URL, custom_hosts=""):
    """Update the hosts file with entries from URL and custom hosts."""
    # Ensure we have admin privileges
    if not is_admin():
        run_as_admin()
        return
    
    # Read current hosts file
    current_content = read_hosts_file()
    if not current_content:
        print("Could not read the hosts file.")
        return False
    
    # Extract original hosts content
    original_content = extract_original_hosts(current_content)
    
    # If no custom hosts provided, try to extract from existing file
    if not custom_hosts and CUSTOM_MARKER_START in current_content:
        custom_hosts = extract_custom_hosts(current_content)
    
    # Fetch new hosts from URL
    url_hosts = fetch_hosts_from_url(url)
    if not url_hosts:
        print("Could not fetch hosts from URL.")
        return False
    
    # Format the URL hosts content (remove comments, empty lines, etc.)
    cleaned_url_hosts = []
    for line in url_hosts.splitlines():
        line = line.strip()
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue
        # Ensure the line is a valid host entry
        if re.match(r'^\d+\.\d+\.\d+\.\d+\s+\S+', line):
            cleaned_url_hosts.append(line)
    
    # Build the new hosts file content
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_content = original_content + "\n\n"
    new_content += f"{MARKER_START} (Added on {timestamp})\n"
    new_content += f"# Source: {url}\n"
    new_content += "\n".join(cleaned_url_hosts) + "\n"
    
    # Add custom hosts if provided
    if custom_hosts:
        new_content += f"\n{CUSTOM_MARKER_START}\n"
        new_content += custom_hosts + "\n"
        new_content += f"{CUSTOM_MARKER_END}\n"
    
    new_content += f"{MARKER_END}\n"
    
    # Write the new content to the hosts file
    return write_hosts_file(new_content)

def remove_hosts():
    """Remove all hosts entries added by this script."""
    # Ensure we have admin privileges
    if not is_admin():
        run_as_admin()
        return
    
    # Read current hosts file
    current_content = read_hosts_file()
    if not current_content:
        print("Could not read the hosts file.")
        return False
    
    # Extract original hosts content
    original_content = extract_original_hosts(current_content)
    
    # Write the original content back to the hosts file
    return write_hosts_file(original_content)

def add_custom_hosts(custom_entries):
    """Add custom hosts entries."""
    # Ensure we have admin privileges
    if not is_admin():
        run_as_admin()
        return
    
    # Read current hosts file
    current_content = read_hosts_file()
    if not current_content:
        print("Could not read the hosts file.")
        return False
    
    # Extract existing custom hosts if any
    existing_custom = extract_custom_hosts(current_content)
    
    # Combine existing and new custom hosts
    if existing_custom:
        combined_custom = existing_custom + "\n" + custom_entries
    else:
        combined_custom = custom_entries
    
    # Update hosts with the combined custom entries
    return update_hosts(custom_hosts=combined_custom)

def print_help():
    """Print help information."""
    print("Windows Hosts File Manager")
    print("=========================")
    print("Usage:")
    print("  python hosts_manager.py [command] [options]")
    print("\nCommands:")
    print("  update       - Update hosts file with entries from URL")
    print("  remove       - Remove all hosts entries added by this script")
    print("  add-custom   - Add custom hosts entries")
    print("  help         - Show this help message")
    print("\nOptions:")
    print("  --url=URL    - Specify a different URL for hosts entries")
    print("  --file=FILE  - Read custom hosts from a file")
    print("\nExamples:")
    print("  python hosts_manager.py update")
    print("  python hosts_manager.py update --url=https://example.com/hosts.txt")
    print("  python hosts_manager.py add-custom --file=my_hosts.txt")
    print("  python hosts_manager.py remove")

def main():
    """Main function to parse arguments and execute commands."""
    if len(sys.argv) < 2 or sys.argv[1] == "help":
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    # Parse options
    url = DEFAULT_URL
    custom_file = None
    
    for arg in sys.argv[2:]:
        if arg.startswith("--url="):
            url = arg[6:]
        elif arg.startswith("--file="):
            custom_file = arg[7:]
    
    # Execute command
    if command == "update":
        update_hosts(url)
    
    elif command == "remove":
        remove_hosts()
    
    elif command == "add-custom":
        custom_hosts = ""
        if custom_file:
            try:
                with open(custom_file, 'r', encoding='utf-8') as file:
                    custom_hosts = file.read()
            except Exception as e:
                print(f"Error reading custom hosts file: {e}")
                return
        else:
            print("Enter custom hosts entries (one per line). Press Ctrl+D (Unix) or Ctrl+Z (Windows) followed by Enter when done:")
            try:
                custom_hosts = sys.stdin.read()
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return
        
        add_custom_hosts(custom_hosts)
    
    else:
        print(f"Unknown command: {command}")
        print_help()

if __name__ == "__main__":
    main()
