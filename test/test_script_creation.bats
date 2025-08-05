#!/usr/bin/env bats

# Load test setup
load setup

setup() {
    setup_test_environment
    mkdir -p "$TEST_VM_DIR"
    cd "$TEST_VM_DIR"
}

teardown() {
    teardown_test_environment
}

@test "create_startup_script creates start-vm.sh file" {
    run create_startup_script
    [ "$status" -eq 0 ]
    [ -f "start-vm.sh" ]
    [[ "$output" =~ "Creating VM startup script" ]]
}

@test "create_startup_script makes script executable" {
    run create_startup_script
    [ "$status" -eq 0 ]
    [ -x "start-vm.sh" ]
}

@test "create_startup_script includes correct VM configuration" {
    run create_startup_script
    [ "$status" -eq 0 ]
    grep -q "VM_DIR=\"$TEST_VM_DIR\"" start-vm.sh
    grep -q "VM_NAME=\"$TEST_VM_NAME\"" start-vm.sh
    grep -q "RAM=\"$TEST_RAM\"" start-vm.sh
    grep -q "CPUS=\"$TEST_CPUS\"" start-vm.sh
    grep -q "SSH_PORT=\"$TEST_SSH_PORT\"" start-vm.sh
}

@test "create_startup_script includes QEMU command with correct parameters" {
    run create_startup_script
    [ "$status" -eq 0 ]
    grep -q "qemu-system-x86_64" start-vm.sh
    grep -q "\-machine type=pc,accel=kvm" start-vm.sh
    grep -q "\-cpu host" start-vm.sh
    grep -q "\-display none" start-vm.sh
    grep -q "\-daemonize" start-vm.sh
}

@test "create_startup_script includes SSH port forwarding" {
    run create_startup_script
    [ "$status" -eq 0 ]
    grep -q "hostfwd=tcp::.*-:22" start-vm.sh
}

@test "create_startup_script includes process detection" {
    run create_startup_script
    [ "$status" -eq 0 ]
    grep -q "pgrep -f" start-vm.sh
    grep -q "VM is already running" start-vm.sh
}

@test "create_stop_script creates stop-vm.sh file" {
    run create_stop_script
    [ "$status" -eq 0 ]
    [ -f "stop-vm.sh" ]
    [[ "$output" =~ "Creating VM stop script" ]]
}

@test "create_stop_script makes script executable" {
    run create_stop_script
    [ "$status" -eq 0 ]
    [ -x "stop-vm.sh" ]
}

@test "create_stop_script includes PID file handling" {
    run create_stop_script
    [ "$status" -eq 0 ]
    grep -q "VM_NAME.pid" stop-vm.sh
    grep -q "kill.*PID" stop-vm.sh
    grep -q "rm -f.*pid" stop-vm.sh
}

@test "create_stop_script includes fallback process killing" {
    run create_stop_script
    [ "$status" -eq 0 ]
    grep -q "pkill -f" stop-vm.sh
    grep -q "qemu.*VM_NAME" stop-vm.sh
}

@test "create_status_script creates status-vm.sh file" {
    run create_status_script
    [ "$status" -eq 0 ]
    [ -f "status-vm.sh" ]
    [[ "$output" =~ "Creating VM status script" ]]
}

@test "create_status_script makes script executable" {
    run create_status_script
    [ "$status" -eq 0 ]
    [ -x "status-vm.sh" ]
}

@test "create_status_script includes SSH connectivity test" {
    run create_status_script
    [ "$status" -eq 0 ]
    grep -q "Testing SSH connection" status-vm.sh
    grep -q "timeout.*ssh" status-vm.sh
    grep -q "SSH: ACCESSIBLE" status-vm.sh
    grep -q "SSH: NOT READY" status-vm.sh
}

@test "create_status_script includes process status checking" {
    run create_status_script
    [ "$status" -eq 0 ]
    grep -q "kill -0.*PID" status-vm.sh
    grep -q "Status: RUNNING" status-vm.sh
    grep -q "Status: STOPPED" status-vm.sh
}

@test "create_status_script includes usage instructions" {
    run create_status_script
    [ "$status" -eq 0 ]
    grep -q "Available commands:" status-vm.sh
    grep -q "./start-vm.sh" status-vm.sh
    grep -q "./stop-vm.sh" status-vm.sh
    grep -q "./status-vm.sh" status-vm.sh
}

@test "all script creation functions print status messages" {
    run create_startup_script
    [ "$status" -eq 0 ]
    [[ "$output" =~ \[INFO\] ]]
    
    run create_stop_script
    [ "$status" -eq 0 ]
    [[ "$output" =~ \[INFO\] ]]
    
    run create_status_script
    [ "$status" -eq 0 ]
    [[ "$output" =~ \[INFO\] ]]
}

@test "startup script includes proper shebang" {
    run create_startup_script
    [ "$status" -eq 0 ]
    head -n 1 start-vm.sh | grep -q "#!/bin/bash"
}

@test "stop script includes proper shebang" {
    run create_stop_script
    [ "$status" -eq 0 ]
    head -n 1 stop-vm.sh | grep -q "#!/bin/bash"
}

@test "status script includes proper shebang" {
    run create_status_script
    [ "$status" -eq 0 ]
    head -n 1 status-vm.sh | grep -q "#!/bin/bash"
}