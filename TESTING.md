# Testing Guide for QEMU Runner

This document explains how to run and work with the test suite for the QEMU Runner project.

## Overview

The test suite uses Python's built-in `unittest` framework and includes comprehensive tests for all major components:

- **QEMURunner class tests**: Core functionality, command building, VM operations
- **Argument parser tests**: Command-line argument parsing and validation
- **Main function tests**: Entry point and command routing
- **Integration tests**: End-to-end functionality testing

## Running Tests

### Quick Start

```bash
# Run all tests
python3 run_tests.py

# Or using make
make test
```

### Test Runner Options

The `run_tests.py` script provides several options:

```bash
# Basic usage
python3 run_tests.py                    # Normal verbosity
python3 run_tests.py -v                 # More verbose
python3 run_tests.py -vv                # Maximum verbosity
python3 run_tests.py -q                 # Quiet mode

# Run specific tests
python3 run_tests.py -t test_qemu_runner.TestQEMURunner
python3 run_tests.py -t test_qemu_runner.TestQEMURunner.test_find_qemu_binary_success

# Coverage analysis (requires coverage package)
python3 run_tests.py --coverage
```

### Using Make Commands

```bash
make test              # Run all tests (normal verbosity)
make test-verbose      # Run with maximum verbosity
make test-quiet        # Run with minimal output
make test-coverage     # Run with coverage analysis
make clean             # Clean up test artifacts
make help              # Show available targets
```

### Direct Test Execution

You can also run tests directly:

```bash
# Run all tests
python3 -m unittest discover

# Run specific test file
python3 -m unittest test_qemu_runner

# Run specific test class
python3 -m unittest test_qemu_runner.TestQEMURunner

# Run specific test method
python3 -m unittest test_qemu_runner.TestQEMURunner.test_find_qemu_binary_success
```

## Test Structure

### Test Files

- `test_qemu_runner.py` - Main test suite
- `run_tests.py` - Test runner with additional features
- `Makefile` - Convenient make targets for testing

### Test Classes

1. **TestQEMURunner** - Tests for the main QEMURunner class
   - Binary detection (`_find_qemu_binary`)
   - Command building (`_build_qemu_command`)
   - VM execution (`run_vm`)
   - Disk creation (`create_disk`)
   - Machine listing (`list_machines`)

2. **TestArgumentParser** - Tests for command-line argument parsing
   - Basic argument parsing
   - Command-specific arguments
   - Flag and option handling

3. **TestMainFunction** - Tests for the main entry point
   - Command routing
   - Error handling
   - Integration with QEMURunner

4. **TestIntegration** - Integration and end-to-end tests
   - Help output generation
   - Dry-run functionality

## Test Features

### Mocking

The tests use extensive mocking to avoid:
- Actual system calls to QEMU
- File system operations
- External command execution

This ensures tests run quickly and don't require QEMU to be installed.

### Coverage Analysis

To run tests with coverage analysis:

```bash
# Install coverage (optional)
pip install coverage

# Run tests with coverage
python3 run_tests.py --coverage
# or
make test-coverage
```

This generates:
- Console coverage report
- HTML coverage report in `htmlcov/` directory

### Test Isolation

Each test class uses proper setup and teardown methods to ensure:
- Clean test environment
- No side effects between tests
- Proper resource cleanup

## Adding New Tests

When adding new functionality to QEMU Runner, follow these guidelines:

### 1. Test Structure

```python
class TestNewFeature(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Mock external dependencies
        pass
    
    def tearDown(self):
        """Clean up after tests"""
        # Stop mocks, clean up resources
        pass
    
    def test_feature_success(self):
        """Test successful operation"""
        # Test the happy path
        pass
    
    def test_feature_error_handling(self):
        """Test error conditions"""
        # Test error cases
        pass
```

### 2. Mocking Guidelines

- Mock external system calls (`subprocess.run`)
- Mock file system operations (`os.path.exists`, `open`)
- Mock any dependencies that require external tools
- Use descriptive mock return values

### 3. Test Naming

- Use descriptive test method names
- Start with `test_`
- Include the scenario being tested
- Example: `test_build_qemu_command_with_network`

### 4. Assertions

- Use specific assertions (`assertEqual`, `assertIn`, `assertRaises`)
- Include descriptive error messages when helpful
- Test both positive and negative cases

## Continuous Integration

The test suite is designed to run in CI environments:

- No external dependencies required
- Fast execution (< 1 second)
- Clear pass/fail indicators
- Detailed error reporting

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from the project root directory
2. **Mock Issues**: Check that mocks are properly configured and cleaned up
3. **Coverage Issues**: Install the `coverage` package if using coverage analysis

### Debug Mode

For debugging test failures, use maximum verbosity:

```bash
python3 run_tests.py -vv
```

This shows:
- Individual test names as they run
- Detailed failure information
- Full error tracebacks

## Performance

The test suite is optimized for speed:
- **30 tests** run in **< 0.1 seconds**
- Extensive mocking eliminates external dependencies
- Efficient test isolation and cleanup

This ensures rapid development feedback and CI compatibility.