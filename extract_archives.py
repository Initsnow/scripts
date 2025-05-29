#!/usr/bin/env python3

import subprocess
import sys
import re
from pathlib import Path
import toml

# --- Configuration: TOML File ---
CONFIG_FILE_NAME = "passwords.toml"

# Common archive extensions (regex pattern)
ARCHIVE_PATTERN = re.compile(r"\.(zip|rar|7z|tar|gz|bz2|xz)$", re.IGNORECASE)


# --- Helper function to load common passwords from TOML ---
def load_common_passwords_from_config(script_dir: Path) -> list[str]:
    config_file_path = script_dir / CONFIG_FILE_NAME
    passwords = []
    if config_file_path.is_file():
        try:
            config_data = toml.load(config_file_path)
            loaded_passwords = config_data.get("common_passwords")
            if isinstance(loaded_passwords, list) and all(
                isinstance(p, str) for p in loaded_passwords
            ):
                passwords = loaded_passwords
                print(
                    f"Successfully loaded {len(passwords)} common passwords from {config_file_path}"
                )
            elif loaded_passwords is not None:
                print(
                    f"Warning: 'common_passwords' in {config_file_path} is not a list of strings. Using empty list.",
                    file=sys.stderr,
                )
            else:
                print(
                    f"Warning: 'common_passwords' key not found in {config_file_path}. Using empty list.",
                    file=sys.stderr,
                )
        except toml.TomlDecodeError as e:
            print(
                f"Error: Could not parse {config_file_path}: {e}. Using empty list for common passwords.",
                file=sys.stderr,
            )
        except Exception as e:
            print(
                f"Error loading {config_file_path}: {e}. Using empty list for common passwords.",
                file=sys.stderr,
            )
    else:
        print(
            f"Info: Configuration file {config_file_path} not found. No common passwords loaded from file."
        )
        print(
            f"You can create a '{CONFIG_FILE_NAME}' file in the script's directory with a list like:"
        )
        print('common_passwords = ["pw1", "pw2"]')
    return passwords


# --- Helper function to attempt extraction ---
def try_extract(
    archive_path: Path,
    extract_dir: Path,
    password: str = None,  # None for initial attempt, str for specific password
    display_cmd: bool = True,
):
    """
    Attempts to extract an archive using 7z.
    If password is None, it attempts extraction with an empty password string.
    Otherwise, it uses the provided password string.

    Returns:
        dict: {
            "success": bool,
            "stderr": str,
            "stdout": str,
            "exit_code": int or None (if 7z not found)
        }
    """
    base_args_for_cmd = ["7z", "x", str(archive_path), f"-o{str(extract_dir)}", "-y"]
    cmd_args = list(base_args_for_cmd)  # Make a copy for actual execution

    # For 7z command:
    # If password is None (initial attempt), use an empty string password "-p".
    # If password is a string (even empty), use "-pPASSWORD".
    # This prevents 7z from hanging waiting for interactive input.
    password_for_7z_cmd = password if password is not None else ""
    cmd_args.append(f"-p{password_for_7z_cmd}")

    if display_cmd:
        # For display, we want to be more specific about what's being tried.
        display_args_list = [
            "7z",
            "x",
            str(archive_path),
            f"-o{str(extract_dir)}",
            "-y",
        ]  # Start with base for display
        if (
            password is not None
        ):  # An actual password string was provided (common, user, or explicit empty)
            if password:  # Non-empty password string
                display_args_list.append("-p********")
            else:  # Explicit empty string password was provided
                display_args_list.append(
                    "-p<empty>"
                )  # Indicate trying an explicit empty password
        # If password is None (initial attempt), display_args_list remains without -p,
        # implying "trying without specifying a password" (even though we send -p"" to 7z).
        print(f"Executing: {' '.join(display_args_list)}")

    print("--- 7zip Output Start ---")
    try:
        process = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
            errors="replace",
            # Consider adding a timeout here for very stubborn cases, though -p"" should prevent hangs.
            # timeout=30 # Example: 30 seconds
        )

        if process.stdout:
            print(process.stdout.strip())
        if process.stderr:
            if process.returncode != 0:
                print(f"7zip stderr:\n{process.stderr.strip()}", file=sys.stderr)
            else:
                print(f"7zip stderr (info):\n{process.stderr.strip()}")

        print("--- 7zip Output End ---")

        success_condition = process.returncode == 0

        return {
            "success": success_condition,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "exit_code": process.returncode,
        }
    # except subprocess.TimeoutExpired:
    #     print("--- 7zip Output End (Timeout) ---", file=sys.stderr)
    #     msg = "ERROR: 7zip command timed out. The archive might be very large or 7zip is unresponsive."
    #     print(msg, file=sys.stderr)
    #     return {"success": False, "stdout": "", "stderr": msg, "exit_code": -1002} # Custom code for timeout
    except FileNotFoundError:
        print("--- 7zip Output End (Error) ---", file=sys.stderr)
        msg = "ERROR: 7zip command ('7z') not found. Please ensure 7-Zip is installed and in your system's PATH."
        print(msg, file=sys.stderr)
        return {"success": False, "stdout": "", "stderr": msg, "exit_code": -1000}
    except Exception as e:
        print("--- 7zip Output End (Error) ---", file=sys.stderr)
        msg = f"An unexpected error occurred while trying to run 7zip: {e}"
        print(msg, file=sys.stderr)
        return {"success": False, "stdout": "", "stderr": msg, "exit_code": -1001}


# --- Main script logic ---
def main(target_dir_str: str = "."):
    script_dir = Path(__file__).resolve().parent
    common_passwords = load_common_passwords_from_config(script_dir)

    target_dir = Path(target_dir_str).resolve()

    if not target_dir.is_dir():
        print(f"Error: Directory not found: {target_dir}")
        sys.exit(1)

    print(f"Scanning for compressed files in: {target_dir}")

    compressed_files = []
    for item in target_dir.iterdir():
        if item.is_file() and ARCHIVE_PATTERN.search(item.name):
            compressed_files.append(item)

    if not compressed_files:
        print(f"No compressed files found in directory: {target_dir}")
        return

    print(f"Found {len(compressed_files)} compressed files to extract.")

    first_7zip_run = True

    for archive_path in compressed_files:
        file_name = archive_path.name

        current_stem = archive_path.stem
        if (
            archive_path.suffix.lower() in [".gz", ".bz2", ".xz"]
            and Path(current_stem).suffix.lower() == ".tar"
        ):
            file_stem_for_dir = Path(current_stem).stem
        else:
            file_stem_for_dir = current_stem

        extract_dir = target_dir / file_stem_for_dir

        print(f"\n----------------------------------------")
        print(f"Processing: {file_name}")

        if not extract_dir.exists():
            try:
                extract_dir.mkdir(parents=True)
                print(f"Created extraction directory: {extract_dir}")
            except OSError as e:
                print(f"Error creating directory {extract_dir}: {e}", file=sys.stderr)
                continue
        else:
            print(f"Extraction directory already exists: {extract_dir}")

        extraction_successful = False
        attempted_password_used = ""  # Stores the password string that worked (or "" if initial attempt worked)

        # 1. Try extracting without specifying a password (internally uses empty password "-p")
        print(f"Attempting extraction (trying with empty password) for {file_name}...")
        # Pass password=None for the initial attempt
        result = try_extract(archive_path, extract_dir, password=None)

        if first_7zip_run and result["exit_code"] == -1000:
            print("Aborting script because 7zip is not available.", file=sys.stderr)
            sys.exit(1)
        first_7zip_run = False

        if result["success"]:
            extraction_successful = True
            # attempted_password_used = "" # Indicates success without an explicit password from list/user
        else:
            print(f"Extraction with empty password failed for {file_name}.")
            print(f"7zip exit code: {result['exit_code']}")

            needs_pw_indicators = [
                "password",
                "encrypted",
                "wrong password",
                "data error",
            ]  # "checksum error" can also be pw related for some formats
            stderr_lower = result["stderr"].lower()
            # Checksum error can sometimes be due to wrong password, especially with RAR
            might_need_password = (
                any(indicator in stderr_lower for indicator in needs_pw_indicators)
                or "checksum error" in stderr_lower
            )

            if (
                might_need_password or result["exit_code"] == 2
            ):  # Exit code 2 is often "Fatal error" which includes password issues
                print(
                    "Archive seems to be password protected or data is corrupted (possibly due to wrong password)."
                )

                if common_passwords:
                    print(
                        f"Trying {len(common_passwords)} common password(s) from config file..."
                    )
                    for common_pw in common_passwords:
                        print(
                            f"Attempting common password for {file_name}... (password itself is hidden)"
                        )
                        # Pass the actual common_pw string
                        pw_result = try_extract(
                            archive_path, extract_dir, password=common_pw
                        )
                        if pw_result["success"]:
                            extraction_successful = True
                            attempted_password_used = common_pw
                            print(
                                f"✓ Successfully extracted {file_name} with a common password."
                            )
                            break
                else:
                    print("No common passwords configured or loaded to try.")

                if not extraction_successful:
                    print(
                        f"Common passwords failed or none were available for {file_name}."
                    )
                    try:
                        user_input = input(
                            f"Enter password for '{file_name}' (or type 's'/'skip' to skip, 'q'/'quit' to quit all): "
                        ).strip()
                    except EOFError:
                        print("EOFError: Cannot read input. Skipping password prompt.")
                        user_input = "s"

                    if user_input.lower() in ["s", "skip"]:
                        print(f"Skipping archive: {file_name}")
                    elif user_input.lower() in ["q", "quit"]:
                        print("Quitting script as per user request.")
                        sys.exit(0)
                    elif user_input:  # If user entered something (not empty)
                        print("Attempting extraction with user-provided password...")
                        # Pass the actual user_input string
                        pw_result = try_extract(
                            archive_path, extract_dir, password=user_input
                        )
                        if pw_result["success"]:
                            extraction_successful = True
                            attempted_password_used = user_input
                    else:  # User just pressed Enter (empty input)
                        print(
                            "Attempting extraction with an explicit empty password from user..."
                        )
                        # Pass an explicit empty string ""
                        pw_result = try_extract(archive_path, extract_dir, password="")
                        if pw_result["success"]:
                            extraction_successful = True
                            attempted_password_used = (
                                ""  # Explicit empty password worked
                            )

            else:  # Not a clear password error, or 7zip failed for other reasons
                print(
                    f"✗ Failed to extract {file_name}. The error might not be password-related, or it's an unrecognized password error."
                )

        if extraction_successful:
            print(f"✓ Successfully extracted {file_name} to {extract_dir}")
            if (
                attempted_password_used is not None and attempted_password_used != ""
            ):  # Check if it's not the initial success or explicit empty
                print("(Used a password for extraction)")
            elif (
                attempted_password_used == "" and not result["success"]
            ):  # Explicit empty password from user/list worked after initial fail
                print("(Used an explicit empty password for extraction)")
            try:
                archive_path.unlink()
                print(f"✓ Deleted original archive: {file_name}")
            except OSError as e:
                print(
                    f"✗ Warning: Failed to delete original archive {file_name}. Error: {e}",
                    file=sys.stderr,
                )
        else:
            print(f"✗ Failed to extract {file_name} after all attempts.")

    print(f"\n----------------------------------------")
    print("Extraction process completed!")


if __name__ == "__main__":
    try:
        import toml
    except ImportError:
        print(
            "Error: The 'toml' library is required. Please install it using 'pip install toml'",
            file=sys.stderr,
        )
        sys.exit(1)

    if len(sys.argv) > 2:
        print("Usage: python extract_archives.py [directory_path]")
        sys.exit(1)

    dir_arg = sys.argv[1] if len(sys.argv) == 2 else "."
    main(dir_arg)

