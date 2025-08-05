# QEMU Ubuntu VM Setup

A comprehensive Python script for setting up headless Ubuntu VMs using QEMU with automated cloud-init configuration.

## 🚀 Features

- **Headless Setup**: No GUI required - perfect for servers and development environments
- **Automated Configuration**: Uses Ubuntu cloud images with cloud-init for zero-touch setup
- **SSH Ready**: Automatically configures SSH access with key-based and password authentication
- **Management Scripts**: Includes start, stop, and status scripts for easy VM lifecycle management
- **Resource Configurable**: Customizable CPU, RAM, and disk settings
- **Port Forwarding**: SSH access via localhost port forwarding

## 📋 Prerequisites

### Required Software

- **QEMU**: Virtual machine hypervisor
- **SSH client**: For connecting to the VM
- **ISO creation tools**: `genisoimage` or `mkisofs` (for cloud-init)

### Installation Commands

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install qemu-system-x86 qemu-utils genisoimage openssh-client
```

**Fedora/RHEL:**
```bash
sudo dnf install qemu-system-x86 qemu-img genisoimage openssh-clients
```

**Arch Linux:**
```bash
sudo pacman -S qemu-system-x86 qemu-img cdrtools openssh
```

## 🛠️ Installation

1. **Clone or download the script:**
   ```bash
   wget https://raw.githubusercontent.com/your-repo/setup-ubuntu-vm.py
   chmod +x setup-ubuntu-vm.py
   ```

2. **Run the setup:**
   ```bash
   ./setup-ubuntu-vm.py
   ```

## 📁 Directory Structure

After running the setup, the following structure is created:

```
vms/
└── ubuntu-vm/
    ├── jammy-server-cloudimg-amd64.img    # Downloaded Ubuntu cloud image
    ├── ubuntu-vm.qcow2                    # VM disk file
    ├── cloud-init.iso                     # Cloud-init configuration
    ├── user-data                          # Cloud-init user configuration
    ├── meta-data                          # Cloud-init metadata
    ├── start-vm.py                        # VM startup script
    ├── stop-vm.py                         # VM shutdown script
    ├── status-vm.py                       # VM status checker
    └── ubuntu-vm.pid                      # Process ID file (when running)
```

## 🔧 Configuration

### Default Settings

| Parameter | Value | Description |
|-----------|-------|-------------|
| VM Name | `ubuntu-vm` | Virtual machine identifier |
| Disk Size | `20G` | Virtual disk capacity |
| RAM | `2G` | Allocated memory |
| CPUs | `2` | Virtual CPU cores |
| SSH Port | `2222` | Host port for SSH forwarding |
| OS | Ubuntu 22.04 LTS | Cloud image version |

### Customization

Edit the configuration variables at the top of `setup-ubuntu-vm.py`:

```python
VM_NAME = "ubuntu-vm"
DISK_SIZE = "20G"
RAM = "2G"
CPUS = "2"
SSH_PORT = "2222"
```

## 🚀 Usage

### Initial Setup

1. **Run the setup script:**
   ```bash
   ./setup-ubuntu-vm.py
   ```

2. **Navigate to VM directory:**
   ```bash
   cd vms/ubuntu-vm
   ```

### VM Management

#### Start the VM
```bash
./start-vm.py
```

#### Check VM Status
```bash
./status-vm.py
```

#### Stop the VM
```bash
./stop-vm.py
```

### SSH Access

#### With Password (Default)
```bash
ssh -p 2222 ubuntu@localhost
# Password: ubuntu
```

#### With SSH Key (Recommended)
```bash
ssh -p 2222 ubuntu@localhost
# Uses the SSH key generated during setup
```

## 🔐 Security Configuration

### Default Credentials
- **Username**: `ubuntu`
- **Password**: `ubuntu`
- **Sudo**: Passwordless sudo enabled

### SSH Configuration
- **Key-based authentication**: Enabled (uses `~/.ssh/id_rsa`)
- **Password authentication**: Enabled
- **Root login**: Enabled
- **Port**: 2222 (forwarded to VM's port 22)

### Firewall
- UFW firewall enabled
- SSH access allowed

## 🔍 Troubleshooting

### VM Won't Start

1. **Check QEMU installation:**
   ```bash
   qemu-system-x86_64 --version
   ```

2. **Verify KVM acceleration:**
   ```bash
   lsmod | grep kvm
   ```

3. **Check available disk space:**
   ```bash
   df -h
   ```

### SSH Connection Issues

1. **Verify VM is running:**
   ```bash
   ./status-vm.py
   ```

2. **Check if SSH port is listening:**
   ```bash
   netstat -tlnp | grep 2222
   ```

3. **Test SSH with verbose output:**
   ```bash
   ssh -v -p 2222 ubuntu@localhost
   ```

### Cloud-init Problems

1. **Check cloud-init logs inside VM:**
   ```bash
   ssh -p 2222 ubuntu@localhost
   sudo tail -f /var/log/cloud-init-output.log
   ```

2. **Verify cloud-init ISO was created:**
   ```bash
   ls -la cloud-init.iso
   ```

### Performance Issues

1. **Enable KVM acceleration** (if available):
   ```bash
   # Check if KVM is available
   ls /dev/kvm
   
   # Add user to kvm group
   sudo usermod -a -G kvm $USER
   ```

2. **Increase VM resources** by editing configuration variables

## 🔄 VM Lifecycle

### Typical Workflow

1. **Setup** (one-time):
   ```bash
   ./setup-ubuntu-vm.py
   cd vms/ubuntu-vm
   ```

2. **Daily usage**:
   ```bash
   ./start-vm.py                    # Start VM
   ssh -p 2222 ubuntu@localhost    # Connect
   # ... do work ...
   ./stop-vm.py                     # Stop VM
   ```

3. **Maintenance**:
   ```bash
   ./status-vm.py                   # Check status
   ```

### VM States

- **STOPPED**: VM is not running
- **RUNNING**: VM is active and accessible
- **STARTING**: VM is booting (SSH may not be ready)

## 📦 What Gets Installed

### Host System
- VM directory structure
- Management scripts (start, stop, status)
- SSH key pair (if not exists)
- Cloud-init configuration

### VM System (via cloud-init)
- OpenSSH server
- Essential development tools:
  - `curl`, `wget`
  - `git`
  - `htop`
  - `vim`
  - `net-tools`
- UFW firewall (configured)
- User account with sudo access

## 🔧 Advanced Usage

### Custom Cloud-init Configuration

Edit `user-data` file to customize the VM setup:

```yaml
#cloud-config
packages:
  - docker.io
  - nodejs
  - npm

runcmd:
  - docker --version
  - node --version
```

### Multiple VMs

To create multiple VMs, modify the `VM_NAME` variable and run setup again:

```python
VM_NAME = "dev-vm"        # First VM
VM_NAME = "staging-vm"    # Second VM
```

### Resource Scaling

For different workloads:

```python
# Development VM
RAM = "4G"
CPUS = "4"
DISK_SIZE = "50G"

# Testing VM  
RAM = "1G"
CPUS = "1"
DISK_SIZE = "10G"
```

## 🐛 Common Issues

### Issue: "Permission denied" when starting VM
**Solution**: Add user to KVM group and re-login:
```bash
sudo usermod -a -G kvm $USER
newgrp kvm
```

### Issue: "Cloud-init ISO not created"
**Solution**: Install ISO creation tools:
```bash
sudo apt install genisoimage  # Ubuntu/Debian
sudo dnf install genisoimage  # Fedora
```

### Issue: SSH connection refused
**Solution**: Wait for VM to fully boot (30-60 seconds), then try again:
```bash
./status-vm.py  # Check if SSH is ready
```

### Issue: VM uses too much CPU
**Solution**: Reduce CPU count or check for runaway processes:
```bash
ssh -p 2222 ubuntu@localhost 'htop'
```

## 🔒 Security Considerations

### Default Security
- ⚠️ **Default password**: Change `ubuntu` password after first login
- ⚠️ **Root access**: Enabled for convenience, disable in production
- ✅ **Firewall**: UFW enabled with SSH allowed
- ✅ **SSH keys**: Automatically configured

### Hardening Recommendations

1. **Change default password:**
   ```bash
   ssh -p 2222 ubuntu@localhost
   passwd ubuntu
   ```

2. **Disable password authentication:**
   ```bash
   sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
   sudo systemctl restart ssh
   ```

3. **Disable root login:**
   ```bash
   sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
   sudo systemctl restart ssh
   ```

## 📊 System Requirements

### Minimum Requirements
- **CPU**: 2 cores (host)
- **RAM**: 4GB (host), 2GB allocated to VM
- **Disk**: 25GB free space
- **Network**: Internet connection for image download

### Recommended Requirements
- **CPU**: 4+ cores with KVM support
- **RAM**: 8GB+ (host)
- **Disk**: SSD with 50GB+ free space
- **Network**: Broadband connection

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Test your changes with a fresh VM setup
4. Submit a pull request

## 📞 Support

### Getting Help
1. Check the troubleshooting section above
2. Run `./status-vm.py` for diagnostic information
3. Check VM logs: `ssh -p 2222 ubuntu@localhost 'sudo journalctl -xe'`

### Reporting Issues
Include the following information:
- Host OS and version
- QEMU version (`qemu-system-x86_64 --version`)
- Error messages and logs
- Output of `./status-vm.py`

---

**Happy VM management! 🐧**