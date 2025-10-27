"""
Pytest configuration and fixtures for VM setup tests
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import os
import sys

# Add the parent directory to sys.path so we can import the setup script
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def mock_vm_dir(temp_dir):
    """Create a mock VM directory structure"""
    vm_dir = temp_dir / "vms" / "ubuntu-vm"
    vm_dir.mkdir(parents=True)
    return vm_dir

@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        yield mock_run

@pytest.fixture
def mock_shutil_which():
    """Mock shutil.which to control tool availability"""
    with patch('shutil.which') as mock_which:
        # By default, assume tools are available
        mock_which.return_value = "/usr/bin/qemu-system-x86_64"
        yield mock_which

@pytest.fixture
def mock_urllib_request():
    """Mock urllib.request for download operations"""
    with patch('urllib.request.urlretrieve') as mock_download:
        yield mock_download

@pytest.fixture
def mock_os_operations():
    """Mock various OS operations"""
    with patch('os.chdir') as mock_chdir, \
         patch('os.chmod') as mock_chmod, \
         patch('os.kill') as mock_kill:
        yield {
            'chdir': mock_chdir,
            'chmod': mock_chmod,
            'kill': mock_kill
        }

@pytest.fixture
def mock_file_operations():
    """Mock file operations"""
    with patch('builtins.open', create=True) as mock_open:
        yield mock_open

@pytest.fixture
def setup_test_environment(temp_dir, mock_subprocess, mock_shutil_which, mock_urllib_request, mock_os_operations):
    """Setup a complete test environment with all necessary mocks"""
    # Change the working directory to temp_dir for tests
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    yield {
        'temp_dir': temp_dir,
        'subprocess': mock_subprocess,
        'shutil_which': mock_shutil_which,
        'urllib_request': mock_urllib_request,
        'os_ops': mock_os_operations
    }
    
    # Restore original working directory
    os.chdir(original_cwd)