# Unit Testing for QEMU Ubuntu VM Setup

This directory contains a comprehensive unit test suite for the `setup-ubuntu-vm.sh` script using the BATS (Bash Automated Testing System) framework.

## Quick Start

Run all tests:
```bash
./run_tests.sh
```

Run tests with verbose output:
```bash
./run_tests.sh --verbose
```

Install BATS framework only:
```bash
./run_tests.sh --install
```

## Test Structure

### Test Files

- `test/setup.bash` - Test setup and mocking framework
- `test/test_utility_functions.bats` - Tests for print functions (status, warning, error)
- `test/test_check_qemu.bats` - Tests for QEMU installation validation
- `test/test_setup_directories.bats` - Tests for VM directory creation
- `test/test_download_cloud_image.bats` - Tests for Ubuntu cloud image download
- `test/test_create_disk.bats` - Tests for VM disk creation and conversion
- `test/test_cloud_init.bats` - Tests for cloud-init configuration generation
- `test/test_ssh_setup.bats` - Tests for SSH key generation and setup
- `test/test_script_creation.bats` - Tests for VM management script creation
- `test/test_configuration.bats` - Tests for configuration variables and validation
- `test/test_integration.bats` - Integration tests for complete workflow

### Test Framework Features

#### Mocking System
The test suite includes a comprehensive mocking system that replaces external commands:
- `qemu-system-x86_64` - QEMU virtualization
- `wget` - File downloading
- `qemu-img` - Disk image manipulation
- `ssh-keygen` - SSH key generation
- `genisoimage`/`mkisofs` - ISO creation

#### Test Environment
- Uses isolated test directories under `/tmp/test-vms/`
- Prevents execution of the main script during testing
- Provides cleanup functions for test isolation
- Configurable test VM parameters

## Test Coverage

### Unit Tests
- ✅ Utility functions (print_status, print_warning, print_error)
- ✅ QEMU installation checking
- ✅ Directory structure creation
- ✅ Cloud image downloading logic
- ✅ VM disk creation and conversion
- ✅ Cloud-init configuration generation
- ✅ SSH key setup and integration
- ✅ VM management script creation
- ✅ Configuration validation

### Integration Tests
- ✅ Complete VM setup workflow
- ✅ File creation verification
- ✅ Cross-script configuration consistency
- ✅ Error handling scenarios
- ✅ Dependency management

## Running Individual Test Files

You can run individual test files using BATS directly:

```bash
# Run specific test file
bats test/test_utility_functions.bats

# Run with verbose output
bats --verbose test/test_check_qemu.bats

# Run all tests in test directory
bats test/
```

## Test Development

### Adding New Tests

1. Create a new `.bats` file in the `test/` directory
2. Include the setup loader: `load setup`
3. Use `setup()` and `teardown()` functions for test isolation
4. Follow the naming convention: `test_[functionality].bats`

Example test structure:
```bash
#!/usr/bin/env bats

load setup

setup() {
    setup_test_environment
    enable_mocks  # if needed
}

teardown() {
    disable_mocks  # if used
    teardown_test_environment
}

@test "descriptive test name" {
    run your_function
    [ "$status" -eq 0 ]
    [[ "$output" =~ "expected output" ]]
}
```

### Test Assertions

Common BATS assertions used in this test suite:
- `[ "$status" -eq 0 ]` - Command succeeded
- `[ "$status" -ne 0 ]` - Command failed
- `[[ "$output" =~ "pattern" ]]` - Output contains pattern
- `[ -f "filename" ]` - File exists
- `[ -d "dirname" ]` - Directory exists
- `[ -x "script" ]` - Script is executable

### Mocking External Commands

The test framework provides mocking for external dependencies:

```bash
# Enable mocking in your test
enable_mocks

# Mock will automatically handle:
# - qemu-system-x86_64 commands
# - wget downloads
# - qemu-img operations
# - SSH key generation
# - ISO creation tools

# Disable mocking when done
disable_mocks
```

## Continuous Integration

The test suite is designed to run in CI environments:
- Automatic BATS installation across different Linux distributions
- Non-interactive execution [[memory:5284374]]
- Isolated test environments
- Comprehensive error reporting

## Dependencies

### Required
- Bash 4.0+
- BATS testing framework (auto-installed by `run_tests.sh`)

### Optional (for real VM operations)
- QEMU/KVM
- wget/curl
- genisoimage or mkisofs
- SSH client

## Troubleshooting

### Common Issues

1. **BATS not found**: Run `./run_tests.sh --install` to install BATS
2. **Permission errors**: Ensure test runner is executable: `chmod +x run_tests.sh`
3. **Test failures**: Run with verbose output: `./run_tests.sh --verbose`

### Test Environment Cleanup

Tests automatically clean up after themselves, but if needed:
```bash
# Manual cleanup
rm -rf /tmp/test-vms/
rm -f /tmp/test_id_rsa*
```

## Performance

The test suite typically runs in under 30 seconds and includes:
- ~80+ individual test cases
- Complete function coverage
- Integration testing
- Error scenario validation

## Contributing

When adding new functionality to the main script:
1. Add corresponding unit tests
2. Update integration tests if needed
3. Run the full test suite: `./run_tests.sh`
4. Ensure all tests pass before committing