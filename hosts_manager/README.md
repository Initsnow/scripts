# ! AI GENERATED, NEED REVIEW
# Windows Hosts Manager

A Python script that adds hosts entries from https://a.dove.isdumb.one/list.txt to the Windows hosts file, with support for custom hosts entries. The script is designed to be non-invasive, preserving original hosts file content and allowing easy removal of changes.

## Features

- Downloads and adds hosts entries from a specified URL
- Preserves all original hosts file content
- Supports adding custom hosts entries
- Clearly marks added content for easy identification
- Provides simple commands to update or remove hosts entries
- Automatically requests administrator privileges when needed
- Uses only standard Python libraries

## Requirements

- Python 3.x
- Windows operating system
- Administrator privileges (the script will automatically request them)

## Usage

### Basic Commands

```
python hosts_manager.py [command] [options]
```

### Available Commands

- `update` - Update hosts file with entries from the default URL
- `remove` - Remove all hosts entries added by this script
- `add-custom` - Add custom hosts entries
- `help` - Show help information

### Options

- `--url=URL` - Specify a different URL for hosts entries
- `--file=FILE` - Read custom hosts from a file

### Examples

1. Update hosts with entries from the default URL:
   ```
   python hosts_manager.py update
   ```

2. Update hosts with entries from a custom URL:
   ```
   python hosts_manager.py update --url=https://example.com/hosts.txt
   ```

3. Add custom hosts entries from a file:
   ```
   python hosts_manager.py add-custom --file=my_hosts.txt
   ```

4. Add custom hosts entries manually (will prompt for input):
   ```
   python hosts_manager.py add-custom
   ```

5. Remove all hosts entries added by this script:
   ```
   python hosts_manager.py remove
   ```

## How It Works

1. The script adds special marker comments to the hosts file to identify the content it adds
2. When updating, it preserves all original content and appends new entries after the markers
3. When removing, it restores the hosts file to its original state by removing everything after the start marker
4. Custom hosts are stored between separate markers for easy management

## Format for Custom Hosts

Custom hosts should follow the standard hosts file format:

```
127.0.0.1 example.com
127.0.0.1 test.example.com
```

Each line should contain an IP address followed by one or more hostnames.
