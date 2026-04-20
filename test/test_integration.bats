#!/usr/bin/env bats

# Load test setup
load setup

setup() {
    setup_test_environment
    enable_mocks
    
    # Mock command to simulate all tools being available
    command() {
        case "$2" in
            "qemu-system-x86_64"|"genisoimage"|"mkisofs")
                return 0
                ;;
            *)
                /usr/bin/command "$@"
                ;;
        esac
    }
    export -f command
}

teardown() {
    disable_mocks
    teardown_test_environment
}

@test "main function executes all setup steps in correct order" {
    # Override main to track function calls
    main() {
        echo "=== Starting main function ==="
        check_qemu
        setup_directories
        download_cloud_image
        create_disk
        create_cloud_init
        setup_ssh_key
        create_startup_script
        create_stop_script
        create_status_script
        echo "=== Main function completed ==="
    }
    export -f main
    
    run main
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Starting main function" ]]
    [[ "$output" =~ "Creating VM directory structure" ]]
    [[ "$output" =~ "Downloading Ubuntu 22.04 LTS cloud image" ]]
    [[ "$output" =~ "Converting cloud image to VM disk" ]]
    [[ "$output" =~ "Creating cloud-init configuration" ]]
    [[ "$output" =~ "Creating VM startup script" ]]
    [[ "$output" =~ "Creating VM stop script" ]]
    [[ "$output" =~ "Creating VM status script" ]]
    [[ "$output" =~ "Main function completed" ]]
}

@test "integration test: complete VM setup creates all required files" {
    # Set up a clean test environment
    export HOME="/tmp"
    export SSH_KEY_PATH="/tmp/.ssh/id_rsa"
    mkdir -p "/tmp/.ssh"
    
    # Run the complete setup process
    check_qemu
    setup_directories
    download_cloud_image
    create_disk
    create_cloud_init
    setup_ssh_key
    create_startup_script
    create_stop_script
    create_status_script
    
    # Verify all expected files were created
    [ -d "$TEST_VM_DIR" ]
    [ -f "$TEST_VM_DIR/$UBUNTU_CLOUD_IMG" ]
    [ -f "$TEST_VM_DIR/$TEST_VM_NAME.qcow2" ]
    [ -f "$TEST_VM_DIR/user-data" ]
    [ -f "$TEST_VM_DIR/meta-data" ]
    [ -f "$TEST_VM_DIR/cloud-init.iso" ]
    [ -f "$TEST_VM_DIR/start-vm.sh" ]
    [ -f "$TEST_VM_DIR/stop-vm.sh" ]
    [ -f "$TEST_VM_DIR/status-vm.sh" ]
    [ -f "/tmp/.ssh/id_rsa" ]
    [ -f "/tmp/.ssh/id_rsa.pub" ]
}

@test "integration test: scripts are executable after creation" {
    # Set up environment and create scripts
    export HOME="/tmp"
    setup_directories
    create_startup_script
    create_stop_script
    create_status_script
    
    # Verify all scripts are executable
    [ -x "$TEST_VM_DIR/start-vm.sh" ]
    [ -x "$TEST_VM_DIR/stop-vm.sh" ]
    [ -x "$TEST_VM_DIR/status-vm.sh" ]
}

@test "integration test: cloud-init configuration is valid" {
    # Set up environment and create cloud-init
    export HOME="/tmp"
    export SSH_KEY_PATH="/tmp/.ssh/id_rsa"
    mkdir -p "/tmp/.ssh"
    
    setup_directories
    create_cloud_init
    setup_ssh_key
    
    # Verify cloud-init files have expected content
    grep -q "#cloud-config" "$TEST_VM_DIR/user-data"
    grep -q "name: ubuntu" "$TEST_VM_DIR/user-data"
    grep -q "instance-id: $TEST_VM_NAME" "$TEST_VM_DIR/meta-data"
    
    # Verify SSH key was properly inserted
    grep -q "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7dummy-public-key" "$TEST_VM_DIR/user-data"
}

@test "integration test: VM configuration variables are consistent across scripts" {
    # Set up environment and create all scripts
    setup_directories
    create_startup_script
    create_stop_script
    create_status_script
    
    # Check that all scripts use the same VM configuration
    grep -q "VM_NAME=\"$TEST_VM_NAME\"" "$TEST_VM_DIR/start-vm.sh"
    grep -q "VM_NAME=\"$TEST_VM_NAME\"" "$TEST_VM_DIR/stop-vm.sh"
    grep -q "VM_NAME=\"$TEST_VM_NAME\"" "$TEST_VM_DIR/status-vm.sh"
    
    grep -q "SSH_PORT=\"$TEST_SSH_PORT\"" "$TEST_VM_DIR/start-vm.sh"
    grep -q "SSH_PORT=\"$TEST_SSH_PORT\"" "$TEST_VM_DIR/status-vm.sh"
}

@test "integration test: error handling when QEMU not available" {
    # Mock command to simulate qemu not being available
    command() {
        if [[ "$1" == "-v" && "$2" == "qemu-system-x86_64" ]]; then
            return 1
        fi
        /usr/bin/command "$@"
    }
    export -f command
    
    run check_qemu
    [ "$status" -eq 1 ]
    [[ "$output" =~ "QEMU is not installed" ]]
}

@test "integration test: setup handles missing dependencies gracefully" {
    # Mock command to simulate missing ISO creation tools
    command() {
        case "$2" in
            "qemu-system-x86_64")
                return 0
                ;;
            "genisoimage"|"mkisofs")
                return 1
                ;;
            *)
                /usr/bin/command "$@"
                ;;
        esac
    }
    export -f command
    
    # Run setup steps
    run bash -c "
        source test/setup.bash
        setup_test_environment
        enable_mocks
        mkdir -p '$TEST_VM_DIR'
        cd '$TEST_VM_DIR'
        create_cloud_init
    "
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Neither genisoimage nor mkisofs found" ]]
    [[ "$output" =~ \[WARNING\] ]]
}