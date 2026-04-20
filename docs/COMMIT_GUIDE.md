# Committing Changes on Raspberry Pi

## Quick Commit

To commit all changes directly on the Raspberry Pi:

```bash
# Option 1: Deploy and commit in one step
./deploy_and_commit.sh raspberrypi.local pi

# Option 2: Just commit (if files already deployed)
./commit_on_pi.sh raspberrypi.local pi "Your commit message"
```

## Manual Commit on Pi

If you prefer to commit manually after SSH'ing into the Pi:

```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local
# Password: 21291645

# Navigate to project
cd /home/pi/VitalRadar

# Initialize git (if not already done)
git init

# Create .gitignore (if not exists)
cat > .gitignore << 'EOF'
*.log
*.db
__pycache__/
*.pyc
venv/
.pids
EOF

# Add all files
git add -A

# Commit
git commit -m "Update: GPS integration, map visualization, and connection fixes"

# View commit
git log
```

## Commit Messages

Suggested commit messages:

- `"Add GPS integration and map visualization"`
- `"Fix connection refused errors with retry logic"`
- `"Update: GPS integration, map visualization, connection fixes"`
- `"Add wait_for_flask.py and improve startup sequence"`
- `"Update deep.py to fetch GPS on person detection"`

## Viewing Commits

On Raspberry Pi:
```bash
cd /home/pi/VitalRadar
git log
git log --oneline
git status
git diff
```

## Git Configuration (Optional)

If you want to set up git user info on the Pi:

```bash
ssh pi@raspberrypi.local
cd /home/pi/VitalRadar
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

## Files Included in Commit

The commit will include:
- ✅ All Python scripts (deep.py, app.py, etc.)
- ✅ Configuration files (requirements.txt, .gitignore)
- ✅ Startup scripts (start.sh, wait_for_flask.py)
- ✅ App directory (routes, models, templates)
- ✅ Deployment scripts

Excluded (via .gitignore):
- ❌ Log files (*.log)
- ❌ Database files (*.db)
- ❌ Python cache (__pycache__/)
- ❌ Virtual environment (venv/)
- ❌ Temporary files (.pids)

