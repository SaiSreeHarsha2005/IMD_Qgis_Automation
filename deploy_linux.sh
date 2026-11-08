#!/usr/bin/env bash
set -e

echo "=================================================================="
echo "  IMD Hyderabad — Automated Map Generation Deployment on Ubuntu"
echo "=================================================================="
echo

if [ "$EUID" -ne 0 ]; then
    echo "[!] Please run with sudo: sudo ./deploy_linux.sh"
    exit 1
fi

echo "[1/4] Installing System Packages & QGIS Engine..."
apt-get update -y
apt-get install -y qgis python3-qgis xvfb fonts-dejavu fonts-liberation python3-openpyxl python3-pip

echo "[2/4] Verifying Python Dependencies..."
python3 -c "import openpyxl; from qgis.core import QgsApplication; print('[OK] QGIS & openpyxl available!')"

echo "[3/4] Setting Permissions..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod -R 775 "$SCRIPT_DIR"
mkdir -p "$SCRIPT_DIR/logs" "$SCRIPT_DIR/output" "$SCRIPT_DIR/data/input"

echo "[4/4] Creating systemd service..."
cat <<EOF > /etc/systemd/system/imd-dashboard.service
[Unit]
Description=IMD Hyderabad Automated Map Generation Dashboard
After=network.target

[Service]
Type=simple
User=$(logname 2>/dev/null || echo root)
WorkingDirectory=$SCRIPT_DIR
Environment="QT_QPA_PLATFORM=offscreen"
Environment="PYTHONPATH=$SCRIPT_DIR:$SCRIPT_DIR/scripts:$SCRIPT_DIR/utils"
ExecStart=/usr/bin/python3 $SCRIPT_DIR/serve_dashboard.py 8765
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable imd-dashboard
systemctl restart imd-dashboard

echo
echo "=================================================================="
echo "  [SUCCESS] Deployment complete!"
echo "  Service Status: systemctl status imd-dashboard"
echo "  Dashboard URL : http://192.27.21.222:8765/templates/dashboard.html"
echo "                  (or http://192.168.156.220:8765/templates/dashboard.html)"
echo "=================================================================="
