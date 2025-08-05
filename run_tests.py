#!/usr/bin/env python3
"""
Test runner for QEMU Runner project
"""

import sys
import unittest
import argparse
from pathlib import Path

def discover_and_run_tests(verbosity=2, pattern='test*.py', start_dir='.'):
    """Discover and run all tests"""
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir, pattern=pattern)
    
    runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_specific_test(test_name, verbosity=2):
    """Run a specific test class or method"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_name)
    
    runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='QEMU Runner Test Suite')
    parser.add_argument('--verbose', '-v', action='count', default=1,
                       help='Increase verbosity (can be used multiple times)')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output')
    parser.add_argument('--pattern', '-p', default='test*.py',
                       help='Test file pattern (default: test*.py)')
    parser.add_argument('--test', '-t',
                       help='Run specific test (e.g., test_qemu_runner.TestQEMURunner.test_find_qemu_binary_success)')
    parser.add_argument('--coverage', '-c', action='store_true',
                       help='Run with coverage analysis (requires coverage.py)')
    
    args = parser.parse_args()
    
    # Determine verbosity level
    if args.quiet:
        verbosity = 0
    else:
        verbosity = args.verbose
    
    # Handle coverage
    if args.coverage:
        try:
            import coverage
            cov = coverage.Coverage()
            cov.start()
        except ImportError:
            print("Coverage analysis requires 'coverage' package.")
            print("Install with: pip install coverage")
            return 1
    
    try:
        # Run tests
        if args.test:
            success = run_specific_test(args.test, verbosity)
        else:
            success = discover_and_run_tests(verbosity, args.pattern)
        
        # Handle coverage reporting
        if args.coverage:
            cov.stop()
            cov.save()
            
            print("\n" + "="*50)
            print("COVERAGE REPORT")
            print("="*50)
            cov.report(show_missing=True)
            
            # Generate HTML report
            html_dir = Path('htmlcov')
            cov.html_report(directory=str(html_dir))
            print(f"\nHTML coverage report generated in: {html_dir}")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())