# Manual Database Fix Steps

Since you're already SSH'd into the Raspberry Pi, follow these steps:

## Step 1: On Raspberry Pi (current SSH session)

Run these commands on the Pi:

```bash
# Navigate to project directory
cd ~/Map1\ copy

# Backup and delete old database
if [ -f "app/predictions.db" ]; then
    BACKUP_NAME="predictions.db.backup.$(date +%Y%m%d_%H%M%S)"
    cp "app/predictions.db" "$BACKUP_NAME"
    echo "[✓] Database backed up to: $BACKUP_NAME"
    rm -f "app/predictions.db"
    echo "[✓] Old database deleted"
else
    echo "[!] Database file not found (this is OK if it's a fresh install)"
fi

# Verify database is deleted
ls -la app/predictions.db 2>/dev/null || echo "[✓] Database file removed"
```

## Step 2: Exit Pi and Deploy from Local Machine

Exit the Pi SSH session:
```bash
exit
```

Then on your local machine, deploy the updated code:
```bash
cd ~/Downloads/Map1\ copy
./deploy_to_pi.sh 192.168.13.16 pi
```

## Step 3: SSH Back into Pi and Start Services

```bash
ssh pi@192.168.13.16
cd ~/Map1\ copy
./start.sh
```

## Step 4: Verify Everything Works

Check the logs:
```bash
# Check Flask logs for database errors
tail -f flask.log

# Check deep learning output
tail -f deep.log
```

The deep learning output should show:
```
  Frame     Dist     Freq      Pwr      Ent  FFT_Conf  DL_Conf   Votes    Detection         Time
```

And the Flask log should show no database errors.

