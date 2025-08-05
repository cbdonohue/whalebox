#!/bin/bash

# QEMU Ubuntu VM Setup Script
# Creates a Ubuntu VM that you can SSH into

set -e  # Exit on any error

# Configuration variables
VM_NAME="ubuntu-vm"
VM_DIR="$(pwd)/vms/$VM_NAME"
DISK_SIZE="20G"
RAM="2G"
CPUS="2"
SSH_PORT="2222"
UBUNTU_CLOUD_URL="https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
UBUNTU_CLOUD_IMG="jammy-server-cloudimg-amd64.img"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if QEMU is installed
check_qemu() {
    if ! command -v qemu-system-x86_64 &> /dev/null; then
        print_error "QEMU is not installed. Please install it first:"
        echo "  Ubuntu/Debian: sudo apt install qemu-system-x86 qemu-utils"
        echo "  Fedora: sudo dnf install qemu-system-x86 qemu-img"
        echo "  Arch: sudo pacman -S qemu-system-x86 qemu-img"
        exit 1
    fi
}

# Create VM directory structure
setup_directories() {
    print_status "Creating VM directory structure..."
    mkdir -p "$VM_DIR"
    cd "$VM_DIR"
}

# Download Ubuntu cloud image if it doesn't exist
download_cloud_image() {
    if [ ! -f "$UBUNTU_CLOUD_IMG" ]; then
        print_status "Downloading Ubuntu 22.04 LTS cloud image..."
        wget -O "$UBUNTU_CLOUD_IMG" "$UBUNTU_CLOUD_URL"
    else
        print_status "Ubuntu cloud image already exists, skipping download."
    fi
}

# Create virtual disk from cloud image
create_disk() {
    if [ ! -f "$VM_NAME.qcow2" ]; then
        print_status "Converting cloud image to VM disk..."
        qemu-img convert -f qcow2 -O qcow2 "$UBUNTU_CLOUD_IMG" "$VM_NAME.qcow2"
        print_status "Resizing disk to $DISK_SIZE..."
        qemu-img resize "$VM_NAME.qcow2" "$DISK_SIZE"
    else
        print_status "Virtual disk already exists, skipping creation."
    fi
}

# Create cloud-init configuration for automated setup
create_cloud_init() {
    print_status "Creating cloud-init configuration..."
    
    # Create user-data for cloud-init
    cat > user-data << 'EOF'
#cloud-config
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
EOF

    # Create meta-data
    cat > meta-data << EOF
instance-id: $VM_NAME
local-hostname: $VM_NAME
EOF

    # Create cloud-init ISO
    if command -v genisoimage &> /dev/null; then
        genisoimage -output cloud-init.iso -volid cidata -joliet -rock user-data meta-data
    elif command -v mkisofs &> /dev/null; then
        mkisofs -output cloud-init.iso -volid cidata -joliet -rock user-data meta-data
    else
        print_warning "Neither genisoimage nor mkisofs found. Cloud-init ISO not created."
        print_warning "You'll need to configure the VM manually during installation."
    fi
}

# Generate SSH key if it doesn't exist
setup_ssh_key() {
    SSH_KEY_PATH="$HOME/.ssh/id_rsa"
    if [ ! -f "$SSH_KEY_PATH" ]; then
        print_status "Generating SSH key pair..."
        ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N ""
    fi
    
    # Update cloud-init with actual SSH key
    if [ -f "$SSH_KEY_PATH.pub" ]; then
        SSH_KEY=$(cat "$SSH_KEY_PATH.pub")
        sed -i "s|ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7.*|$SSH_KEY|" user-data
        
        # Recreate cloud-init ISO with updated key
        if command -v genisoimage &> /dev/null || command -v mkisofs &> /dev/null; then
            rm -f cloud-init.iso
            if command -v genisoimage &> /dev/null; then
                genisoimage -output cloud-init.iso -volid cidata -joliet -rock user-data meta-data
            else
                mkisofs -output cloud-init.iso -volid cidata -joliet -rock user-data meta-data
            fi
        fi
    fi
}

# Create startup script
create_startup_script() {
    print_status "Creating VM startup script..."
    
    cat > start-vm.sh << EOF
#!/bin/bash

# Start the Ubuntu VM
VM_DIR="$VM_DIR"
VM_NAME="$VM_NAME"
RAM="$RAM"
CPUS="$CPUS"
SSH_PORT="$SSH_PORT"

cd "\$VM_DIR"

# Check if VM is already running
if pgrep -f "qemu.*\$VM_NAME" > /dev/null; then
    echo "VM is already running!"
    echo "SSH into it with: ssh -p $SSH_PORT ubuntu@localhost"
    exit 1
fi

echo "Starting Ubuntu VM..."
echo "SSH will be available on port $SSH_PORT"
echo "Default login: ubuntu/ubuntu"
echo ""

# Start QEMU
qemu-system-x86_64 \\
    -name "\$VM_NAME" \\
    -machine type=pc,accel=kvm \\
    -cpu host \\
    -smp "\$CPUS" \\
    -m "\$RAM" \\
    -drive file="\$VM_NAME.qcow2",format=qcow2,if=virtio \\
    -drive file=cloud-init.iso,format=raw,if=virtio,readonly=on \\
    -netdev user,id=net0,hostfwd=tcp::\$SSH_PORT-:22 \\
    -device virtio-net-pci,netdev=net0 \\
    -display none \\
    -daemonize \\
    -pidfile "\$VM_NAME.pid"

# Wait a moment for the VM to start
sleep 2

if [ -f "\$VM_NAME.pid" ]; then
    echo "VM started successfully!"
    echo "PID: \$(cat \$VM_NAME.pid)"
    echo ""
    echo "To SSH into the VM:"
    echo "  ssh -p $SSH_PORT ubuntu@localhost"
    echo ""
    echo "To stop the VM:"
    echo "  ./stop-vm.sh"
else
    echo "Failed to start VM"
    exit 1
fi
EOF

    chmod +x start-vm.sh
}

# Create stop script
create_stop_script() {
    print_status "Creating VM stop script..."
    
    cat > stop-vm.sh << EOF
#!/bin/bash

VM_DIR="$VM_DIR"
VM_NAME="$VM_NAME"

cd "\$VM_DIR"

if [ -f "\$VM_NAME.pid" ]; then
    PID=\$(cat "\$VM_NAME.pid")
    if kill "\$PID" 2>/dev/null; then
        echo "VM stopped successfully"
        rm -f "\$VM_NAME.pid"
    else
        echo "Failed to stop VM with PID \$PID"
        echo "Trying to kill all QEMU processes for this VM..."
        pkill -f "qemu.*\$VM_NAME"
        rm -f "\$VM_NAME.pid"
    fi
else
    echo "VM PID file not found. Trying to kill all QEMU processes for this VM..."
    pkill -f "qemu.*\$VM_NAME"
fi
EOF

    chmod +x stop-vm.sh
}



# Create status script
create_status_script() {
    print_status "Creating VM status script..."
    
    cat > status-vm.sh << EOF
#!/bin/bash

VM_DIR="$VM_DIR"
VM_NAME="$VM_NAME"
SSH_PORT="$SSH_PORT"

cd "\$VM_DIR"

echo "=== VM Status ==="
if [ -f "\$VM_NAME.pid" ]; then
    PID=\$(cat "\$VM_NAME.pid")
    if kill -0 "\$PID" 2>/dev/null; then
        echo "Status: RUNNING (PID: \$PID)"
        echo "SSH: ssh -p $SSH_PORT ubuntu@localhost"
        echo ""
        echo "Testing SSH connection..."
        timeout 5 ssh -p $SSH_PORT -o ConnectTimeout=3 -o BatchMode=yes ubuntu@localhost echo "SSH OK" 2>/dev/null
        if [ \$? -eq 0 ]; then
            echo "SSH: ACCESSIBLE"
        else
            echo "SSH: NOT READY (VM may still be booting)"
        fi
    else
        echo "Status: STOPPED (stale PID file)"
        rm -f "\$VM_NAME.pid"
    fi
else
    if pgrep -f "qemu.*\$VM_NAME" > /dev/null; then
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
EOF

    chmod +x status-vm.sh
}

# Main setup function
main() {
    print_status "Setting up QEMU Ubuntu VM..."
    
    check_qemu
    setup_directories
    download_cloud_image
    create_disk
    create_cloud_init
    setup_ssh_key
    create_startup_script
    create_stop_script
    create_status_script
    
    print_status "VM setup completed!"
    echo ""
    echo "VM Directory: $VM_DIR"
    echo "SSH Port: $SSH_PORT"
    echo ""
    echo "✅ HEADLESS SETUP: Uses Ubuntu cloud image with automated cloud-init"
    echo ""
    echo "Next steps:"
    echo "1. cd $VM_DIR"
    echo "2. ./start-vm.sh     # Start the VM"
    echo ""
    echo "3. SSH into VM:"
    echo "   ssh -p $SSH_PORT -o PreferredAuthentications=password ubuntu@localhost"
    echo "   Password: ubuntu"
    echo ""
    echo "4. Management commands:"
    echo "   ./status-vm.sh    # Check VM status and SSH connectivity"
    echo "   ./stop-vm.sh      # Stop the VM"
    echo ""
    print_warning "Note: Use direct image modification with virt-customize for reliable setup."
    print_warning "Cloud-init may not work reliably with standard Ubuntu Server ISO."
}

# Run main function only if not being sourced for testing
if [[ "${BASH_SOURCE[0]}" == "${0}" ]] && [[ "${TESTING:-}" != "true" ]]; then
    main "$@"
fi