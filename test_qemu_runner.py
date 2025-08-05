#!/usr/bin/env python3
"""
Test suite for QEMU Runner
"""

import unittest
import unittest.mock as mock
import argparse
import sys
import os
import tempfile
from pathlib import Path
from io import StringIO

# Import the module to test
import qemu_runner


class TestQEMURunner(unittest.TestCase):
    """Test cases for the QEMURunner class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock subprocess.run to avoid actual system calls
        self.subprocess_patcher = mock.patch('qemu_runner.subprocess.run')
        self.mock_subprocess = self.subprocess_patcher.start()
        
        # Mock os.path.exists to control file existence checks
        self.exists_patcher = mock.patch('qemu_runner.os.path.exists')
        self.mock_exists = self.exists_patcher.start()
        
        # Mock open for KVM access check
        self.open_patcher = mock.patch('builtins.open', mock.mock_open())
        self.mock_open = self.open_patcher.start()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.subprocess_patcher.stop()
        self.exists_patcher.stop()
        self.open_patcher.stop()
    
    def test_find_qemu_binary_success(self):
        """Test successful QEMU binary detection"""
        # Mock successful 'which' command for qemu-system-x86_64
        self.mock_subprocess.return_value.returncode = 0
        
        runner = qemu_runner.QEMURunner()
        self.assertEqual(runner.qemu_binary, 'qemu-system-x86_64')
        
        # Verify 'which' was called
        self.mock_subprocess.assert_called_with(['which', 'qemu-system-x86_64'], capture_output=True)
    
    def test_find_qemu_binary_fallback(self):
        """Test QEMU binary detection with fallback"""
        # Mock first binary not found, second one found
        self.mock_subprocess.side_effect = [
            mock.Mock(returncode=1),  # qemu-system-x86_64 not found
            mock.Mock(returncode=0),  # qemu-system-i386 found
        ]
        
        runner = qemu_runner.QEMURunner()
        self.assertEqual(runner.qemu_binary, 'qemu-system-i386')
    
    def test_find_qemu_binary_not_found(self):
        """Test QEMU binary not found raises RuntimeError"""
        # Mock all binaries not found
        self.mock_subprocess.return_value.returncode = 1
        
        with self.assertRaises(RuntimeError) as context:
            qemu_runner.QEMURunner()
        
        self.assertIn("No QEMU binary found", str(context.exception))
    
    def test_build_qemu_command_basic(self):
        """Test basic QEMU command building"""
        self.mock_subprocess.return_value.returncode = 0
        runner = qemu_runner.QEMURunner()
        
        # Create mock args
        args = argparse.Namespace(
            memory='2G',
            cores=4,
            disk=None,
            cdrom=None,
            boot=None,
            network=False,
            vnc=None,
            display=None,
            enable_kvm=False,
            qemu_args=None,
            verbose=False
        )
        
        cmd = runner._build_qemu_command(args)
        
        expected = [
            'qemu-system-x86_64',
            '-m', '2G',
            '-smp', '4',
            '-display', 'none',
            '-serial', 'stdio'
        ]
        self.assertEqual(cmd, expected)
    
    def test_build_qemu_command_with_disk(self):
        """Test QEMU command building with disk"""
        self.mock_subprocess.return_value.returncode = 0
        self.mock_exists.return_value = True  # Disk file exists
        
        runner = qemu_runner.QEMURunner()
        
        args = argparse.Namespace(
            memory='1G',
            cores=1,
            disk='/path/to/disk.qcow2',
            cdrom=None,
            boot=None,
            network=False,
            vnc=None,
            display=None,
            enable_kvm=False,
            qemu_args=None,
            verbose=False
        )
        
        cmd = runner._build_qemu_command(args)
        
        self.assertIn('-hda', cmd)
        self.assertIn('/path/to/disk.qcow2', cmd)
    
    def test_build_qemu_command_disk_not_found(self):
        """Test QEMU command building with non-existent disk"""
        self.mock_subprocess.return_value.returncode = 0
        self.mock_exists.return_value = False  # Disk file doesn't exist
        
        runner = qemu_runner.QEMURunner()
        
        args = argparse.Namespace(
            disk='/nonexistent/disk.qcow2',
            cdrom=None,
            memory='1G',
            cores=1,
            boot=None,
            network=False,
            vnc=None,
            display=None,
            enable_kvm=False,
            qemu_args=None,
            verbose=False
        )
        
        with self.assertRaises(FileNotFoundError) as context:
            runner._build_qemu_command(args)
        
        self.assertIn("Disk image not found", str(context.exception))
    
    def test_build_qemu_command_with_network(self):
        """Test QEMU command building with network enabled"""
        self.mock_subprocess.return_value.returncode = 0
        
        runner = qemu_runner.QEMURunner()
        
        args = argparse.Namespace(
            memory='1G',
            cores=1,
            disk=None,
            cdrom=None,
            boot=None,
            network=True,
            network_device='e1000',
            vnc=None,
            display=None,
            enable_kvm=False,
            qemu_args=None,
            verbose=False
        )
        
        cmd = runner._build_qemu_command(args)
        
        self.assertIn('-netdev', cmd)
        self.assertIn('user,id=net0', cmd)
        self.assertIn('-device', cmd)
        self.assertIn('e1000,netdev=net0', cmd)
    
    def test_build_qemu_command_with_kvm(self):
        """Test QEMU command building with KVM enabled"""
        self.mock_subprocess.return_value.returncode = 0
        self.mock_exists.return_value = True  # /dev/kvm exists
        
        runner = qemu_runner.QEMURunner()
        
        args = argparse.Namespace(
            memory='1G',
            cores=1,
            disk=None,
            cdrom=None,
            boot=None,
            network=False,
            vnc=None,
            display=None,
            enable_kvm=True,
            qemu_args=None,
            verbose=False
        )
        
        cmd = runner._build_qemu_command(args)
        
        self.assertIn('-enable-kvm', cmd)
    
    def test_build_qemu_command_kvm_no_access(self):
        """Test QEMU command building with KVM but no access"""
        self.mock_subprocess.return_value.returncode = 0
        self.mock_exists.return_value = True  # /dev/kvm exists
        self.mock_open.side_effect = PermissionError()  # But can't access it
        
        runner = qemu_runner.QEMURunner()
        
        args = argparse.Namespace(
            memory='1G',
            cores=1,
            disk=None,
            cdrom=None,
            boot=None,
            network=False,
            vnc=None,
            display=None,
            enable_kvm=True,
            qemu_args=None,
            verbose=False
        )
        
        cmd = runner._build_qemu_command(args)
        
        self.assertIn('-accel', cmd)
        self.assertIn('tcg', cmd)
        self.assertNotIn('-enable-kvm', cmd)
    
    def test_run_vm_dry_run(self):
        """Test VM run in dry-run mode"""
        self.mock_subprocess.return_value.returncode = 0
        
        runner = qemu_runner.QEMURunner()
        
        args = argparse.Namespace(
            memory='1G',
            cores=1,
            disk=None,
            cdrom=None,
            boot=None,
            network=False,
            vnc=None,
            display=None,
            enable_kvm=False,
            qemu_args=None,
            dry_run=True,
            verbose=False
        )
        
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = runner.run_vm(args)
        
        self.assertEqual(result, 0)
        self.assertIn("Would execute:", mock_stdout.getvalue())
    
    def test_run_vm_actual_run(self):
        """Test actual VM run"""
        # Mock QEMU binary detection
        self.mock_subprocess.return_value.returncode = 0
        
        runner = qemu_runner.QEMURunner()
        
        args = argparse.Namespace(
            memory='1G',
            cores=1,
            disk=None,
            cdrom=None,
            boot=None,
            network=False,
            vnc=None,
            display=None,
            enable_kvm=False,
            qemu_args=None,
            dry_run=False,
            verbose=False
        )
        
        # Mock the actual QEMU run
        mock_qemu_run = mock.Mock(returncode=0)
        with mock.patch('qemu_runner.subprocess.run', side_effect=[
            mock.Mock(returncode=0),  # For binary detection
            mock_qemu_run  # For actual QEMU run
        ]):
            result = runner.run_vm(args)
        
        self.assertEqual(result, 0)
    
    def test_create_disk_success(self):
        """Test successful disk creation"""
        self.mock_subprocess.return_value.returncode = 0
        
        runner = qemu_runner.QEMURunner()
        
        with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = runner.create_disk('/path/to/disk.qcow2', '10G', 'qcow2')
        
        self.assertEqual(result, 0)
        self.assertIn("Created disk image", mock_stdout.getvalue())
    
    def test_create_disk_failure(self):
        """Test disk creation failure"""
        # Mock qemu-img binary detection success, but creation failure
        self.mock_subprocess.side_effect = [
            mock.Mock(returncode=0),  # Binary detection
            mock.Mock(returncode=1, stderr="Creation failed")  # Disk creation failure
        ]
        
        runner = qemu_runner.QEMURunner()
        
        with mock.patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = runner.create_disk('/path/to/disk.qcow2', '10G', 'qcow2')
        
        self.assertEqual(result, 1)
        self.assertIn("Error creating disk", mock_stderr.getvalue())
    
    def test_create_disk_qemu_img_not_found(self):
        """Test disk creation when qemu-img not found"""
        # Mock binary detection success, but qemu-img not found
        self.mock_subprocess.side_effect = [
            mock.Mock(returncode=0),  # Binary detection
            FileNotFoundError()  # qemu-img not found
        ]
        
        runner = qemu_runner.QEMURunner()
        
        with mock.patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = runner.create_disk('/path/to/disk.qcow2', '10G', 'qcow2')
        
        self.assertEqual(result, 1)
        self.assertIn("qemu-img not found", mock_stderr.getvalue())
    
    def test_list_machines(self):
        """Test listing machine types"""
        # Mock binary detection and machine list
        self.mock_subprocess.side_effect = [
            mock.Mock(returncode=0),  # Binary detection
            mock.Mock(returncode=0)   # Machine list
        ]
        
        runner = qemu_runner.QEMURunner()
        result = runner.list_machines()
        
        self.assertEqual(result, 0)


class TestArgumentParser(unittest.TestCase):
    """Test cases for argument parsing"""
    
    def test_create_parser(self):
        """Test parser creation"""
        parser = qemu_runner.create_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
    
    def test_parse_basic_args(self):
        """Test parsing basic arguments"""
        parser = qemu_runner.create_parser()
        args = parser.parse_args(['--memory', '2G', '--cores', '4'])
        
        self.assertEqual(args.memory, '2G')
        self.assertEqual(args.cores, 4)
    
    def test_parse_disk_args(self):
        """Test parsing disk arguments"""
        parser = qemu_runner.create_parser()
        args = parser.parse_args(['--disk', '/path/to/disk.qcow2'])
        
        self.assertEqual(args.disk, '/path/to/disk.qcow2')
    
    def test_parse_create_disk_command(self):
        """Test parsing create-disk command"""
        parser = qemu_runner.create_parser()
        args = parser.parse_args(['create-disk', '--path', 'test.qcow2', '--size', '10G'])
        
        self.assertEqual(args.command, 'create-disk')
        self.assertEqual(args.path, 'test.qcow2')
        self.assertEqual(args.size, '10G')
    
    def test_parse_list_machines_command(self):
        """Test parsing list-machines command"""
        parser = qemu_runner.create_parser()
        args = parser.parse_args(['list-machines'])
        
        self.assertEqual(args.command, 'list-machines')
    
    def test_parse_network_args(self):
        """Test parsing network arguments"""
        parser = qemu_runner.create_parser()
        args = parser.parse_args(['--network', '--network-device', 'virtio-net'])
        
        self.assertTrue(args.network)
        self.assertEqual(args.network_device, 'virtio-net')
    
    def test_parse_display_args(self):
        """Test parsing display arguments"""
        parser = qemu_runner.create_parser()
        args = parser.parse_args(['--vnc', ':1'])
        
        self.assertEqual(args.vnc, ':1')
    
    def test_parse_dry_run_verbose(self):
        """Test parsing dry-run and verbose flags"""
        parser = qemu_runner.create_parser()
        args = parser.parse_args(['--dry-run', '--verbose'])
        
        self.assertTrue(args.dry_run)
        self.assertTrue(args.verbose)


class TestMainFunction(unittest.TestCase):
    """Test cases for the main function"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock subprocess.run to avoid actual system calls
        self.subprocess_patcher = mock.patch('qemu_runner.subprocess.run')
        self.mock_subprocess = self.subprocess_patcher.start()
        self.mock_subprocess.return_value.returncode = 0
        
        # Mock sys.argv to control command line arguments
        self.argv_patcher = mock.patch('sys.argv')
        self.mock_argv = self.argv_patcher.start()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.subprocess_patcher.stop()
        self.argv_patcher.stop()
    
    def test_main_default_run_command(self):
        """Test main function with default run command"""
        self.mock_argv.__getitem__.return_value = ['qemu_runner.py', '--memory', '1G']
        
        with mock.patch('qemu_runner.create_parser') as mock_parser:
            mock_args = mock.Mock()
            mock_args.command = None
            mock_args.memory = '1G'
            mock_args.cores = 1
            mock_args.disk = None
            mock_args.cdrom = None
            mock_args.boot = None
            mock_args.network = False
            mock_args.vnc = None
            mock_args.display = None
            mock_args.enable_kvm = False
            mock_args.qemu_args = None
            mock_args.dry_run = True
            mock_args.verbose = False
            
            mock_parser.return_value.parse_args.return_value = mock_args
            
            with mock.patch('sys.stdout', new_callable=StringIO):
                result = qemu_runner.main()
            
            self.assertEqual(result, 0)
    
    def test_main_create_disk_command(self):
        """Test main function with create-disk command"""
        with mock.patch('qemu_runner.create_parser') as mock_parser:
            mock_args = mock.Mock()
            mock_args.command = 'create-disk'
            mock_args.path = 'test.qcow2'
            mock_args.size = '10G'
            mock_args.format = 'qcow2'
            
            mock_parser.return_value.parse_args.return_value = mock_args
            
            with mock.patch('sys.stdout', new_callable=StringIO):
                result = qemu_runner.main()
            
            self.assertEqual(result, 0)
    
    def test_main_list_machines_command(self):
        """Test main function with list-machines command"""
        with mock.patch('qemu_runner.create_parser') as mock_parser:
            mock_args = mock.Mock()
            mock_args.command = 'list-machines'
            
            mock_parser.return_value.parse_args.return_value = mock_args
            
            result = qemu_runner.main()
            
            self.assertEqual(result, 0)
    
    def test_main_invalid_command(self):
        """Test main function with invalid command"""
        with mock.patch('qemu_runner.create_parser') as mock_parser:
            mock_args = mock.Mock()
            mock_args.command = 'invalid-command'
            
            mock_parser_instance = mock.Mock()
            mock_parser.return_value = mock_parser_instance
            mock_parser_instance.parse_args.return_value = mock_args
            
            result = qemu_runner.main()
            
            self.assertEqual(result, 1)
            mock_parser_instance.print_help.assert_called_once()
    
    def test_main_exception_handling(self):
        """Test main function exception handling"""
        with mock.patch('qemu_runner.QEMURunner') as mock_runner_class:
            mock_runner_class.side_effect = Exception("Test exception")
            
            with mock.patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with mock.patch('qemu_runner.create_parser') as mock_parser:
                    mock_args = mock.Mock()
                    mock_args.command = 'run'
                    mock_parser.return_value.parse_args.return_value = mock_args
                    
                    result = qemu_runner.main()
            
            self.assertEqual(result, 1)
            self.assertIn("Fatal error", mock_stderr.getvalue())


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.test_disk = os.path.join(self.test_dir, 'test.qcow2')
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_help_output(self):
        """Test that help output is generated without errors"""
        with mock.patch('sys.argv', ['qemu_runner.py', '--help']):
            with self.assertRaises(SystemExit) as context:
                qemu_runner.main()
            
            # Help should exit with code 0
            self.assertEqual(context.exception.code, 0)
    
    @mock.patch('qemu_runner.subprocess.run')
    def test_dry_run_integration(self, mock_subprocess):
        """Test dry-run integration"""
        mock_subprocess.return_value.returncode = 0
        
        with mock.patch('sys.argv', ['qemu_runner.py', '--memory', '1G', '--dry-run']):
            with mock.patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = qemu_runner.main()
        
        self.assertEqual(result, 0)
        self.assertIn("Would execute:", mock_stdout.getvalue())


if __name__ == '__main__':
    unittest.main()