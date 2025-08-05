#!/usr/bin/env bats

# Load test setup
load setup

setup() {
    setup_test_environment
}

teardown() {
    teardown_test_environment
}

@test "setup_directories creates VM directory" {
    run setup_directories
    [ "$status" -eq 0 ]
    [ -d "$TEST_VM_DIR" ]
    [[ "$output" =~ "Creating VM directory structure" ]]
}

@test "setup_directories changes to VM directory" {
    # Save current directory
    original_dir=$(pwd)
    
    run bash -c "source test/setup.bash; setup_test_environment; setup_directories; pwd"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "$TEST_VM_DIR" ]]
}

@test "setup_directories handles existing directory" {
    # Create directory first
    mkdir -p "$TEST_VM_DIR"
    
    run setup_directories
    [ "$status" -eq 0 ]
    [ -d "$TEST_VM_DIR" ]
    [[ "$output" =~ "Creating VM directory structure" ]]
}

@test "setup_directories creates nested directories" {
    # Test with a deeply nested path
    export TEST_VM_DIR="/tmp/test-vms/nested/path/test-vm"
    VM_DIR="$TEST_VM_DIR"
    
    run setup_directories
    [ "$status" -eq 0 ]
    [ -d "$TEST_VM_DIR" ]
}

@test "setup_directories handles directory creation failure" {
    # Try to create directory in a location that should fail
    export TEST_VM_DIR="/root/forbidden/test-vm"
    VM_DIR="$TEST_VM_DIR"
    
    run setup_directories
    # Should fail due to permissions
    [ "$status" -ne 0 ]
}

@test "setup_directories prints status message" {
    run setup_directories
    [ "$status" -eq 0 ]
    [[ "$output" =~ \[INFO\] ]]
    [[ "$output" =~ "Creating VM directory structure" ]]
    # Check for green color code from print_status
    [[ "$output" =~ $'\033[0;32m' ]]
}