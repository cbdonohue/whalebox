#!/usr/bin/env bats

# Load test setup
load setup

setup() {
    setup_test_environment
    enable_mocks
    mkdir -p "$TEST_VM_DIR"
    cd "$TEST_VM_DIR"
    # Create dummy user-data file
    cat > user-data << 'EOF'
#cloud-config
users:
  - name: ubuntu
    ssh_authorized_keys:
      - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7... # This will be replaced with your actual key
EOF
}

teardown() {
    disable_mocks
    teardown_test_environment
}

@test "setup_ssh_key generates SSH key when it doesn't exist" {
    # Use a test SSH key path
    export SSH_KEY_PATH="/tmp/test_id_rsa"
    export HOME="/tmp"
    
    run setup_ssh_key
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Generating SSH key pair" ]]
    [[ "$output" =~ "ssh-keygen mock called" ]]
    [ -f "/tmp/test_id_rsa" ]
    [ -f "/tmp/test_id_rsa.pub" ]
}

@test "setup_ssh_key skips generation when key exists" {
    # Create dummy SSH key files
    export SSH_KEY_PATH="/tmp/test_id_rsa"
    export HOME="/tmp"
    mkdir -p "/tmp/.ssh"
    echo "existing-key" > "/tmp/.ssh/id_rsa"
    echo "ssh-rsa existing-public-key" > "/tmp/.ssh/id_rsa.pub"
    
    run setup_ssh_key
    [ "$status" -eq 0 ]
    [[ ! "$output" =~ "Generating SSH key pair" ]]
    [[ ! "$output" =~ "ssh-keygen mock called" ]]
}

@test "setup_ssh_key updates user-data with actual SSH key" {
    # Use a test SSH key path
    export SSH_KEY_PATH="/tmp/test_id_rsa"
    export HOME="/tmp"
    
    run setup_ssh_key
    [ "$status" -eq 0 ]
    
    # Check that the placeholder was replaced
    ! grep -q "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7..." user-data
    grep -q "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7dummy-public-key test@example.com" user-data
}

@test "setup_ssh_key recreates cloud-init ISO after key update" {
    # Mock command to simulate genisoimage being available
    command() {
        if [[ "$1" == "-v" && "$2" == "genisoimage" ]]; then
            return 0
        fi
        /usr/bin/command "$@"
    }
    export -f command
    
    # Use a test SSH key path
    export SSH_KEY_PATH="/tmp/test_id_rsa"
    export HOME="/tmp"
    
    # Create dummy existing ISO
    touch cloud-init.iso
    
    run setup_ssh_key
    [ "$status" -eq 0 ]
    [[ "$output" =~ "genisoimage mock called" ]]
    [ -f "cloud-init.iso" ]
}

@test "setup_ssh_key uses correct ssh-keygen parameters" {
    # Use a test SSH key path
    export SSH_KEY_PATH="/tmp/test_id_rsa"
    export HOME="/tmp"
    
    run setup_ssh_key
    [ "$status" -eq 0 ]
    [[ "$output" =~ "ssh-keygen mock called with args: -t rsa -b 4096 -f /tmp/.ssh/id_rsa -N " ]]
}

@test "setup_ssh_key handles missing SSH key file gracefully" {
    # Use a test SSH key path that won't be created
    export SSH_KEY_PATH="/tmp/nonexistent_key"
    export HOME="/tmp"
    
    # Override mock to not create files
    mock_ssh_keygen() {
        echo "ssh-keygen mock called with args: $*"
        # Don't create files to simulate failure
    }
    export -f mock_ssh_keygen
    
    run setup_ssh_key
    [ "$status" -eq 0 ]
    # Should still complete without error, just won't update user-data
}

@test "setup_ssh_key removes existing ISO before recreating" {
    # Mock command to simulate genisoimage being available
    command() {
        if [[ "$1" == "-v" && "$2" == "genisoimage" ]]; then
            return 0
        fi
        /usr/bin/command "$@"
    }
    export -f command
    
    # Use a test SSH key path
    export SSH_KEY_PATH="/tmp/test_id_rsa"
    export HOME="/tmp"
    
    # Create dummy existing ISO with content
    echo "old iso content" > cloud-init.iso
    
    run setup_ssh_key
    [ "$status" -eq 0 ]
    
    # Verify ISO was recreated (our mock creates empty file)
    [ -f "cloud-init.iso" ]
    [ ! -s "cloud-init.iso" ]  # Should be empty from mock
}

@test "setup_ssh_key works with mkisofs fallback" {
    # Mock command to simulate only mkisofs being available
    command() {
        if [[ "$1" == "-v" && "$2" == "genisoimage" ]]; then
            return 1
        elif [[ "$1" == "-v" && "$2" == "mkisofs" ]]; then
            return 0
        fi
        /usr/bin/command "$@"
    }
    export -f command
    
    # Use a test SSH key path
    export SSH_KEY_PATH="/tmp/test_id_rsa"
    export HOME="/tmp"
    
    run setup_ssh_key
    [ "$status" -eq 0 ]
    [ -f "cloud-init.iso" ]
}