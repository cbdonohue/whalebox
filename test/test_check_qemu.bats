#!/usr/bin/env bats

# Load test setup
load setup

setup() {
    setup_test_environment
}

teardown() {
    teardown_test_environment
}

@test "check_qemu succeeds when qemu-system-x86_64 is available" {
    # Mock command to simulate qemu being available
    command() {
        if [[ "$1" == "-v" && "$2" == "qemu-system-x86_64" ]]; then
            return 0
        fi
        /usr/bin/command "$@"
    }
    export -f command
    
    run check_qemu
    [ "$status" -eq 0 ]
    [[ ! "$output" =~ "QEMU is not installed" ]]
}

@test "check_qemu fails when qemu-system-x86_64 is not available" {
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
    [[ "$output" =~ "Please install it first" ]]
}

@test "check_qemu shows installation instructions for Ubuntu/Debian" {
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
    [[ "$output" =~ "Ubuntu/Debian: sudo apt install qemu-system-x86 qemu-utils" ]]
}

@test "check_qemu shows installation instructions for Fedora" {
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
    [[ "$output" =~ "Fedora: sudo dnf install qemu-system-x86 qemu-img" ]]
}

@test "check_qemu shows installation instructions for Arch" {
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
    [[ "$output" =~ "Arch: sudo pacman -S qemu-system-x86 qemu-img" ]]
}

@test "check_qemu uses proper error formatting" {
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
    # Check that it uses the print_error function (red color)
    [[ "$output" =~ $'\033[0;31m' ]]
    [[ "$output" =~ \[ERROR\] ]]
}