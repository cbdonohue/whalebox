#!/usr/bin/env bats

# Load test setup
load setup

setup() {
    setup_test_environment
    enable_mocks
    mkdir -p "$TEST_VM_DIR"
    cd "$TEST_VM_DIR"
}

teardown() {
    disable_mocks
    teardown_test_environment
}

@test "download_cloud_image downloads image when it doesn't exist" {
    run download_cloud_image
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Downloading Ubuntu 22.04 LTS cloud image" ]]
    [[ "$output" =~ "wget mock called" ]]
    [ -f "$UBUNTU_CLOUD_IMG" ]
}

@test "download_cloud_image skips download when image exists" {
    # Create dummy image file
    touch "$UBUNTU_CLOUD_IMG"
    
    run download_cloud_image
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Ubuntu cloud image already exists, skipping download" ]]
    [[ ! "$output" =~ "wget mock called" ]]
}

@test "download_cloud_image uses correct wget parameters" {
    run download_cloud_image
    [ "$status" -eq 0 ]
    [[ "$output" =~ "wget mock called with args: -O $UBUNTU_CLOUD_IMG $UBUNTU_CLOUD_URL" ]]
}

@test "download_cloud_image prints proper status messages" {
    run download_cloud_image
    [ "$status" -eq 0 ]
    [[ "$output" =~ \[INFO\] ]]
    [[ "$output" =~ "Downloading Ubuntu 22.04 LTS cloud image" ]]
    # Check for green color code from print_status
    [[ "$output" =~ $'\033[0;32m' ]]
}

@test "download_cloud_image creates file with correct name" {
    run download_cloud_image
    [ "$status" -eq 0 ]
    [ -f "$UBUNTU_CLOUD_IMG" ]
    [ -f "jammy-server-cloudimg-amd64.img" ]
}

@test "download_cloud_image handles existing file gracefully" {
    # Create dummy image file with some content
    echo "dummy content" > "$UBUNTU_CLOUD_IMG"
    original_content=$(cat "$UBUNTU_CLOUD_IMG")
    
    run download_cloud_image
    [ "$status" -eq 0 ]
    [[ "$output" =~ "already exists, skipping download" ]]
    
    # Verify file wasn't overwritten
    current_content=$(cat "$UBUNTU_CLOUD_IMG")
    [ "$original_content" = "$current_content" ]
}

@test "download_cloud_image uses correct Ubuntu cloud URL" {
    run download_cloud_image
    [ "$status" -eq 0 ]
    [[ "$output" =~ "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img" ]]
}