#!/usr/bin/env python3
"""
Test runner script for ingest_domestic_2023.py

This script provides a convenient way to run all tests and generate reports.
"""

import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return True if successful."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)

        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print("❌ FAILED")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Run all tests and generate reports."""

    # Python executable path
    python_exe = "C:/code/green-home-search/api/.venv/Scripts/python.exe"

    print("🧪 EPC Data Ingestion Test Suite")
    print("=" * 60)

    # Check if pytest is available
    check_pytest = run_command([python_exe, "-m", "pytest", "--version"], "Checking pytest availability")
    if not check_pytest:
        print("❌ pytest is not available. Please install pytest:")
        print(f"   {python_exe} -m pip install pytest")
        return False

    # Run unit tests
    unit_tests = run_command(
        [python_exe, "-m", "pytest", "test_ingest_domestic_2023.py", "-v", "--tb=short"],
        "Unit Tests"
    )

    # Run integration tests
    integration_tests = run_command(
        [python_exe, "test_integration_ingest.py"],
        "Integration Tests"
    )

    # Run all tests together with summary
    all_tests = run_command(
        [python_exe, "-m", "pytest", ".", "-v", "--tb=short"],
        "All Tests (Summary)"
    )

    # Try to run with coverage if available
    print(f"\n{'='*60}")
    print("Attempting to run with coverage...")
    coverage_available = run_command(
        [python_exe, "-c", "import pytest_cov; print('pytest-cov is available')"],
        "Checking pytest-cov availability"
    )

    if coverage_available:
        run_command(
            [python_exe, "-m", "pytest", ".", "--cov=ingest_domestic_2023", "--cov-report=term-missing"],
            "Tests with Coverage Report"
        )
    else:
        print("ℹ️  pytest-cov not available. To get coverage reports, install it:")
        print(f"   {python_exe} -m pip install pytest-cov")

    # Final summary
    print(f"\n{'='*60}")
    print("🏁 TEST SUMMARY")
    print(f"{'='*60}")

    results = [
        ("Unit Tests", unit_tests),
        ("Integration Tests", integration_tests),
        ("All Tests", all_tests)
    ]

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")

    overall_success = all(result for _, result in results)

    if overall_success:
        print("\n🎉 All tests passed successfully!")
        return True
    else:
        print("\n💥 Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
