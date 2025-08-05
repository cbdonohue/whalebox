#!/usr/bin/env python3
"""
Example usage of QEMU Runner
This script demonstrates how to use the QEMU Runner utility programmatically.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print("Output:", result.stdout)
    if result.stderr:
        print("Error:", result.stderr)
    return result.returncode == 0

def main():
    """Example usage scenarios"""
    script_path = Path(__file__).parent / "qemu_runner.py"
    
    print("=== QEMU Runner Example Usage ===\n")
    
    # Example 1: Show help
    print("1. Showing help:")
    run_command([str(script_path), "--help"])
    print()
    
    # Example 2: Create a test disk image
    print("2. Creating a test disk image:")
    test_disk = "test_vm.qcow2"
    run_command([str(script_path), "create-disk", "--path", test_disk, "--size", "1G"])
    print()
    
    # Example 3: Show what a VM run command would look like (dry run)
    print("3. Dry run - showing VM command that would be executed:")
    if Path(test_disk).exists():
        run_command([
            str(script_path), 
            "--disk", test_disk,
            "--memory", "512M",
            "--cores", "1",
            "--dry-run"
        ])
    print()
    
    # Example 4: List available machine types
    print("4. Listing available machine types:")
    run_command([str(script_path), "list-machines"])
    print()
    
    # Cleanup
    if Path(test_disk).exists():
        Path(test_disk).unlink()
        print(f"Cleaned up test disk: {test_disk}")

if __name__ == "__main__":
    main()