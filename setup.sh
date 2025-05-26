#!/bin/bash

# Color definitions
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored status messages
print_status() {
    echo -e "${BLUE}[STATUS]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_warning "$1 is required but not installed."
        return 1
    fi
    return 0
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Install prerequisites
print_status "Checking and installing prerequisites..."
apt-get update

# Install Python and related packages
if ! check_command python3; then
    print_status "Installing Python3..."
    apt-get install -y python3
fi

print_status "Installing python3-venv..."
apt-get install -y python3-venv

print_status "Installing pip..."
apt-get install -y python3-pip

# Rest of the original script continues here...