#!/usr/bin/env python3
"""
QEMU Runner - A simple command line utility for running QEMU virtual machines
Copyright (c) 2024 - Open Source (MIT License)
"""

import argparse
import subprocess
import sys
import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any


class QEMURunner:
    """Main class for managing QEMU virtual machines"""
    
    def __init__(self):
        self.qemu_binary = self._find_qemu_binary()
        
    def _find_qemu_binary(self) -> str:
        """Find the appropriate QEMU binary on the system"""
        # Common QEMU binary names
        qemu_binaries = [
            'qemu-system-x86_64',
            'qemu-system-i386',
            'qemu-system-aarch64',
            'qemu-kvm'
        ]
        
        for binary in qemu_binaries:
            if subprocess.run(['which', binary], capture_output=True).returncode == 0:
                return binary
        
        raise RuntimeError("No QEMU binary found. Please install QEMU.")
    
    def _build_qemu_command(self, args: argparse.Namespace) -> List[str]:
        """Build the QEMU command based on provided arguments"""
        cmd = [self.qemu_binary]
        
        # Memory
        if args.memory:
            cmd.extend(['-m', args.memory])
        
        # CPU cores
        if args.cores:
            cmd.extend(['-smp', str(args.cores)])
        
        # Disk image
        if args.disk:
            if not os.path.exists(args.disk):
                raise FileNotFoundError(f"Disk image not found: {args.disk}")
            cmd.extend(['-hda', args.disk])
        
        # CD-ROM/ISO
        if args.cdrom:
            if not os.path.exists(args.cdrom):
                raise FileNotFoundError(f"CD-ROM image not found: {args.cdrom}")
            cmd.extend(['-cdrom', args.cdrom])
        
        # Boot order
        if args.boot:
            cmd.extend(['-boot', args.boot])
        
        # Network
        if args.network:
            cmd.extend(['-netdev', f'user,id=net0', '-device', f'{args.network_device},netdev=net0'])
        
        # VNC display
        if args.vnc:
            cmd.extend(['-vnc', args.vnc])
        elif args.display:
            cmd.extend(['-display', args.display])
        else:
            # Default to headless mode with serial output
            cmd.extend(['-display', 'none'])
            cmd.extend(['-serial', 'stdio'])
        
        # Enable KVM if available and accessible
        if args.enable_kvm and os.path.exists('/dev/kvm'):
            try:
                # Test if we can actually access KVM
                with open('/dev/kvm', 'r'):
                    cmd.extend(['-enable-kvm'])
            except PermissionError:
                # KVM not accessible, use software emulation
                if args.verbose:
                    print("KVM not accessible, using software emulation")
                cmd.extend(['-accel', 'tcg'])
        
        # Additional QEMU arguments
        if args.qemu_args:
            cmd.extend(args.qemu_args.split())
        
        return cmd
    
    def run_vm(self, args: argparse.Namespace) -> int:
        """Run the virtual machine with specified configuration"""
        try:
            cmd = self._build_qemu_command(args)
            
            if args.dry_run:
                print("Would execute:", ' '.join(cmd))
                return 0
            
            if args.verbose:
                print("Executing:", ' '.join(cmd))
            
            # Run QEMU
            result = subprocess.run(cmd)
            return result.returncode
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def create_disk(self, path: str, size: str, format: str = 'qcow2') -> int:
        """Create a new disk image"""
        try:
            qemu_img = 'qemu-img'
            cmd = [qemu_img, 'create', '-f', format, path, size]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Created disk image: {path} ({size})")
            else:
                print(f"Error creating disk: {result.stderr}", file=sys.stderr)
            
            return result.returncode
            
        except FileNotFoundError:
            print("Error: qemu-img not found. Please install QEMU tools.", file=sys.stderr)
            return 1
    
    def list_machines(self) -> int:
        """List available machine types"""
        try:
            cmd = [self.qemu_binary, '-machine', 'help']
            result = subprocess.run(cmd)
            return result.returncode
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description='QEMU Runner - A simple CLI for running QEMU virtual machines',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --disk vm.qcow2 --memory 2G --cores 2
  %(prog)s --cdrom ubuntu.iso --memory 4G --boot d
  %(prog)s create-disk --path vm.qcow2 --size 20G
  %(prog)s list-machines
        """
    )
    
    # Add main run arguments directly to the main parser for convenience
    # VM Configuration
    parser.add_argument('--disk', '-d', 
                       help='Path to disk image file')
    parser.add_argument('--cdrom', '-c', 
                       help='Path to CD-ROM/ISO image')
    parser.add_argument('--memory', '-m', default='1G',
                       help='Amount of RAM (default: 1G)')
    parser.add_argument('--cores', '-s', type=int, default=1,
                       help='Number of CPU cores (default: 1)')
    parser.add_argument('--boot', '-b', 
                       help='Boot order (c=disk, d=cdrom, n=network)')
    
    # Display options
    parser.add_argument('--vnc', 
                       help='Enable VNC display (e.g., :1)')
    parser.add_argument('--display', 
                       help='Display type (sdl, gtk, vnc, none)')
    
    # Network options
    parser.add_argument('--network', action='store_true',
                       help='Enable network (NAT)')
    parser.add_argument('--network-device', default='e1000',
                       help='Network device type (default: e1000)')
    
    # Performance options
    parser.add_argument('--enable-kvm', action='store_true', default=True,
                       help='Enable KVM acceleration (default: true)')
    
    # Advanced options
    parser.add_argument('--qemu-args', 
                       help='Additional QEMU arguments')
    
    # Utility options
    parser.add_argument('--dry-run', action='store_true',
                       help='Show command that would be executed')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Main run command (default) - duplicate the args for explicit run command
    run_parser = subparsers.add_parser('run', help='Run a virtual machine (explicit)')
    
    # VM Configuration
    run_parser.add_argument('--disk', '-d', 
                           help='Path to disk image file')
    run_parser.add_argument('--cdrom', '-c', 
                           help='Path to CD-ROM/ISO image')
    run_parser.add_argument('--memory', '-m', default='1G',
                           help='Amount of RAM (default: 1G)')
    run_parser.add_argument('--cores', '-s', type=int, default=1,
                           help='Number of CPU cores (default: 1)')
    run_parser.add_argument('--boot', '-b', 
                           help='Boot order (c=disk, d=cdrom, n=network)')
    
    # Display options
    run_parser.add_argument('--vnc', 
                           help='Enable VNC display (e.g., :1)')
    run_parser.add_argument('--display', 
                           help='Display type (sdl, gtk, vnc, none)')
    
    # Network options
    run_parser.add_argument('--network', action='store_true',
                           help='Enable network (NAT)')
    run_parser.add_argument('--network-device', default='e1000',
                           help='Network device type (default: e1000)')
    
    # Performance options
    run_parser.add_argument('--enable-kvm', action='store_true', default=True,
                           help='Enable KVM acceleration (default: true)')
    
    # Advanced options
    run_parser.add_argument('--qemu-args', 
                           help='Additional QEMU arguments')
    
    # Utility options
    run_parser.add_argument('--dry-run', action='store_true',
                           help='Show command that would be executed')
    run_parser.add_argument('--verbose', '-v', action='store_true',
                           help='Verbose output')
    
    # Create disk command
    disk_parser = subparsers.add_parser('create-disk', help='Create a new disk image')
    disk_parser.add_argument('--path', '-p', required=True,
                            help='Path for the new disk image')
    disk_parser.add_argument('--size', '-s', required=True,
                            help='Size of the disk (e.g., 20G, 500M)')
    disk_parser.add_argument('--format', '-f', default='qcow2',
                            help='Disk format (default: qcow2)')
    
    # List machines command
    subparsers.add_parser('list-machines', help='List available machine types')
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # If no command specified, default to 'run'
    if not args.command:
        args.command = 'run'
    
    try:
        runner = QEMURunner()
        
        if args.command == 'run':
            return runner.run_vm(args)
        elif args.command == 'create-disk':
            return runner.create_disk(args.path, args.size, args.format)
        elif args.command == 'list-machines':
            return runner.list_machines()
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())