#!/bin/bash

# Function to print informational messages
print_msg() {
    echo -e "\e[1;34m>>> $1\e[0m"
}

# Function to print error messages
print_err() {
    echo -e "\e[1;31m>>> ERROR: $1\e[0m"
}

# Keep track of test success
BACKEND_FAILED=0
FRONTEND_FAILED=0

# Run backend tests
print_msg "Starting Backend Tests..."
cd repo/backend || exit 1

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run pytest
if pytest; then
    print_msg "Backend Tests Passed!"
else
    print_err "Backend Tests Failed!"
    BACKEND_FAILED=1
fi

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

cd ../.. || exit 1

echo ""

# Run frontend tests
print_msg "Starting Frontend Tests..."
cd repo/frontend || exit 1

# Run vitest
if npm run test:unit; then
    print_msg "Frontend Tests Passed!"
else
    print_err "Frontend Tests Failed!"
    FRONTEND_FAILED=1
fi

cd ../.. || exit 1

echo ""

# Summary
if [ "$BACKEND_FAILED" -eq 1 ] || [ "$FRONTEND_FAILED" -eq 1 ]; then
    print_err "Some tests failed. Check the output above for details."
    exit 1
else
    print_msg "All tests passed successfully!"
    exit 0
fi
