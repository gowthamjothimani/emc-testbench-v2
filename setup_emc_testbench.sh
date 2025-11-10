#!/bin/bash
# ===============================================
#  Automated Deployment Script for BeagleBone
#  Author : Guru
#  Purpose: Clone repo, install deps, and deploy
# ===============================================

set -e

# -------- CONFIGURATION --------
REPO_URL="https://github.com/gowthamjothimani/emc-testbench-v2.git"
APP_DIR="$HOME/emc-testbench-v2"
PYTHON_BIN="python3"
PIP_BIN="pip3"
REQUIREMENTS=(
    flask
    flask-socketio
    minimalmodbus
    psutil
    paho-mqtt
)

# -------- FUNCTIONS --------
update_system() {
    echo "🔄 Updating system packages..."
    sudo apt update -y
    sudo apt install -y git python3 python3-pip python3-venv python3-setuptools python3-wheel
}

upgrade_pip() {
    echo "🚀 Upgrading pip, setuptools, and wheel..."
    sudo ${PIP_BIN} install --upgrade pip setuptools wheel
}

clone_repo() {
    echo "📦 Cloning repository..."
    if [ -d "$APP_DIR" ]; then
        echo "➡️  Repo already exists, pulling latest changes..."
        cd "$APP_DIR" && git pull
    else
        git clone "$REPO_URL" "$APP_DIR"
    fi
}

create_venv() {
    echo "🐍 Creating Python virtual environment..."
    cd "$APP_DIR"
    if [ ! -d "venv" ]; then
        ${PYTHON_BIN} -m venv venv
    fi
    source venv/bin/activate
}

install_requirements() {
    echo "📦 Installing Python dependencies..."
    ${PIP_BIN} install --upgrade pip setuptools wheel

    # Fix for BeagleBone/ARM builds
    ${PIP_BIN} install markupsafe==2.1.3

    for pkg in "${REQUIREMENTS[@]}"; do
        echo "➡️  Installing $pkg..."
        ${PIP_BIN} install "$pkg"
    done
}

start_app() {
    echo "🚀 Starting Flask application..."
    cd "$APP_DIR"
    source venv/bin/activate
    nohup ${PYTHON_BIN} app.py > app.log 2>&1 &
    echo "✅ App started successfully! Logs -> $APP_DIR/app.log"
}

# -------- MAIN EXECUTION --------
echo "==============================================="
echo "     🚀 EMC Testbench Auto Deployment"
echo "==============================================="

update_system
upgrade_pip
clone_repo
create_venv
install_requirements
start_app

echo "==============================================="
echo "✅ Deployment Completed Successfully!"
echo "==============================================="
