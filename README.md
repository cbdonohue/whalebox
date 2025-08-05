# QEMU Ubuntu VM Setup

A comprehensive bash script for creating and managing headless Ubuntu virtual machines using QEMU with automated cloud-init configuration.

## 🚀 Features

- **Automated VM Creation**: One-command setup of Ubuntu 22.04 LTS VMs
- **Headless Operation**: No GUI required - perfect for servers and remote environments
- **SSH Access**: Pre-configured SSH access with key-based and password authentication
- **Cloud-Init Integration**: Automated user setup and package installation
- **VM Management**: Easy start, stop, and status monitoring scripts
- **Customizable Configuration**: Adjustable RAM, CPU, disk size, and SSH port
- **Security Ready**: UFW firewall enabled with SSH access configured

## 📋 Prerequisites

### Required Software
- **QEMU**: Virtualization platform
- **SSH**: For connecting to the VM
- **wget**: For downloading Ubuntu cloud images
- **genisoimage** or **mkisofs**: For creating cloud-init ISO (optional but recommended)

### Installation Commands

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install qemu-system-x86 qemu-utils genisoimage openssh-client wget
```

**Fedora:**
```bash
sudo dnf install qemu-system-x86 qemu-img genisoimage openssh-clients wget
```

**Arch Linux:**
```bash
sudo pacman -S qemu-system-x86 qemu-img cdrtools openssh wget
```

## 🛠️ Quick Start

1. **Clone or download the script:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Make the script executable:**
   ```bash
   chmod +x setup-ubuntu-vm.sh
   ```

3. **Run the setup:**
   ```bash
   ./setup-ubuntu-vm.sh
   ```

4. **Start your VM:**
   ```bash
   cd vms/ubuntu-vm
   ./start-vm.sh
   ```

5. **SSH into your VM:**
   ```bash
   ssh -p 2222 ubuntu@localhost
   ```
   Default password: `ubuntu`

## 📁 Project Structure

After running the setup script, the following structure will be created:

```
project-root/
├── setup-ubuntu-vm.sh          # Main setup script
├── vms/
│   └── ubuntu-vm/
│       ├── jammy-server-cloudimg-amd64.img  # Downloaded Ubuntu cloud image
│       ├── ubuntu-vm.qcow2     # VM disk file
│       ├── cloud-init.iso      # Cloud-init configuration
│       ├── user-data           # Cloud-init user configuration
│       ├── meta-data           # Cloud-init metadata
│       ├── start-vm.sh         # VM startup script
│       ├── stop-vm.sh          # VM shutdown script
│       └── status-vm.sh        # VM status checker
```

## ⚙️ Configuration

The script uses the following default configuration (modifiable at the top of `setup-ubuntu-vm.sh`):

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `VM_NAME` | `ubuntu-vm` | Name of the virtual machine |
| `DISK_SIZE` | `20G` | Virtual disk size |
| `RAM` | `2G` | Memory allocation |
| `CPUS` | `2` | Number of CPU cores |
| `SSH_PORT` | `2222` | Host port for SSH forwarding |

To customize these values, edit the configuration section at the top of `setup-ubuntu-vm.sh` before running it.

## 🎮 VM Management

### Starting the VM
```bash
cd vms/ubuntu-vm
./start-vm.sh
```

### Checking VM Status
```bash
./status-vm.sh
```

### Stopping the VM
```bash
./stop-vm.sh
```

### SSH Access
```bash
# Password authentication (default password: ubuntu)
ssh -p 2222 ubuntu@localhost

# Key-based authentication (if SSH keys are set up)
ssh -p 2222 -i ~/.ssh/id_rsa ubuntu@localhost
```

## 🔧 Advanced Usage

### Custom SSH Configuration

The script automatically generates SSH keys if they don't exist. To use your own SSH key:

1. Ensure your public key exists at `~/.ssh/id_rsa.pub`
2. Run the setup script - it will automatically include your key in the cloud-init configuration

### Modifying Cloud-Init Configuration

The `user-data` file contains the cloud-init configuration. You can modify it to:
- Install additional packages
- Configure services
- Set up custom users
- Run custom commands on first boot

After modifying `user-data`, recreate the cloud-init ISO:
```bash
cd vms/ubuntu-vm
genisoimage -output cloud-init.iso -volid cidata -joliet -rock user-data meta-data
```

### Multiple VMs

To create multiple VMs, modify the `VM_NAME` variable in the script before running it:
```bash
# Edit setup-ubuntu-vm.sh and change VM_NAME
VM_NAME="my-dev-vm"
```

## 🔒 Security Features

- **User Account**: Creates `ubuntu` user with sudo privileges
- **SSH Configuration**: Enables both key-based and password authentication
- **Firewall**: UFW firewall enabled with SSH access allowed
- **Password**: Default password is `ubuntu` (change after first login)

### Recommended Security Steps

After first login, consider:
1. Changing the default password: `passwd`
2. Disabling password authentication in favor of keys only
3. Configuring additional firewall rules as needed
4. Setting up fail2ban for SSH protection

## 🐛 Troubleshooting

### VM Won't Start
- Check if QEMU is properly installed
- Verify KVM acceleration is available: `kvm-ok` (install `cpu-checker` package)
- Ensure sufficient disk space for the VM
- Check if the SSH port is already in use: `netstat -tlnp | grep 2222`

### SSH Connection Issues
- Wait 60-90 seconds after starting the VM for cloud-init to complete
- Check VM status: `./status-vm.sh`
- Verify the VM is running: `ps aux | grep qemu`
- Test SSH connectivity: `telnet localhost 2222`

### Cloud-Init Problems
- Check cloud-init logs inside the VM: `sudo tail -f /var/log/cloud-init-output.log`
- Verify cloud-init ISO was created successfully
- Ensure genisoimage or mkisofs is installed

### Performance Issues
- Increase RAM allocation in the configuration
- Ensure KVM acceleration is enabled
- Check host system resources

## 🔄 VM Lifecycle

1. **Setup**: Run `setup-ubuntu-vm.sh` once to create the VM
2. **Start**: Use `start-vm.sh` to boot the VM
3. **Connect**: SSH into the VM for development/administration
4. **Stop**: Use `stop-vm.sh` to gracefully shutdown
5. **Status**: Check `status-vm.sh` anytime to see current state

## 📝 Default VM Configuration

The created Ubuntu VM includes:
- **OS**: Ubuntu 22.04 LTS (Jammy Jellyfish)
- **User**: `ubuntu` with sudo privileges
- **Packages**: openssh-server, curl, wget, git, htop, vim, net-tools
- **Services**: SSH enabled and started
- **Firewall**: UFW enabled with SSH access
- **Network**: NAT with SSH port forwarding

## 🤝 Contributing

Feel free to submit issues and enhancement requests! Common improvements include:
- Additional cloud-init templates
- Support for other Linux distributions
- GUI/VNC support options
- Automated backup scripts
- Network bridge configuration

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## ⚠️ Important Notes

- This script creates **headless VMs** (no display output)
- Uses Ubuntu cloud images for faster, automated setup
- Requires KVM acceleration for optimal performance
- Default credentials are `ubuntu/ubuntu` - change after first login
- VMs are stored in the `vms/` directory (excluded from git)

## 🔗 Useful Resources

- [QEMU Documentation](https://www.qemu.org/docs/master/)
- [Ubuntu Cloud Images](https://cloud-images.ubuntu.com/)
- [Cloud-Init Documentation](https://cloudinit.readthedocs.io/)
- [SSH Key Management](https://www.ssh.com/academy/ssh/keygen)