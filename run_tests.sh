#!/bin/bash

# Test runner script for QEMU Ubuntu VM Setup
# Installs BATS testing framework and runs all unit tests

set -e

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

# Check if BATS is installed
check_bats() {
    if ! command -v bats &> /dev/null; then
        print_warning "BATS is not installed. Installing..."
        install_bats
    else
        print_status "BATS is already installed"
    fi
}

# Install BATS testing framework
install_bats() {
    print_status "Installing BATS testing framework..."
    
    # Check if we're on Ubuntu/Debian
    if command -v apt &> /dev/null; then
        print_status "Installing BATS via apt..."
        sudo apt update
        sudo apt install -y bats
    # Check if we're on Fedora/RHEL
    elif command -v dnf &> /dev/null; then
        print_status "Installing BATS via dnf..."
        sudo dnf install -y bats
    # Check if we're on Arch
    elif command -v pacman &> /dev/null; then
        print_status "Installing BATS via pacman..."
        sudo pacman -S --noconfirm bats
    # Fallback to manual installation
    else
        print_status "Installing BATS manually..."
        # Clone BATS repository
        if [ ! -d "/tmp/bats-core" ]; then
            git clone https://github.com/bats-core/bats-core.git /tmp/bats-core
        fi
        cd /tmp/bats-core
        sudo ./install.sh /usr/local
        cd - > /dev/null
    fi
    
    # Verify installation
    if command -v bats &> /dev/null; then
        print_status "BATS installed successfully: $(bats --version)"
    else
        print_error "Failed to install BATS"
        exit 1
    fi
}

# Run all tests
run_tests() {
    print_status "Running unit tests..."
    
    # Change to project root
    cd "$(dirname "$0")"
    
    # Check if test directory exists
    if [ ! -d "test" ]; then
        print_error "Test directory not found!"
        exit 1
    fi
    
    # Run all BATS test files
    test_files=(
        "test/test_utility_functions.bats"
        "test/test_check_qemu.bats"
        "test/test_setup_directories.bats"
        "test/test_download_cloud_image.bats"
        "test/test_create_disk.bats"
        "test/test_cloud_init.bats"
        "test/test_ssh_setup.bats"
        "test/test_script_creation.bats"
        "test/test_configuration.bats"
        "test/test_integration.bats"
    )
    
    total_tests=0
    passed_tests=0
    failed_tests=0
    
    for test_file in "${test_files[@]}"; do
        if [ -f "$test_file" ]; then
            print_status "Running $test_file..."
            if bats "$test_file"; then
                print_status "✅ $test_file passed"
                ((passed_tests++))
            else
                print_error "❌ $test_file failed"
                ((failed_tests++))
            fi
            ((total_tests++))
        else
            print_warning "Test file not found: $test_file"
        fi
    done
    
    # Print summary
    echo ""
    echo "==============================================="
    echo "TEST SUMMARY"
    echo "==============================================="
    echo "Total test files: $total_tests"
    echo "Passed: $passed_tests"
    echo "Failed: $failed_tests"
    echo ""
    
    if [ $failed_tests -eq 0 ]; then
        print_status "🎉 All tests passed!"
        exit 0
    else
        print_error "Some tests failed. Please check the output above."
        exit 1
    fi
}

# Run tests with verbose output
run_tests_verbose() {
    print_status "Running unit tests with verbose output..."
    
    cd "$(dirname "$0")"
    
    if [ ! -d "test" ]; then
        print_error "Test directory not found!"
        exit 1
    fi
    
    # Run all tests in verbose mode
    bats --recursive --verbose test/
}

# Show help
show_help() {
    echo "QEMU Ubuntu VM Setup - Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Run tests with verbose output"
    echo "  -i, --install  Install BATS testing framework only"
    echo ""
    echo "Examples:"
    echo "  $0              # Run all tests"
    echo "  $0 --verbose    # Run tests with detailed output"
    echo "  $0 --install    # Install BATS framework only"
}

# Main function
main() {
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            check_bats
            run_tests_verbose
            ;;
        -i|--install)
            install_bats
            exit 0
            ;;
        "")
            check_bats
            run_tests
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"