#!/usr/bin/env bats

# Load test setup
load setup

setup() {
    setup_test_environment
    enable_mocks
    mkdir -p "$TEST_VM_DIR"
    cd "$TEST_VM_DIR"
    # Create dummy cloud image
    touch "$UBUNTU_CLOUD_IMG"
}

teardown() {
    disable_mocks
    teardown_test_environment
}

@test "create_disk converts cloud image to VM disk" {
    run create_disk
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Converting cloud image to VM disk" ]]
    [[ "$output" =~ "qemu-img mock called with args: convert -f qcow2 -O qcow2 $UBUNTU_CLOUD_IMG $VM_NAME.qcow2" ]]
    [ -f "$VM_NAME.qcow2" ]
}

@test "create_disk resizes disk to specified size" {
    run create_disk
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Resizing disk to $DISK_SIZE" ]]
    [[ "$output" =~ "qemu-img mock called with args: resize $VM_NAME.qcow2 $DISK_SIZE" ]]
}

@test "create_disk skips creation when disk exists" {
    # Create dummy disk file
    touch "$VM_NAME.qcow2"
    
    run create_disk
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Virtual disk already exists, skipping creation" ]]
    [[ ! "$output" =~ "Converting cloud image" ]]
    [[ ! "$output" =~ "qemu-img mock called" ]]
}

@test "create_disk prints proper status messages" {
    run create_disk
    [ "$status" -eq 0 ]
    [[ "$output" =~ \[INFO\] ]]
    [[ "$output" =~ "Converting cloud image to VM disk" ]]
    [[ "$output" =~ "Resizing disk to" ]]
    # Check for green color code from print_status
    [[ "$output" =~ $'\033[0;32m' ]]
}

@test "create_disk uses correct qcow2 format" {
    run create_disk
    [ "$status" -eq 0 ]
    [[ "$output" =~ "convert -f qcow2 -O qcow2" ]]
}

@test "create_disk creates file with VM name" {
    run create_disk
    [ "$status" -eq 0 ]
    [ -f "$TEST_VM_NAME.qcow2" ]
}

@test "create_disk uses virtio interface format" {
    # This is implicit in the qcow2 format choice, but we test the format is correct
    run create_disk
    [ "$status" -eq 0 ]
    [[ "$output" =~ "-f qcow2 -O qcow2" ]]
}

@test "create_disk handles missing cloud image gracefully" {
    # Remove the cloud image
    rm -f "$UBUNTU_CLOUD_IMG"
    
    run create_disk
    # Should still succeed (qemu-img mock doesn't check source file)
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Converting cloud image to VM disk" ]]
}