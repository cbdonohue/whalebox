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
    
    startup_script = f'''#!/usr/bin/env python3
"""
Start the Ubuntu VM using QEMU
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# VM Configuration
VM_NAME = "{VM_NAME}"
VM_DIR = Path("{VM_DIR}")
RAM = "{RAM}"
CPUS = "{CPUS}"
SSH_PORT = "{SSH_PORT}"

def check_vm_running():
    """Check if VM is already running"""
    try:
        result = subprocess.run(['pgrep', '-f', f'qemu.*{{VM_NAME}}'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def start_vm():
    """Start the VM"""
    # Change to VM directory
    os.chdir(VM_DIR)
    
    # Check if VM is already running
    if check_vm_running():
        print("VM is already running!")
        print(f"SSH into it with: ssh -p {{SSH_PORT}} ubuntu@localhost")
        sys.exit(1)
    
    print("Starting Ubuntu VM...")
    print(f"SSH will be available on port {{SSH_PORT}}")
    print("Default login: ubuntu/ubuntu")
    print("")
    
    # QEMU command
    qemu_cmd = [
        'qemu-system-x86_64',
        '-name', VM_NAME,
        '-machine', 'type=pc,accel=kvm',
        '-cpu', 'host',
        '-smp', CPUS,
        '-m', RAM,
        '-drive', f'file={{VM_NAME}}.qcow2,format=qcow2,if=virtio',
        '-drive', 'file=cloud-init.iso,format=raw,if=virtio,readonly=on',
        '-netdev', f'user,id=net0,hostfwd=tcp::{{SSH_PORT}}-:22',
        '-device', 'virtio-net-pci,netdev=net0',
        '-display', 'none',
        '-daemonize',
        '-pidfile', f'{{VM_NAME}}.pid'
    ]
    
    try:
        # Start QEMU
        subprocess.run(qemu_cmd, check=True)
        
        # Wait a moment for the VM to start
        time.sleep(2)
        
        # Check if PID file was created
        pid_file = VM_DIR / f"{{VM_NAME}}.pid"
        if pid_file.exists():
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
            print("VM started successfully!")
            print(f"PID: {{pid}}")
            print("")
            print("To SSH into the VM:")
            print(f"  ssh -p {{SSH_PORT}} ubuntu@localhost")
            print("")
            print("To stop the VM:")
            print("  ./stop-vm.py")
        else:
            print("Failed to start VM")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to start VM: {{e}}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting VM: {{e}}")
        sys.exit(1)

def main():
    """Main function"""
    if not VM_DIR.exists():
        print(f"Error: VM directory {{VM_DIR}} does not exist")
        print("Please run setup-ubuntu-vm.py first")
        sys.exit(1)
    
    start_vm()

if __name__ == "__main__":
    main()
'''

    with open("start-vm.py", "w") as f:
        f.write(startup_script)
    
    os.chmod("start-vm.py", 0o755)

def create_stop_script():
    """Create stop script"""
    print_status("Creating VM stop script...")
    
    stop_script = f'''#!/usr/bin/env python3
"""
Stop the Ubuntu VM
"""

import os
import sys
import signal
import subprocess
from pathlib import Path

# VM Configuration
VM_NAME = "{VM_NAME}"
VM_DIR = Path("{VM_DIR}")

def kill_qemu_processes():
    """Kill all QEMU processes for this VM"""
    try:
        subprocess.run(['pkill', '-f', f'qemu.*{{VM_NAME}}'], check=False)
        print("Killed all QEMU processes for this VM")
    except Exception as e:
        print(f"Error killing QEMU processes: {{e}}")

def stop_vm():
    """Stop the VM"""
    # Change to VM directory
    os.chdir(VM_DIR)
    
    pid_file = VM_DIR / f"{{VM_NAME}}.pid"
    
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Try to terminate the process gracefully
            try:
                os.kill(pid, signal.SIGTERM)
                print("VM stopped successfully")
                pid_file.unlink()  # Remove PID file
                return
            except ProcessLookupError:
                print(f"Process with PID {{pid}} not found")
            except PermissionError:
                print(f"Permission denied when trying to kill PID {{pid}}")
            except Exception as e:
                print(f"Failed to stop VM with PID {{pid}}: {{e}}")
            
            print("Trying to kill all QEMU processes for this VM...")
            kill_qemu_processes()
            pid_file.unlink()  # Remove PID file
            
        except ValueError:
            print("Invalid PID in PID file")
            print("Trying to kill all QEMU processes for this VM...")
            kill_qemu_processes()
            pid_file.unlink()
        except Exception as e:
            print(f"Error reading PID file: {{e}}")
            print("Trying to kill all QEMU processes for this VM...")
            kill_qemu_processes()
            if pid_file.exists():
                pid_file.unlink()
    else:
        print("VM PID file not found. Trying to kill all QEMU processes for this VM...")
        kill_qemu_processes()

def main():
    """Main function"""
    if not VM_DIR.exists():
        print(f"Error: VM directory {{VM_DIR}} does not exist")
        sys.exit(1)
    
    stop_vm()

if __name__ == "__main__":
    main()
'''

    with open("stop-vm.py", "w") as f:
        f.write(stop_script)
    
    os.chmod("stop-vm.py", 0o755)

def create_status_script():
    """Create status script"""
    print_status("Creating VM status script...")
    
    status_script = f'''#!/usr/bin/env python3
"""
Check the status of the Ubuntu VM
"""

import os
import sys
import subprocess
import signal
from pathlib import Path

# VM Configuration
VM_NAME = "{VM_NAME}"
VM_DIR = Path("{VM_DIR}")
SSH_PORT = "{SSH_PORT}"

def check_vm_running():
    """Check if VM is running via pgrep"""
    try:
        result = subprocess.run(['pgrep', '-f', f'qemu.*{{VM_NAME}}'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def test_ssh_connection():
    """Test SSH connectivity to the VM"""
    print("Testing SSH connection...")
    try:
        result = subprocess.run([
            'timeout', '5',
            'ssh', '-p', SSH_PORT, 
            '-o', 'ConnectTimeout=3',
            '-o', 'BatchMode=yes',
            'ubuntu@localhost',
            'echo', 'SSH OK'
        ], capture_output=True, text=True, timeout=6)
        
        if result.returncode == 0:
            print("SSH: ACCESSIBLE")
        else:
            print("SSH: NOT READY (VM may still be booting)")
    except subprocess.TimeoutExpired:
        print("SSH: NOT READY (connection timeout)")
    except Exception as e:
        print(f"SSH: ERROR ({{e}})")

def check_vm_status():
    """Check and display VM status"""
    # Change to VM directory
    if VM_DIR.exists():
        os.chdir(VM_DIR)
    
    print("=== VM Status ===")
    
    pid_file = VM_DIR / f"{{VM_NAME}}.pid"
    
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is actually running
            try:
                os.kill(pid, 0)  # Send signal 0 to check if process exists
                print(f"Status: RUNNING (PID: {{pid}})")
                print(f"SSH: ssh -p {{SSH_PORT}} ubuntu@localhost")
                print("")
                test_ssh_connection()
            except ProcessLookupError:
                print("Status: STOPPED (stale PID file)")
                pid_file.unlink()  # Remove stale PID file
            except PermissionError:
                # Process exists but we can't signal it (different user)
                print(f"Status: RUNNING (PID: {{pid}})")
                print(f"SSH: ssh -p {{SSH_PORT}} ubuntu@localhost")
                print("")
                test_ssh_connection()
                
        except (ValueError, FileNotFoundError):
            print("Status: STOPPED (invalid PID file)")
            if pid_file.exists():
                pid_file.unlink()
        except Exception as e:
            print(f"Status: UNKNOWN (error reading PID file: {{e}})")
    else:
        if check_vm_running():
            print("Status: RUNNING (no PID file)")
        else:
            print("Status: STOPPED")
    
    print("")
    print("Available commands:")
    print("  ./start-vm.py   - Start the VM")
    print("  ./stop-vm.py    - Stop the VM")
    print("  ./status-vm.py  - Show this status")

def main():
    """Main function"""
    if not VM_DIR.exists():
        print(f"Error: VM directory {{VM_DIR}} does not exist")
        print("Please run setup-ubuntu-vm.py first")
        sys.exit(1)
    
    check_vm_status()

if __name__ == "__main__":
    main()
'''

    with open("status-vm.py", "w") as f:
        f.write(status_script)
    
    os.chmod("status-vm.py", 0o755)

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
        print("2. ./start-vm.py     # Start the VM")
        print("")
        print("3. SSH into VM:")
        print(f"   ssh -p {SSH_PORT} -o PreferredAuthentications=password ubuntu@localhost")
        print("   Password: ubuntu")
        print("")
        print("4. Management commands:")
        print("   ./status-vm.py    # Check VM status and SSH connectivity")
        print("   ./stop-vm.py      # Stop the VM")
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