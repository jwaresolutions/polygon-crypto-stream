# Bitcoin/USD Data Streaming Service

A Python service that streams real-time Bitcoin/USD market data using Polygon.io's API and saves it to daily CSV files. The service captures minute-by-minute data 24/7 and maintains daily statistics.

## Features

- Real-time minute-by-minute BTC/USD data collection
- 24/7 data collection (including weekends)
- Automatic daily file management
- Data quality monitoring and gap detection
- Daily statistics tracking
- Systemd service integration for reliable operation

## Prerequisites

- Python 3.8 or higher
- Polygon.io account (Currencies Starter tier or higher with Crypto data access)
- Linux system with systemd (for service deployment)

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd [repo-directory]
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy configuration template and edit with your API key:
```bash
cp config.template.py config.py
vim config.py  # Replace 'your_polygon_api_key_here' with your actual API key
```

## Service Setup

1. Edit crypto-stream.service:
   - Replace both instances of `{location to source}` with your project path
   - Example: `/home/user/crypto-stream` if your project is in that directory
   - The paths should point to:
     * The venv Python: `/home/user/crypto-stream/venv/bin/python`
     * The service script: `/home/user/crypto-stream/src/crypto_stream_service.py`

2. Copy service file to systemd:
```bash
sudo cp crypto-stream.service /etc/systemd/system/crypto-stream.service
```

3. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable crypto-stream
sudo systemctl start crypto-stream
```

## Common Commands

1. View service status:
```bash
sudo systemctl status crypto-stream
```
2. Watch live logs:
```bash
journalctl -u crypto-stream -f
```
3. Restart service:
```bash
./restart-crypto-service.sh
```
4. Test connection:
```bash
python test_polygon.py
```