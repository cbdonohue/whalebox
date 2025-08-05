#!/usr/bin/env python3

"""
QEMU Ubuntu VM Setup Script
Creates a Ubuntu VM that you can SSH into
Python version of setup-ubuntu-vm.sh
"""

import os
import sys
import subprocess
import shutil
import urllib.request
from pathlib import Path
import time
import signal

# Configuration variables
VM_NAME = "ubuntu-vm"
VM_DIR = Path.cwd() / "vms" / VM_NAME
DISK_SIZE = "20G"
RAM = "2G"
CPUS = "2"
SSH_PORT = "2222"
UBUNTU_CLOUD_URL = "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
UBUNTU_CLOUD_IMG = "jammy-server-cloudimg-amd64.img"

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color

def print_status(message):
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")

def print_warning(message):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def print_error(message):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def check_qemu():
    """Check if QEMU is installed"""
    if not shutil.which("qemu-system-x86_64"):
        print_error("QEMU is not installed. Please install it first:")
        print("  Ubuntu/Debian: sudo apt install qemu-system-x86 qemu-utils")
        print("  Fedora: sudo dnf install qemu-system-x86 qemu-img")
        print("  Arch: sudo pacman -S qemu-system-x86 qemu-img")
        sys.exit(1)

def setup_directories():
    """Create VM directory structure"""
    print_status("Creating VM directory structure...")
    VM_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(VM_DIR)

def download_cloud_image():
    """Download Ubuntu cloud image if it doesn't exist"""
    cloud_img_path = VM_DIR / UBUNTU_CLOUD_IMG
    if not cloud_img_path.exists():
        print_status("Downloading Ubuntu 22.04 LTS cloud image...")
        try:
            urllib.request.urlretrieve(UBUNTU_CLOUD_URL, cloud_img_path)
        except Exception as e:
            print_error(f"Failed to download cloud image: {e}")
            sys.exit(1)
    else:
        print_status("Ubuntu cloud image already exists, skipping download.")

def create_disk():
    """Create virtual disk from cloud image"""
    vm_disk = VM_DIR / f"{VM_NAME}.qcow2"
    if not vm_disk.exists():
        print_status("Converting cloud image to VM disk...")
        try:
            subprocess.run([
                "qemu-img", "convert", "-f", "qcow2", "-O", "qcow2",
                UBUNTU_CLOUD_IMG, f"{VM_NAME}.qcow2"
            ], check=True)
            
            print_status(f"Resizing disk to {DISK_SIZE}...")
            subprocess.run([
                "qemu-img", "resize", f"{VM_NAME}.qcow2", DISK_SIZE
            ], check=True)
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to create disk: {e}")
            sys.exit(1)
    else:
        print_status("Virtual disk already exists, skipping creation.")

def create_cloud_init():
    """Create cloud-init configuration for automated setup"""
    print_status("Creating cloud-init configuration...")
    
    # Create user-data for cloud-init
    user_data = """#cloud-config
users:
  - name: ubuntu
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    ssh_authorized_keys:
      - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7... # This will be replaced with your actual key
    lock_passwd: false
    # Password hash for 'ubuntu' - generated with: openssl passwd -6 ubuntu
    passwd: $6$rounds=4096$saltsalt$IxDD3jeSOb5eB1CX5LBsqZFVkJdido3OUILO5Ue7442fiqxjRp0t/PQMFz2bJXaFS2dovcGkT0.vWu5SqN9V4/

# Enable SSH
ssh_pwauth: true
disable_root: false

# Install essential packages
packages:
  - openssh-server
  - curl
  - wget
  - git
  - htop
  - vim
  - net-tools

# Configure SSH
write_files:
  - path: /etc/ssh/sshd_config.d/custom.conf
    content: |
      PermitRootLogin yes
      PasswordAuthentication yes
      PubkeyAuthentication yes
    permissions: '0644'

# Ensure cloud-init completes and SSH is ready
runcmd:
  - systemctl enable ssh
  - systemctl start ssh
  - ufw --force enable
  - ufw allow ssh
  - systemctl restart ssh
  - echo "Cloud-init setup completed" > /var/log/cloud-init-complete.log

# Final message
final_message: "Ubuntu VM is ready! SSH available on port 22"
"""

    with open("user-data", "w") as f:
        f.write(user_data)

    # Create meta-data
    meta_data = f"""instance-id: {VM_NAME}
local-hostname: {VM_NAME}
"""
    
    with open("meta-data", "w") as f:
        f.write(meta_data)

    # Create cloud-init ISO
    iso_created = False
    for tool in ["genisoimage", "mkisofs"]:
        if shutil.which(tool):
            try:
                subprocess.run([
                    tool, "-output", "cloud-init.iso", "-volid", "cidata",
                    "-joliet", "-rock", "user-data", "meta-data"
                ], check=True)
                iso_created = True
                break
            except subprocess.CalledProcessError:
                continue
    
    if not iso_created:
        print_warning("Neither genisoimage nor mkisofs found. Cloud-init ISO not created.")
        print_warning("You'll need to configure the VM manually during installation.")

def setup_ssh_key():
    """Generate SSH key if it doesn't exist"""
    ssh_key_path = Path.home() / ".ssh" / "id_rsa"
    ssh_pub_path = ssh_key_path.with_suffix(".pub")
    
    if not ssh_key_path.exists():
        print_status("Generating SSH key pair...")
        try:
            subprocess.run([
                "ssh-keygen", "-t", "rsa", "-b", "4096", 
                "-f", str(ssh_key_path), "-N", ""
            ], check=True)
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to generate SSH key: {e}")
            return
    
    # Update cloud-init with actual SSH key
    if ssh_pub_path.exists():
        try:
            with open(ssh_pub_path, "r") as f:
                ssh_key = f.read().strip()
            
            # Read user-data file
            with open("user-data", "r") as f:
                user_data_content = f.read()
            
            # Replace the placeholder SSH key
            user_data_content = user_data_content.replace(
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7...", 
                ssh_key
            )
            
            # Write back the updated user-data
            with open("user-data", "w") as f:
                f.write(user_data_content)
            
            # Recreate cloud-init ISO with updated key
            if Path("cloud-init.iso").exists():
                Path("cloud-init.iso").unlink()
                
                for tool in ["genisoimage", "mkisofs"]:
                    if shutil.which(tool):
                        try:
                            subprocess.run([
                                tool, "-output", "cloud-init.iso", "-volid", "cidata",
                                "-joliet", "-rock", "user-data", "meta-data"
                            ], check=True)
                            break
                        except subprocess.CalledProcessError:
                            continue
                            
        except Exception as e:
            print_error(f"Failed to setup SSH key: {e}")

def create_startup_script():
    """Create startup script"""
    print_status("Creating VM startup script...")
    
    startup_script = f"""#!/bin/bash

# Start the Ubuntu VM
VM_DIR="{VM_DIR}"
VM_NAME="{VM_NAME}"
RAM="{RAM}"
CPUS="{CPUS}"
SSH_PORT="{SSH_PORT}"

cd "$VM_DIR"

# Check if VM is already running
if pgrep -f "qemu.*$VM_NAME" > /dev/null; then
    echo "VM is already running!"
    echo "SSH into it with: ssh -p {SSH_PORT} ubuntu@localhost"
    exit 1
fi

echo "Starting Ubuntu VM..."
echo "SSH will be available on port {SSH_PORT}"
echo "Default login: ubuntu/ubuntu"
echo ""

# Start QEMU
qemu-system-x86_64 \\
    -name "$VM_NAME" \\
    -machine type=pc,accel=kvm \\
    -cpu host \\
    -smp "$CPUS" \\
    -m "$RAM" \\
    -drive file="$VM_NAME.qcow2",format=qcow2,if=virtio \\
    -drive file=cloud-init.iso,format=raw,if=virtio,readonly=on \\
    -netdev user,id=net0,hostfwd=tcp::$SSH_PORT-:22 \\
    -device virtio-net-pci,netdev=net0 \\
    -display none \\
    -daemonize \\
    -pidfile "$VM_NAME.pid"

# Wait a moment for the VM to start
sleep 2

if [ -f "$VM_NAME.pid" ]; then
    echo "VM started successfully!"
    echo "PID: $(cat $VM_NAME.pid)"
    echo ""
    echo "To SSH into the VM:"
    echo "  ssh -p {SSH_PORT} ubuntu@localhost"
    echo ""
    echo "To stop the VM:"
    echo "  ./stop-vm.sh"
else
    echo "Failed to start VM"
    exit 1
fi
"""

    with open("start-vm.sh", "w") as f:
        f.write(startup_script)
    
    os.chmod("start-vm.sh", 0o755)

def create_stop_script():
    """Create stop script"""
    print_status("Creating VM stop script...")
    
    stop_script = f"""#!/bin/bash

VM_DIR="{VM_DIR}"
VM_NAME="{VM_NAME}"

cd "$VM_DIR"

if [ -f "$VM_NAME.pid" ]; then
    PID=$(cat "$VM_NAME.pid")
    if kill "$PID" 2>/dev/null; then
        echo "VM stopped successfully"
        rm -f "$VM_NAME.pid"
    else
        echo "Failed to stop VM with PID $PID"
        echo "Trying to kill all QEMU processes for this VM..."
        pkill -f "qemu.*$VM_NAME"
        rm -f "$VM_NAME.pid"
    fi
else
    echo "VM PID file not found. Trying to kill all QEMU processes for this VM..."
    pkill -f "qemu.*$VM_NAME"
fi
"""

    with open("stop-vm.sh", "w") as f:
        f.write(stop_script)
    
    os.chmod("stop-vm.sh", 0o755)

def create_status_script():
    """Create status script"""
    print_status("Creating VM status script...")
    
    status_script = f"""#!/bin/bash

VM_DIR="{VM_DIR}"
VM_NAME="{VM_NAME}"
SSH_PORT="{SSH_PORT}"

cd "$VM_DIR"

echo "=== VM Status ==="
if [ -f "$VM_NAME.pid" ]; then
    PID=$(cat "$VM_NAME.pid")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Status: RUNNING (PID: $PID)"
        echo "SSH: ssh -p {SSH_PORT} ubuntu@localhost"
        echo ""
        echo "Testing SSH connection..."
        timeout 5 ssh -p {SSH_PORT} -o ConnectTimeout=3 -o BatchMode=yes ubuntu@localhost echo "SSH OK" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "SSH: ACCESSIBLE"
        else
            echo "SSH: NOT READY (VM may still be booting)"
        fi
    else
        echo "Status: STOPPED (stale PID file)"
        rm -f "$VM_NAME.pid"
    fi
else
    if pgrep -f "qemu.*$VM_NAME" > /dev/null; then
        echo "Status: RUNNING (no PID file)"
    else
        echo "Status: STOPPED"
    fi
fi

echo ""
echo "Available commands:"
echo "  ./start-vm.sh   - Start the VM"
echo "  ./stop-vm.sh    - Stop the VM"
echo "  ./status-vm.sh  - Show this status"
"""

    with open("status-vm.sh", "w") as f:
        f.write(status_script)
    
    os.chmod("status-vm.sh", 0o755)

def main():
    """Main setup function"""
    print_status("Setting up QEMU Ubuntu VM...")
    
    try:
        check_qemu()
        setup_directories()
        download_cloud_image()
        create_disk()
        create_cloud_init()
        setup_ssh_key()
        create_startup_script()
        create_stop_script()
        create_status_script()
        
        print_status("VM setup completed!")
        print("")
        print(f"VM Directory: {VM_DIR}")
        print(f"SSH Port: {SSH_PORT}")
        print("")
        print("✅ HEADLESS SETUP: Uses Ubuntu cloud image with automated cloud-init")
        print("")
        print("Next steps:")
        print(f"1. cd {VM_DIR}")
        print("2. ./start-vm.sh     # Start the VM")
        print("")
        print("3. SSH into VM:")
        print(f"   ssh -p {SSH_PORT} -o PreferredAuthentications=password ubuntu@localhost")
        print("   Password: ubuntu")
        print("")
        print("4. Management commands:")
        print("   ./status-vm.sh    # Check VM status and SSH connectivity")
        print("   ./stop-vm.sh      # Stop the VM")
        print("")
        print_warning("Note: Use direct image modification with virt-customize for reliable setup.")
        print_warning("Cloud-init may not work reliably with standard Ubuntu Server ISO.")
        
    except KeyboardInterrupt:
        print_error("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()