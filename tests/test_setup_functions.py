"""
Tests for setup functions in setup-ubuntu-vm.py
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
import subprocess
import urllib.error

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestCheckQemu:
    """Test the check_qemu function"""
    
    def test_check_qemu_installed(self, mock_shutil_which):
        """Test when QEMU is installed"""
        from setup_ubuntu_vm import check_qemu
        mock_shutil_which.return_value = "/usr/bin/qemu-system-x86_64"
        
        # Should not raise any exception
        check_qemu()
        mock_shutil_which.assert_called_once_with("qemu-system-x86_64")
    
    def test_check_qemu_not_installed(self, mock_shutil_which):
        """Test when QEMU is not installed"""
        from setup_ubuntu_vm import check_qemu
        mock_shutil_which.return_value = None
        
        with pytest.raises(SystemExit) as excinfo:
            check_qemu()
        
        assert excinfo.value.code == 1
        mock_shutil_which.assert_called_once_with("qemu-system-x86_64")

class TestSetupDirectories:
    """Test the setup_directories function"""
    
    def test_setup_directories_creates_vm_dir(self, temp_dir, mock_os_operations):
        """Test that setup_directories creates VM directory and changes to it"""
        from setup_ubuntu_vm import setup_directories, VM_DIR
        
        with patch('setup_ubuntu_vm.VM_DIR', temp_dir / "vms" / "ubuntu-vm"):
            setup_directories()
            
            # Check that directory was created
            assert (temp_dir / "vms" / "ubuntu-vm").exists()
            # Check that we changed to the directory
            mock_os_operations['chdir'].assert_called_once()

class TestDownloadCloudImage:
    """Test the download_cloud_image function"""
    
    def test_download_cloud_image_success(self, mock_vm_dir, mock_urllib_request):
        """Test successful download of cloud image"""
        from setup_ubuntu_vm import download_cloud_image, UBUNTU_CLOUD_IMG, UBUNTU_CLOUD_URL
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir):
            download_cloud_image()
            
            mock_urllib_request.assert_called_once_with(
                UBUNTU_CLOUD_URL, 
                mock_vm_dir / UBUNTU_CLOUD_IMG
            )
    
    def test_download_cloud_image_already_exists(self, mock_vm_dir, mock_urllib_request):
        """Test when cloud image already exists"""
        from setup_ubuntu_vm import download_cloud_image, UBUNTU_CLOUD_IMG
        
        # Create the file to simulate it already existing
        cloud_img_path = mock_vm_dir / UBUNTU_CLOUD_IMG
        cloud_img_path.touch()
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir):
            download_cloud_image()
            
            # Should not attempt to download
            mock_urllib_request.assert_not_called()
    
    def test_download_cloud_image_failure(self, mock_vm_dir, mock_urllib_request):
        """Test download failure"""
        from setup_ubuntu_vm import download_cloud_image
        
        mock_urllib_request.side_effect = urllib.error.URLError("Network error")
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir):
            with pytest.raises(SystemExit) as excinfo:
                download_cloud_image()
            
            assert excinfo.value.code == 1

class TestCreateDisk:
    """Test the create_disk function"""
    
    def test_create_disk_success(self, mock_vm_dir, mock_subprocess):
        """Test successful disk creation"""
        from setup_ubuntu_vm import create_disk, VM_NAME, DISK_SIZE, UBUNTU_CLOUD_IMG
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir):
            create_disk()
            
            # Check that qemu-img commands were called
            assert mock_subprocess.call_count == 2
            
            # Check convert command
            convert_call = mock_subprocess.call_args_list[0]
            assert convert_call[0][0][:2] == ["qemu-img", "convert"]
            
            # Check resize command
            resize_call = mock_subprocess.call_args_list[1]
            assert resize_call[0][0][:3] == ["qemu-img", "resize", f"{VM_NAME}.qcow2"]
    
    def test_create_disk_already_exists(self, mock_vm_dir, mock_subprocess):
        """Test when disk already exists"""
        from setup_ubuntu_vm import create_disk, VM_NAME
        
        # Create the disk file to simulate it already existing
        vm_disk = mock_vm_dir / f"{VM_NAME}.qcow2"
        vm_disk.touch()
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir):
            create_disk()
            
            # Should not call qemu-img commands
            mock_subprocess.assert_not_called()
    
    def test_create_disk_failure(self, mock_vm_dir, mock_subprocess):
        """Test disk creation failure"""
        from setup_ubuntu_vm import create_disk
        
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "qemu-img")
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir):
            with pytest.raises(SystemExit) as excinfo:
                create_disk()
            
            assert excinfo.value.code == 1

class TestCreateCloudInit:
    """Test the create_cloud_init function"""
    
    def test_create_cloud_init_with_genisoimage(self, mock_vm_dir, mock_subprocess, mock_shutil_which):
        """Test cloud-init creation with genisoimage"""
        from setup_ubuntu_vm import create_cloud_init
        
        mock_shutil_which.side_effect = lambda tool: "/usr/bin/genisoimage" if tool == "genisoimage" else None
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir), \
             patch('builtins.open', mock_open()) as mock_file:
            create_cloud_init()
            
            # Check that files were written
            assert mock_file.call_count >= 2  # user-data and meta-data
            
            # Check that genisoimage was called
            mock_subprocess.assert_called_once()
            args = mock_subprocess.call_args[0][0]
            assert args[0] == "genisoimage"
            assert "cloud-init.iso" in args
    
    def test_create_cloud_init_with_mkisofs(self, mock_vm_dir, mock_subprocess, mock_shutil_which):
        """Test cloud-init creation with mkisofs as fallback"""
        from setup_ubuntu_vm import create_cloud_init
        
        # genisoimage not available, mkisofs available
        mock_shutil_which.side_effect = lambda tool: "/usr/bin/mkisofs" if tool == "mkisofs" else None
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir), \
             patch('builtins.open', mock_open()) as mock_file:
            create_cloud_init()
            
            # Check that mkisofs was called
            mock_subprocess.assert_called_once()
            args = mock_subprocess.call_args[0][0]
            assert args[0] == "mkisofs"
    
    def test_create_cloud_init_no_tools(self, mock_vm_dir, mock_subprocess, mock_shutil_which):
        """Test when neither genisoimage nor mkisofs are available"""
        from setup_ubuntu_vm import create_cloud_init
        
        mock_shutil_which.return_value = None
        
        with patch('setup_ubuntu_vm.VM_DIR', mock_vm_dir), \
             patch('builtins.open', mock_open()) as mock_file:
            # Should not raise exception, just print warning
            create_cloud_init()
            
            # Should not call subprocess
            mock_subprocess.assert_not_called()

class TestSetupSshKey:
    """Test the setup_ssh_key function"""
    
    def test_setup_ssh_key_generates_new_key(self, mock_subprocess):
        """Test SSH key generation when key doesn't exist"""
        from setup_ubuntu_vm import setup_ssh_key
        
        mock_ssh_key_path = Mock()
        mock_ssh_pub_path = Mock()
        mock_ssh_key_path.exists.return_value = False
        mock_ssh_pub_path.exists.return_value = True
        
        mock_file_content = "ssh-rsa AAAAB3NzaC1yc2EAAA... test@example.com"
        
        with patch('pathlib.Path.home') as mock_home, \
             patch('builtins.open', mock_open(read_data=mock_file_content)) as mock_file:
            
            mock_home.return_value = Path("/tmp")
            mock_ssh_key_path.with_suffix.return_value = mock_ssh_pub_path
            
            with patch.object(Path, '__truediv__', return_value=mock_ssh_key_path):
                setup_ssh_key()
            
            # Check that ssh-keygen was called
            mock_subprocess.assert_called()
            args = mock_subprocess.call_args[0][0]
            assert args[0] == "ssh-keygen"
    
    def test_setup_ssh_key_uses_existing_key(self, mock_subprocess):
        """Test when SSH key already exists"""
        from setup_ubuntu_vm import setup_ssh_key
        
        mock_ssh_key_path = Mock()
        mock_ssh_pub_path = Mock()
        mock_ssh_key_path.exists.return_value = True
        mock_ssh_pub_path.exists.return_value = True
        
        mock_file_content = "ssh-rsa AAAAB3NzaC1yc2EAAA... test@example.com"
        
        with patch('pathlib.Path.home') as mock_home, \
             patch('builtins.open', mock_open(read_data=mock_file_content)) as mock_file:
            
            mock_home.return_value = Path("/tmp")
            mock_ssh_key_path.with_suffix.return_value = mock_ssh_pub_path
            
            with patch.object(Path, '__truediv__', return_value=mock_ssh_key_path):
                setup_ssh_key()
            
            # Should not generate new key
            ssh_keygen_calls = [call for call in mock_subprocess.call_args_list 
                              if call[0][0][0] == "ssh-keygen"]
            assert len(ssh_keygen_calls) == 0