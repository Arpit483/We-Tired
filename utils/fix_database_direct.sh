#!/bin/bash
# Direct database fix script to run on Raspberry Pi
# Run this ON the Raspberry Pi (not from local machine)
echo "=========================================="
echo "Fixing Database Schema"
echo "=========================================="
echo ""
# Find the project directory
if [ -d "/home/pi/VitalRadar" ]; then
    PROJECT_DIR="/home/pi/VitalRadar"
elif [ -d "$HOME/Map1 copy" ]; then
    PROJECT_DIR="$HOME/Map1 copy"
elif [ -d "$HOME/Map1_copy" ]; then
    PROJECT_DIR="$HOME/Map1_copy"
else
    echo "[ERROR] Could not find project directory"
    echo "Please run this script from your project directory"
    exit 1
fi
cd "$PROJECT_DIR"
echo "[*] Project directory: $(pwd)"
# Stop Flask if running
echo "[*] Stopping Flask application..."
pkill -f "python.*app.py" || echo "[!] Flask not running (this is OK)"
# Wait a moment for Flask to stop
sleep 2
# Backup and delete old database
DB_PATH="app/predictions.db"
if [ -f "$DB_PATH" ]; then
    BACKUP_NAME="predictions.db.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$DB_PATH" "$BACKUP_NAME"
    echo "[✓] Database backed up to: $BACKUP_NAME"
    rm -f "$DB_PATH"
    echo "[✓] Old database deleted"
    # Verify deletion
    if [ ! -f "$DB_PATH" ]; then
        echo "[✓] Database file successfully removed"
    else
        echo "[ERROR] Failed to delete database file"
        exit 1
    fi
else
    echo "[!] Database file not found at $DB_PATH (this is OK if it's a fresh install)"
fi
echo ""
echo "=========================================="
echo "Database fix complete!"
echo "=========================================="
echo ""
echo "Next step: Restart Flask to recreate the database with the correct schema:"
echo "  ./start.sh"
echo ""
