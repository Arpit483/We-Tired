# Troubleshooting SSH Connection to Raspberry Pi

## Quick Diagnostic Steps

### 1. Test Basic Connectivity

First, check if the Pi is reachable on the network:

```bash
# Ping the Pi
ping -c 4 192.168.13.16

# If ping fails, try to find the Pi on the network
arp -a | grep -i "b8:27:eb\|dc:a6:32\|e4:5f:01"
```

### 2. Test SSH Connection Manually

Try connecting manually to see the exact error:

```bash
# Test SSH connection (will prompt for password)
ssh -v pi@192.168.13.16

# Or with password inline (if sshpass is installed)
sshpass -p "21291645" ssh -v pi@192.168.13.16 "echo 'Connection successful'"
```

**Common SSH errors:**
- `Connection refused` → SSH service not running on Pi
- `Connection timed out` → Pi not on network or firewall blocking
- `Permission denied` → Wrong password or username
- `Host key verification failed` → SSH key issue

### 3. Check if SSH is Enabled on Raspberry Pi

**If you have physical access to the Pi:**

```bash
# SSH into Pi (if you can access it another way)
# Then check SSH status:
sudo systemctl status ssh

# Enable SSH if disabled:
sudo systemctl enable ssh
sudo systemctl start ssh

# Check SSH is listening:
sudo netstat -tlnp | grep :22
```

**Or enable SSH via Raspberry Pi configuration:**
```bash
sudo raspi-config
# Navigate to: Interface Options → SSH → Enable
```

### 4. Find the Correct IP Address

The Pi's IP might have changed. Try these methods:

**On the Pi itself:**
```bash
# Run on Raspberry Pi
hostname -I
# or
ip addr show
```

**From your computer (if Pi is on same network):**
```bash
# Scan local network for Raspberry Pi
nmap -sn 192.168.13.0/24 | grep -B 2 "Raspberry Pi"

# Or try common hostnames
ping raspberrypi.local
ping raspberrypi
```

### 5. Alternative Connection Methods

**Option A: Use hostname instead of IP**
```bash
# Try using hostname
./deploy_to_pi.sh raspberrypi.local pi
```

**Option B: Connect via USB/Ethernet**
If you have USB-to-Ethernet or direct Ethernet connection, the IP might be different.

**Option C: Use VNC or Physical Access**
If you can access the Pi via VNC or physically, you can:
1. Enable SSH via GUI or command line
2. Find the correct IP address
3. Update the scripts with the correct IP

### 6. Check Firewall Settings

**On Raspberry Pi:**
```bash
# Check if firewall is blocking SSH
sudo ufw status

# Allow SSH if needed
sudo ufw allow ssh
sudo ufw allow 22/tcp
```

**On your Mac (if firewall is blocking outbound):**
```bash
# Check firewall status
/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

### 7. Verify Username and Password

**Test with explicit credentials:**
```bash
# Test SSH with verbose output
sshpass -p "21291645" ssh -v -o StrictHostKeyChecking=no pi@192.168.13.16 "whoami"
```

If this works, the issue is with the script. If it doesn't, the credentials might be wrong.

### 8. Check SSH Key Issues

Sometimes SSH keys can cause issues:

```bash
# Remove old SSH key for this host
ssh-keygen -R 192.168.13.16

# Or remove all keys and try again
ssh-keygen -R raspberrypi.local
```

### 9. Manual File Transfer (If SSH Works Manually)

If SSH works manually but scripts fail, you can transfer files manually:

```bash
# Create a tarball of your project
cd "/Users/adityasunildolas/Downloads/Map1 copy"
tar -czf vitalradar.tar.gz app/ app.py deep.py *.sh *.md requirements.txt *.pt

# Transfer manually
scp vitalradar.tar.gz pi@192.168.13.16:/home/pi/

# Then SSH in and extract
ssh pi@192.168.13.16
cd /home/pi
tar -xzf vitalradar.tar.gz -C VitalRadar/
```

### 10. Test Script with Verbose Output

Modify the script temporarily to see more details:

```bash
# Edit deploy_to_pi.sh and change the SSH test line to:
sshpass -p "$PI_PASSWORD" ssh -v -o StrictHostKeyChecking=no "$PI_USER@$PI_IP" "echo 'Connection successful'"
```

## Quick Fixes

### Fix 1: Enable SSH on Pi (if you have access)

```bash
# On Raspberry Pi
sudo systemctl enable ssh
sudo systemctl start ssh
sudo systemctl status ssh
```

### Fix 2: Update IP Address

If you found a different IP:

```bash
# Update all scripts with new IP
# Or use hostname
./deploy_to_pi.sh raspberrypi.local pi
```

### Fix 3: Check Network Connection

```bash
# On Pi, check network
ping -c 4 8.8.8.8  # Test internet
ip addr show       # Check IP assignment
```

## Still Not Working?

1. **Physical Access**: If you have physical access to the Pi, connect a monitor/keyboard and:
   - Check the IP: `hostname -I`
   - Enable SSH: `sudo systemctl enable ssh && sudo systemctl start ssh`
   - Check network: `ip addr show`

2. **Different Network**: Make sure your computer and Pi are on the same network/subnet

3. **Router Issues**: Some routers isolate devices. Check router settings for "AP Isolation" or "Client Isolation"

4. **Try Different Port**: If SSH is on a non-standard port:
   ```bash
   ssh -p 2222 pi@192.168.13.16
   ```

## Success Indicators

When SSH is working, you should see:
```bash
$ ssh pi@192.168.13.16
pi@192.168.13.16's password: 
# After entering password, you get a shell prompt
pi@raspberrypi:~ $
```

If you see this, SSH is working and the scripts should work too!

