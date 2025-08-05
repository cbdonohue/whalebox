# QEMU Runner

A simple, open-source command line utility for running QEMU virtual machines with ease.

## Features

- **Simple CLI Interface**: Easy-to-use command line interface for common VM operations
- **Flexible Configuration**: Support for various VM configurations (memory, CPU, storage, network)
- **Multiple Commands**: Run VMs, create disk images, and list machine types
- **Cross-Platform**: Works on Linux and macOS systems with QEMU installed
- **KVM Acceleration**: Automatic KVM acceleration when available
- **Multiple Display Options**: Support for SDL, VNC, and other display types

## Installation

### Prerequisites

First, ensure QEMU is installed on your system:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install qemu-system-x86 qemu-utils
```

**CentOS/RHEL/Fedora:**
```bash
sudo dnf install qemu-system-x86 qemu-img
# or for older versions:
sudo yum install qemu-system-x86 qemu-img
```

**macOS (with Homebrew):**
```bash
brew install qemu
```

### Install QEMU Runner

**Option 1: Direct execution**
```bash
git clone <repository-url>
cd qemu-runner
chmod +x qemu_runner.py
./qemu_runner.py --help
```

**Option 2: Install as Python package**
```bash
git clone <repository-url>
cd qemu-runner
pip install .
qemu-runner --help
```

**Option 3: Development installation**
```bash
git clone <repository-url>
cd qemu-runner
pip install -e .
```

## Usage

### Basic Examples

**Run a VM with existing disk:**
```bash
./qemu_runner.py --disk vm.qcow2 --memory 2G --cores 2
```

**Boot from ISO with network:**
```bash
./qemu_runner.py --cdrom ubuntu-20.04.iso --memory 4G --boot d --network
```

**Create a new disk image:**
```bash
./qemu_runner.py create-disk --path myvm.qcow2 --size 20G
```

**List available machine types:**
```bash
./qemu_runner.py list-machines
```

### Command Reference

#### Main Command: `run` (default)

```bash
./qemu_runner.py [run] [OPTIONS]
```

**Storage Options:**
- `--disk, -d PATH`: Path to disk image file
- `--cdrom, -c PATH`: Path to CD-ROM/ISO image

**System Configuration:**
- `--memory, -m SIZE`: Amount of RAM (default: 1G)
- `--cores, -s NUM`: Number of CPU cores (default: 1)
- `--boot, -b ORDER`: Boot order (c=disk, d=cdrom, n=network)

**Display Options:**
- `--vnc DISPLAY`: Enable VNC display (e.g., :1)
- `--display TYPE`: Display type (sdl, gtk, vnc, none)
- **Default**: Headless mode (`none`) with serial console output to terminal

**Network Options:**
- `--network`: Enable network (NAT)
- `--network-device TYPE`: Network device type (default: e1000)

**Performance Options:**
- `--enable-kvm`: Enable KVM acceleration (default: true)

**Advanced Options:**
- `--qemu-args ARGS`: Additional QEMU arguments
- `--dry-run`: Show command that would be executed
- `--verbose, -v`: Verbose output

#### Disk Creation: `create-disk`

```bash
./qemu_runner.py create-disk --path PATH --size SIZE [--format FORMAT]
```

- `--path, -p PATH`: Path for the new disk image
- `--size, -s SIZE`: Size of the disk (e.g., 20G, 500M)
- `--format, -f FORMAT`: Disk format (default: qcow2)

#### List Machines: `list-machines`

```bash
./qemu_runner.py list-machines
```

### Complete Example Workflow

1. **Create a new VM disk:**
   ```bash
   ./qemu_runner.py create-disk --path ubuntu-vm.qcow2 --size 25G
   ```

2. **Install OS from ISO:**
   ```bash
   ./qemu_runner.py --cdrom ubuntu-20.04.iso --disk ubuntu-vm.qcow2 --memory 4G --cores 2 --boot d --network
   ```

3. **Boot from installed OS:**
   ```bash
   ./qemu_runner.py --disk ubuntu-vm.qcow2 --memory 4G --cores 2 --network
   ```

## Configuration Tips

### Memory Sizing
- Use suffixes: `512M`, `1G`, `2G`, `4G`
- Recommended: At least 1G for modern Linux, 2G+ for desktop environments

### Disk Formats
- **qcow2**: QEMU's native format, supports snapshots and compression
- **raw**: Raw disk image, better performance but larger size
- **vdi**: VirtualBox format
- **vmdk**: VMware format

### Boot Orders
- `c`: Boot from hard disk
- `d`: Boot from CD-ROM
- `n`: Boot from network (PXE)
- `a`: Boot from floppy

### Network Configuration
The `--network` flag enables basic NAT networking, allowing the VM to access the internet and the host can access VM services through port forwarding.

## Troubleshooting

### Common Issues

**QEMU not found:**
```
Error: No QEMU binary found. Please install QEMU.
```
Solution: Install QEMU using your system's package manager.

**KVM acceleration not available:**
If KVM is not available, the VM will run with software emulation (slower).
Check: `ls -la /dev/kvm`

**Permission denied on /dev/kvm:**
```bash
sudo usermod -a -G kvm $USER
# Then log out and log back in
```

**Display issues:**
If SDL display doesn't work, try:
```bash
./qemu_runner.py --vnc :1 --disk vm.qcow2
# Then connect with VNC viewer to localhost:5901
```

## Contributing

This is an open-source project. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- QEMU development team for the excellent virtualization platform
- The open-source community for inspiration and feedback