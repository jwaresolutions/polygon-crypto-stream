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
    if ! command -v "$1" &> /dev/null; then
        print_warning "$1 is required but not installed."
        return 1
    fi
    return 0
}

# Function to check for root privileges
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "This script must be run as root (with sudo)"
        print_error "Please run: sudo $0"
        exit 1
    fi
}

# First thing: check for root privileges
check_root

# Install prerequisites
print_status "Checking and installing prerequisites..."
if ! apt-get update; then
    print_error "Failed to update package lists. Are you running as root?"
    exit 1
fi

# Install Python and related packages
if ! check_command python3; then
    print_status "Installing Python3..."
    if ! apt-get install -y python3; then
        print_error "Failed to install Python3. Are you running as root?"
        exit 1
    fi
fi

print_status "Installing python3-venv..."
if ! apt-get install -y python3-venv; then
    print_error "Failed to install python3-venv. Are you running as root?"
    exit 1
fi

print_status "Installing pip..."
if ! apt-get install -y python3-pip; then
    print_error "Failed to install pip. Are you running as root?"
    exit 1
fi

# Get the absolute path of the project directory
PROJECT_DIR=$(pwd)
print_status "Project directory: $PROJECT_DIR"

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    if ! python3 -m venv venv; then
        print_error "Failed to create virtual environment"
        exit 1
    fi
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    print_error "Failed to activate virtual environment"
    exit 1
fi

# Install dependencies
if [ -f "requirements.txt" ]; then
    print_status "Installing dependencies..."
    if ! pip install -r requirements.txt; then
        print_error "Failed to install dependencies"
        exit 1
    fi
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Check for config file
if [ ! -f "config.py" ]; then
    if [ -f "config.template.py" ]; then
        print_status "Creating config.py from template..."
        cp config.template.py config.py
        print_warning "Please edit config.py with your Polygon.io API key"
        read -p "Would you like to edit config.py now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-vim} config.py
        fi
    else
        print_error "config.template.py not found"
        exit 1
    fi
fi

# Create data directory if it doesn't exist
print_status "Creating data directory..."
mkdir -p data
print_success "Data directory created/verified"

# Update systemd service file
print_status "Configuring systemd service..."
SERVICE_FILE="crypto-stream.service"
TEMP_SERVICE_FILE="crypto-stream.service.tmp"

# Create temporary service file with correct paths
cat > $TEMP_SERVICE_FILE << EOL
[Unit]
Description=BTCUSD Streaming Data Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/crypto_stream_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Check if service is already installed and running
if systemctl is-active --quiet crypto-stream; then
    print_warning "Crypto stream service is already running"
    
    # Compare existing service file with new one
    if ! cmp -s "/etc/systemd/system/$SERVICE_FILE" "$TEMP_SERVICE_FILE"; then
        print_status "Service file needs updating..."
        sudo cp $TEMP_SERVICE_FILE "/etc/systemd/system/$SERVICE_FILE"
        sudo systemctl daemon-reload
        sudo systemctl restart crypto-stream
        print_success "Service updated and restarted"
    else
        print_success "Service file is up to date"
    fi
else
    # Install new service file
    print_status "Installing service file..."
    cp $TEMP_SERVICE_FILE "/etc/systemd/system/$SERVICE_FILE"
    systemctl daemon-reload
    systemctl enable crypto-stream
    systemctl start crypto-stream
    print_success "Service installed and started"
fi

# Clean up temporary file
rm $TEMP_SERVICE_FILE

# Verify service is running
print_status "Verifying service status..."
if systemctl is-active --quiet crypto-stream; then
    print_success "Service is running"
    
    # Wait a bit and check for data files
    print_status "Waiting 60 seconds to verify data collection..."
    sleep 60
    
    # Check for new data files
    LATEST_FILE=$(ls -t data/BTCUSD_*.csv 2>/dev/null | head -1)
    if [ ! -z "$LATEST_FILE" ]; then
        print_success "Data file created: $LATEST_FILE"
        print_status "Last few records:"
        tail -n 5 "$LATEST_FILE"
    else
        print_warning "No data files found yet. Check logs for issues."
    fi
else
    print_error "Service failed to start"
    echo "Check logs with: journalctl -u crypto-stream -n 50"
fi

# Final status and instructions
echo
print_success "Setup completed!"
echo
echo "Useful commands:"
echo "  - View service status: sudo systemctl status crypto-stream"
echo "  - View logs: journalctl -u crypto-stream -f"
echo "  - Restart service: sudo systemctl restart crypto-stream"
echo "  - Stop service: sudo systemctl stop crypto-stream"
echo
echo "Data files are stored in: $PROJECT_DIR/data/"

# Offer to show logs
read -p "Would you like to view the service logs? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    journalctl -u crypto-stream -f
fi