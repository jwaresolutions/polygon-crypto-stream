#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Reloading systemd daemon...${NC}"
sudo systemctl daemon-reload

echo -e "${YELLOW}Stopping crypto-stream service...${NC}"
sudo systemctl stop crypto-stream
sleep 2  # Give it time to stop cleanly

echo -e "${YELLOW}Starting crypto-stream service...${NC}"
sudo systemctl start crypto-stream
sleep 2  # Give it time to start

# Check if service is running
if systemctl is-active --quiet crypto-stream; then
    echo -e "${GREEN}Service is running successfully${NC}"
else
    echo -e "${RED}Service failed to start${NC}"
fi

# Show current status
echo -e "${YELLOW}Current service status:${NC}"
sudo systemctl status crypto-stream

# Ask if user wants to see logs
read -p "Do you want to watch the logs? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${YELLOW}Showing logs (Ctrl+C to exit):${NC}"
    journalctl -u crypto-stream -f
fi