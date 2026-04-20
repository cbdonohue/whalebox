#!/bin/bash

# Test setup file - loads functions from main script for testing
# This file is sourced by BATS test files

# Source the main script to get access to functions
# We need to prevent the main function from running during testing
export TESTING=true
source "$(dirname "${BASH_SOURCE[0]}")/../setup-ubuntu-vm.sh"

# Test helper functions
setup_test_environment() {
    export TEST_VM_NAME="test-ubuntu-vm"
    export TEST_VM_DIR="/tmp/test-vms/$TEST_VM_NAME"
    export TEST_DISK_SIZE="5G"
    export TEST_RAM="1G"
    export TEST_CPUS="1"
    export TEST_SSH_PORT="2223"
    
    # Override global variables for testing
    VM_NAME="$TEST_VM_NAME"
    VM_DIR="$TEST_VM_DIR"
    DISK_SIZE="$TEST_DISK_SIZE"
    RAM="$TEST_RAM"
    CPUS="$TEST_CPUS"
    SSH_PORT="$TEST_SSH_PORT"
}

teardown_test_environment() {
    # Clean up test directories
    if [ -d "/tmp/test-vms" ]; then
        rm -rf "/tmp/test-vms"
    fi
    
    # Clean up any test SSH keys
    if [ -f "/tmp/test_id_rsa" ]; then
        rm -f "/tmp/test_id_rsa" "/tmp/test_id_rsa.pub"
    fi
}

# Mock external commands for testing
mock_qemu_system_x86_64() {
    echo "qemu-system-x86_64 mock called with args: $*"
}

mock_wget() {
    echo "wget mock called with args: $*"
    # Create a dummy file if -O is specified
    if [[ "$*" == *"-O"* ]]; then
        local output_file
        for ((i=1; i<=$#; i++)); do
            if [[ "${!i}" == "-O" ]]; then
                ((i++))
                output_file="${!i}"
                break
            fi
        done
        if [[ -n "$output_file" ]]; then
            touch "$output_file"
        fi
    fi
}

mock_qemu_img() {
    echo "qemu-img mock called with args: $*"
    # Create dummy files for convert and resize operations
    if [[ "$1" == "convert" ]]; then
        # Extract output file from convert command
        local output_file="${!#}"  # Last argument
        touch "$output_file"
    fi
}

mock_ssh_keygen() {
    echo "ssh-keygen mock called with args: $*"
    # Create dummy SSH key files
    local key_file
    for ((i=1; i<=$#; i++)); do
        if [[ "${!i}" == "-f" ]]; then
            ((i++))
            key_file="${!i}"
            break
        fi
    done
    if [[ -n "$key_file" ]]; then
        echo "dummy-private-key" > "$key_file"
        echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7dummy-public-key test@example.com" > "$key_file.pub"
    fi
}

mock_genisoimage() {
    echo "genisoimage mock called with args: $*"
    # Create dummy ISO file
    local output_file
    for ((i=1; i<=$#; i++)); do
        if [[ "${!i}" == "-output" ]]; then
            ((i++))
            output_file="${!i}"
            break
        fi
    done
    if [[ -n "$output_file" ]]; then
        touch "$output_file"
    fi
}

# Function to enable mocking
enable_mocks() {
    alias qemu-system-x86_64=mock_qemu_system_x86_64
    alias wget=mock_wget
    alias qemu-img=mock_qemu_img
    alias ssh-keygen=mock_ssh_keygen
    alias genisoimage=mock_genisoimage
    alias mkisofs=mock_genisoimage
}

# Function to disable mocking
disable_mocks() {
    unalias qemu-system-x86_64 2>/dev/null || true
    unalias wget 2>/dev/null || true
    unalias qemu-img 2>/dev/null || true
    unalias ssh-keygen 2>/dev/null || true
    unalias genisoimage 2>/dev/null || true
    unalias mkisofs 2>/dev/null || true
}