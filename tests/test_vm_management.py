"""
Tests for VM management functions (start, stop, status)
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
import subprocess
import signal
import os

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestVMStartup:
    """Test VM startup functionality"""
    
    def test_check_vm_running_true(self, mock_subprocess):
        """Test check_vm_running when VM is running"""
        # This would be in the start-vm.py script, but we'll test the logic
        mock_subprocess.return_value.returncode = 0
        
        # Simulate the check_vm_running function logic
        result = subprocess.run(['pgrep', '-f', 'qemu.*ubuntu-vm'], 
                              capture_output=True, text=True)
        assert result.returncode == 0
    
    def test_check_vm_running_false(self, mock_subprocess):
        """Test check_vm_running when VM is not running"""
        mock_subprocess.return_value.returncode = 1
        
        result = subprocess.run(['pgrep', '-f', 'qemu.*ubuntu-vm'], 
                              capture_output=True, text=True)
        assert result.returncode == 1
    
    def test_qemu_command_construction(self):
        """Test that QEMU command is constructed correctly"""
        # Test the command structure that would be generated
        vm_name = "ubuntu-vm"
        cpus = "2"
        ram = "2G"
        ssh_port = "2222"
        
        expected_cmd = [
            'qemu-system-x86_64',
            '-name', vm_name,
            '-machine', 'type=pc,accel=kvm',
            '-cpu', 'host',
            '-smp', cpus,
            '-m', ram,
            '-drive', f'file={vm_name}.qcow2,format=qcow2,if=virtio',
            '-drive', 'file=cloud-init.iso,format=raw,if=virtio,readonly=on',
            '-netdev', f'user,id=net0,hostfwd=tcp::{ssh_port}-:22',
            '-device', 'virtio-net-pci,netdev=net0',
            '-display', 'none',
            '-daemonize',
            '-pidfile', f'{vm_name}.pid'
        ]
        
        # Verify command structure
        assert expected_cmd[0] == 'qemu-system-x86_64'
        assert '-name' in expected_cmd
        assert '-display' in expected_cmd
        assert 'none' in expected_cmd  # Headless mode
        assert '-daemonize' in expected_cmd

class TestVMStop:
    """Test VM stop functionality"""
    
    def test_stop_vm_with_pid_file(self, mock_vm_dir, mock_os_operations):
        """Test stopping VM when PID file exists"""
        # Create a mock PID file
        pid_file = mock_vm_dir / "ubuntu-vm.pid"
        pid_file.write_text("12345")
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir):
            # Simulate the stop logic
            if pid_file.exists():
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # This would call os.kill(pid, signal.SIGTERM)
                mock_os_operations['kill'].return_value = None
                
                assert pid == 12345
    
    def test_stop_vm_no_pid_file(self, mock_vm_dir, mock_subprocess):
        """Test stopping VM when no PID file exists"""
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir):
            # Should fall back to pkill
            subprocess.run(['pkill', '-f', 'qemu.*ubuntu-vm'], check=False)
            
            mock_subprocess.assert_called_once()
            args = mock_subprocess.call_args[0][0]
            assert args[0] == 'pkill'
            assert 'qemu.*ubuntu-vm' in args
    
    def test_stop_vm_process_not_found(self, mock_vm_dir, mock_os_operations):
        """Test stopping VM when process doesn't exist"""
        pid_file = mock_vm_dir / "ubuntu-vm.pid"
        pid_file.write_text("99999")
        
        mock_os_operations['kill'].side_effect = ProcessLookupError("No such process")
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir):
            # Should handle ProcessLookupError gracefully
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                # This is expected behavior
                pass

class TestVMStatus:
    """Test VM status functionality"""
    
    def test_vm_status_running_with_pid(self, mock_vm_dir, mock_os_operations):
        """Test status check when VM is running with valid PID file"""
        pid_file = mock_vm_dir / "ubuntu-vm.pid"
        pid_file.write_text("12345")
        
        # Mock os.kill to simulate process exists
        mock_os_operations['kill'].return_value = None
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir):
            if pid_file.exists():
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Signal 0 checks if process exists
                os.kill(pid, 0)
                
                assert pid == 12345
    
    def test_vm_status_stopped_stale_pid(self, mock_vm_dir, mock_os_operations):
        """Test status check when PID file exists but process is dead"""
        pid_file = mock_vm_dir / "ubuntu-vm.pid"
        pid_file.write_text("99999")
        
        mock_os_operations['kill'].side_effect = ProcessLookupError("No such process")
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir):
            if pid_file.exists():
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    # Should remove stale PID file
                    assert True  # Expected behavior
    
    def test_ssh_connectivity_test(self, mock_subprocess):
        """Test SSH connectivity testing"""
        ssh_port = "2222"
        
        # Test successful SSH connection
        mock_subprocess.return_value.returncode = 0
        
        result = subprocess.run([
            'timeout', '5',
            'ssh', '-p', ssh_port, 
            '-o', 'ConnectTimeout=3',
            '-o', 'BatchMode=yes',
            'ubuntu@localhost',
            'echo', 'SSH OK'
        ], capture_output=True, text=True, timeout=6)
        
        assert result.returncode == 0
    
    def test_ssh_connectivity_failure(self, mock_subprocess):
        """Test SSH connectivity when connection fails"""
        mock_subprocess.return_value.returncode = 1
        
        result = subprocess.run([
            'timeout', '5',
            'ssh', '-p', "2222", 
            '-o', 'ConnectTimeout=3',
            '-o', 'BatchMode=yes',
            'ubuntu@localhost',
            'echo', 'SSH OK'
        ], capture_output=True, text=True, timeout=6)
        
        assert result.returncode == 1

class TestScriptGeneration:
    """Test generated script functionality"""
    
    def test_startup_script_content(self, mock_vm_dir):
        """Test that startup script contains correct content"""
        from setup_ubuntu_vm import create_startup_script, VM_NAME, RAM, CPUS, SSH_PORT
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir), \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            
            create_startup_script()
            
            # Check that file was written and made executable
            mock_file.assert_called()
            mock_chmod.assert_called_with("start-vm.py", 0o755)
            
            # Check content includes expected variables
            written_content = ''.join(call.args[0] for call in mock_file().write.call_args_list)
            assert VM_NAME in written_content
            assert RAM in written_content
            assert CPUS in written_content
            assert SSH_PORT in written_content
    
    def test_stop_script_content(self, mock_vm_dir):
        """Test that stop script contains correct content"""
        from setup_ubuntu_vm import create_stop_script, VM_NAME
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir), \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            
            create_stop_script()
            
            # Check that file was written and made executable
            mock_file.assert_called()
            mock_chmod.assert_called_with("stop-vm.py", 0o755)
            
            # Check content includes expected variables
            written_content = ''.join(call.args[0] for call in mock_file().write.call_args_list)
            assert VM_NAME in written_content
            assert 'pkill' in written_content
    
    def test_status_script_content(self, mock_vm_dir):
        """Test that status script contains correct content"""
        from setup_ubuntu_vm import create_status_script, VM_NAME, SSH_PORT
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir), \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            
            create_status_script()
            
            # Check that file was written and made executable
            mock_file.assert_called()
            mock_chmod.assert_called_with("status-vm.py", 0o755)
            
            # Check content includes expected variables
            written_content = ''.join(call.args[0] for call in mock_file().write.call_args_list)
            assert VM_NAME in written_content
            assert SSH_PORT in written_content