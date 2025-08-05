#!/usr/bin/env bats

# Load test setup
load setup

setup() {
    setup_test_environment
}

teardown() {
    teardown_test_environment
}

@test "print_status outputs green INFO message" {
    run print_status "Test message"
    [ "$status" -eq 0 ]
    [[ "$output" =~ \[INFO\] ]]
    [[ "$output" =~ "Test message" ]]
    # Check for green color code
    [[ "$output" =~ $'\033[0;32m' ]]
}

@test "print_warning outputs yellow WARNING message" {
    run print_warning "Warning message"
    [ "$status" -eq 0 ]
    [[ "$output" =~ \[WARNING\] ]]
    [[ "$output" =~ "Warning message" ]]
    # Check for yellow color code
    [[ "$output" =~ $'\033[1;33m' ]]
}

@test "print_error outputs red ERROR message" {
    run print_error "Error message"
    [ "$status" -eq 0 ]
    [[ "$output" =~ \[ERROR\] ]]
    [[ "$output" =~ "Error message" ]]
    # Check for red color code
    [[ "$output" =~ $'\033[0;31m' ]]
}

@test "print_status handles empty message" {
    run print_status ""
    [ "$status" -eq 0 ]
    [[ "$output" =~ \[INFO\] ]]
}

@test "print_warning handles special characters" {
    run print_warning "Message with special chars: !@#$%^&*()"
    [ "$status" -eq 0 ]
    [[ "$output" =~ \[WARNING\] ]]
    [[ "$output" =~ "Message with special chars: !@#" ]]
}

@test "print_error handles multiline message" {
    run print_error "Line 1
Line 2"
    [ "$status" -eq 0 ]
    [[ "$output" =~ \[ERROR\] ]]
    [[ "$output" =~ "Line 1" ]]
}

@test "all print functions reset color codes" {
    run print_status "test"
    [[ "$output" =~ $'\033[0m' ]]
    
    run print_warning "test"
    [[ "$output" =~ $'\033[0m' ]]
    
    run print_error "test"
    [[ "$output" =~ $'\033[0m' ]]
}