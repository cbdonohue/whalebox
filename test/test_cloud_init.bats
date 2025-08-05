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

@test "create_cloud_init creates user-data file" {
    run create_cloud_init
    [ "$status" -eq 0 ]
    [ -f "user-data" ]
    [[ "$output" =~ "Creating cloud-init configuration" ]]
}

@test "create_cloud_init creates meta-data file" {
    run create_cloud_init
    [ "$status" -eq 0 ]
    [ -f "meta-data" ]
}

@test "create_cloud_init user-data contains cloud-config header" {
    run create_cloud_init
    [ "$status" -eq 0 ]
    grep -q "#cloud-config" user-data
}

@test "create_cloud_init user-data configures ubuntu user" {
    run create_cloud_init
    [ "$status" -eq 0 ]
    grep -q "name: ubuntu" user-data
    grep -q "sudo: ALL=(ALL) NOPASSWD:ALL" user-data
    grep -q "shell: /bin/bash" user-data
}

@test "create_cloud_init user-data includes SSH configuration" {
    run create_cloud_init
    [ "$status" -eq 0 ]
    grep -q "ssh_authorized_keys:" user-data
    grep -q "ssh_pwauth: true" user-data
    grep -q "disable_root: false" user-data
}

@test "create_cloud_init user-data includes essential packages" {
    run create_cloud_init
    [ "$status" -eq 0 ]
    grep -q "packages:" user-data
    grep -q "openssh-server" user-data
    grep -q "curl" user-data
    grep -q "wget" user-data
    grep -q "git" user-data
    grep -q "htop" user-data
    grep -q "vim" user-data
    grep -q "net-tools" user-data
}

@test "create_cloud_init user-data configures SSH service" {
    run create_cloud_init
    [ "$status" -eq 0 ]
    grep -q "systemctl enable ssh" user-data
    grep -q "systemctl start ssh" user-data
    grep -q "systemctl restart ssh" user-data
}

@test "create_cloud_init user-data configures firewall" {
    run create_cloud_init
    [ "$status" -eq 0 ]
    grep -q "ufw --force enable" user-data
    grep -q "ufw allow ssh" user-data
}

@test "create_cloud_init meta-data contains instance information" {
    run create_cloud_init
    [ "$status" -eq 0 ]
    grep -q "instance-id: $VM_NAME" meta-data
    grep -q "local-hostname: $VM_NAME" meta-data
}

@test "create_cloud_init creates ISO with genisoimage when available" {
    # Mock command to simulate genisoimage being available
    command() {
        if [[ "$1" == "-v" && "$2" == "genisoimage" ]]; then
            return 0
        fi
        /usr/bin/command "$@"
    }
    export -f command
    
    run create_cloud_init
    [ "$status" -eq 0 ]
    [[ "$output" =~ "genisoimage mock called" ]]
    [ -f "cloud-init.iso" ]
}

@test "create_cloud_init creates ISO with mkisofs when genisoimage unavailable" {
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
    
    run create_cloud_init
    [ "$status" -eq 0 ]
    [[ "$output" =~ "genisoimage mock called" ]]  # Our mock handles both
    [ -f "cloud-init.iso" ]
}

@test "create_cloud_init warns when no ISO tools available" {
    # Mock command to simulate neither tool being available
    command() {
        if [[ "$1" == "-v" && ("$2" == "genisoimage" || "$2" == "mkisofs") ]]; then
            return 1
        fi
        /usr/bin/command "$@"
    }
    export -f command
    
    run create_cloud_init
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Neither genisoimage nor mkisofs found" ]]
    [[ "$output" =~ "Cloud-init ISO not created" ]]
    [[ "$output" =~ \[WARNING\] ]]
}

@test "create_cloud_init ISO uses correct parameters" {
    # Mock command to simulate genisoimage being available
    command() {
        if [[ "$1" == "-v" && "$2" == "genisoimage" ]]; then
            return 0
        fi
        /usr/bin/command "$@"
    }
    export -f command
    
    run create_cloud_init
    [ "$status" -eq 0 ]
    [[ "$output" =~ "genisoimage mock called with args: -output cloud-init.iso -volid cidata -joliet -rock user-data meta-data" ]]
}

@test "create_cloud_init user-data includes password hash" {
    run create_cloud_init
    [ "$status" -eq 0 ]
    grep -q "passwd: \$6\$rounds=4096" user-data
    grep -q "lock_passwd: false" user-data
}