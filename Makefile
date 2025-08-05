# Makefile for QEMU Runner project

.PHONY: test test-verbose test-quiet test-coverage clean help

# Python executable
PYTHON := python3

# Default target
help:
	@echo "QEMU Runner - Available Make Targets:"
	@echo ""
	@echo "  test          - Run all tests with normal verbosity"
	@echo "  test-verbose  - Run tests with maximum verbosity"
	@echo "  test-quiet    - Run tests with minimal output"
	@echo "  test-coverage - Run tests with coverage analysis"
	@echo "  clean         - Clean up test artifacts and cache files"
	@echo "  help          - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make test                    # Run all tests"
	@echo "  make test-coverage          # Run with coverage"
	@echo "  make clean                  # Clean up files"

# Run tests with normal verbosity
test:
	@echo "Running QEMU Runner tests..."
	$(PYTHON) run_tests.py

# Run tests with maximum verbosity
test-verbose:
	@echo "Running QEMU Runner tests (verbose)..."
	$(PYTHON) run_tests.py -vv

# Run tests with minimal output
test-quiet:
	@echo "Running QEMU Runner tests (quiet)..."
	$(PYTHON) run_tests.py -q

# Run tests with coverage analysis
test-coverage:
	@echo "Running QEMU Runner tests with coverage..."
	$(PYTHON) run_tests.py --coverage

# Clean up test artifacts and cache files
clean:
	@echo "Cleaning up test artifacts..."
	rm -rf __pycache__/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf *.pyc
	rm -rf .pytest_cache/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean completed."

# Quick test run (alias for test)
check: test