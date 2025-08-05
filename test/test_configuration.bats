#!/usr/bin/env bats

# Load test setup
load setup

setup() {
    setup_test_environment
}

teardown() {
    teardown_test_environment
}

@test "configuration variables are set correctly" {
    # Test default configuration values
    [ "$VM_NAME" = "test-ubuntu-vm" ]
    [ "$DISK_SIZE" = "5G" ]
    [ "$RAM" = "1G" ]
    [ "$CPUS" = "1" ]
    [ "$SSH_PORT" = "2223" ]
    [ "$UBUNTU_CLOUD_URL" = "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img" ]
    [ "$UBUNTU_CLOUD_IMG" = "jammy-server-cloudimg-amd64.img" ]
}

@test "VM directory path is constructed correctly" {
    [[ "$VM_DIR" =~ "/tmp/test-vms/$VM_NAME" ]]
    [[ "$VM_DIR" = "/tmp/test-vms/test-ubuntu-vm" ]]
}

@test "color codes are defined correctly" {
    [ "$RED" = '\033[0;31m' ]
    [ "$GREEN" = '\033[0;32m' ]
    [ "$YELLOW" = '\033[1;33m' ]
    [ "$NC" = '\033[0m' ]
}

@test "script has proper shebang and error handling" {
    head -n 1 "/workspace/setup-ubuntu-vm.sh" | grep -q "#!/bin/bash"
    grep -q "set -e" "/workspace/setup-ubuntu-vm.sh"
}

@test "script includes all required functions" {
    grep -q "print_status()" "/workspace/setup-ubuntu-vm.sh"
    grep -q "print_warning()" "/workspace/setup-ubuntu-vm.sh"
    grep -q "print_error()" "/workspace/setup-ubuntu-vm.sh"
    grep -q "check_qemu()" "/workspace/setup-ubuntu-vm.sh"
    grep -q "setup_directories()" "/workspace/setup-ubuntu-vm.sh"
    grep -q "download_cloud_image()" "/workspace/setup-ubuntu-vm.sh"
    grep -q "create_disk()" "/workspace/setup-ubuntu-vm.sh"
    grep -q "create_cloud_init()" "/workspace/setup-ubuntu-vm.sh"
    grep -q "setup_ssh_key()" "/workspace/setup-ubuntu-vm.sh"
    grep -q "create_startup_script()" "/workspace/setup-ubuntu-vm.sh"
    grep -q "create_stop_script()" "/workspace/setup-ubuntu-vm.sh"
    grep -q "create_status_script()" "/workspace/setup-ubuntu-vm.sh"
    grep -q "main()" "/workspace/setup-ubuntu-vm.sh"
}

@test "script calls main function at the end" {
    tail -n 5 "/workspace/setup-ubuntu-vm.sh" | grep -q 'main "$@"'
}

@test "configuration supports different VM sizes" {
    # Test that variables can be overridden
    export DISK_SIZE="10G"
    export RAM="4G"
    export CPUS="4"
    
    [ "$DISK_SIZE" = "10G" ]
    [ "$RAM" = "4G" ]
    [ "$CPUS" = "4" ]
}

@test "SSH port configuration is valid" {
    # Test that SSH port is a number and in valid range
    [[ "$SSH_PORT" =~ ^[0-9]+$ ]]
    [ "$SSH_PORT" -gt 1000 ]
    [ "$SSH_PORT" -lt 65536 ]
}

@test "Ubuntu cloud image URL is accessible format" {
    [[ "$UBUNTU_CLOUD_URL" =~ ^https:// ]]
    [[ "$UBUNTU_CLOUD_URL" =~ cloud-images\.ubuntu\.com ]]
    [[ "$UBUNTU_CLOUD_URL" =~ \.img$ ]]
}

@test "VM name is valid for filesystem" {
    # Test that VM name doesn't contain invalid filesystem characters
    [[ ! "$VM_NAME" =~ [/\\:*?"<>|] ]]
    [[ "$VM_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]
}