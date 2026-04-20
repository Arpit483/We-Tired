#!/usr/bin/env python3
"""
Check if deep learning script is actually processing both sensors
"""

import subprocess
import time
import re

def check_deep_learning_logs():
    """Check recent deep learning output for both sensors"""
    print("🔍 Checking Deep Learning Output:")
    print("-" * 40)
    
    try:
        # Check if deep_optimized.py is running
        result = subprocess.run(['pgrep', '-f', 'deep_optimized.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✅ deep_optimized.py running (PIDs: {', '.join(pids)})")
        else:
            print("❌ deep_optimized.py not running!")
            return False
        
        # Check log files for sensor output
        log_files = ['deep.log', 'deep_learning.log', 'deep_corrected.log']
        
        for log_file in log_files:
            try:
                import os
                project_dir = os.path.dirname(os.path.abspath(__file__))
                result = subprocess.run(['tail', '-20', log_file], 
                                      capture_output=True, text=True, cwd=project_dir)
                if result.returncode == 0 and result.stdout.strip():
                    print(f"\n📄 Recent output from {log_file}:")
                    lines = result.stdout.strip().split('\n')
                    
                    s1_count = 0
                    s2_count = 0
                    
                    for line in lines[-10:]:  # Last 10 lines
                        if '[S1]' in line:
                            s1_count += 1
                            print(f"   S1: {line.strip()}")
                        elif '[S2]' in line:
                            s2_count += 1
                            print(f"   S2: {line.strip()}")
                    
                    print(f"\n   📊 Sensor activity: S1={s1_count} lines, S2={s2_count} lines")
                    
                    if s1_count > 0 and s2_count > 0:
                        print("   ✅ Both sensors active in logs")
                        return True
                    elif s1_count > 0:
                        print("   ⚠️  Only S1 (left) sensor active")
                        return False
                    elif s2_count > 0:
                        print("   ⚠️  Only S2 (right) sensor active")
                        return False
                    else:
                        print("   ❌ No sensor activity in recent logs")
                        
            except Exception as e:
                print(f"   ❌ Could not read {log_file}: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        return False

def check_sensor_devices():
    """Check if both sensor devices are accessible"""
    print("\n🔌 Checking Sensor Devices:")
    print("-" * 40)
    
    import os
    
    sensors = ['/dev/ttyUSB0', '/dev/ttyUSB1']
    accessible = []
    
    for sensor in sensors:
        if os.path.exists(sensor):
            try:
                # Try to check if device is accessible
                result = subprocess.run(['ls', '-la', sensor], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   ✅ {sensor}: {result.stdout.strip()}")
                    accessible.append(sensor)
                else:
                    print(f"   ❌ {sensor}: Not accessible")
            except Exception as e:
                print(f"   ❌ {sensor}: Error - {e}")
        else:
            print(f"   ❌ {sensor}: Not found")
    
    return len(accessible) == 2

def restart_deep_learning():
    """Restart the deep learning script"""
    print("\n🔄 Restarting Deep Learning Script:")
    print("-" * 40)
    
    try:
        # Kill existing processes
        subprocess.run(['pkill', '-f', 'deep_optimized.py'], 
                      capture_output=True)
        print("   🛑 Stopped existing processes")
        
        time.sleep(2)
        
        # Start new process
        import os
        project_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.run(['bash', '-c', 
                       f'cd "{project_dir}" && source venv/bin/activate && nohup python3 deep_optimized.py > deep_restart.log 2>&1 &'],
                      capture_output=True)
        print("   🚀 Started new deep_optimized.py process")
        
        time.sleep(3)
        
        # Check if it started
        result = subprocess.run(['pgrep', '-f', 'deep_optimized.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Process started successfully (PID: {result.stdout.strip()})")
            return True
        else:
            print("   ❌ Failed to start process")
            return False
            
    except Exception as e:
        print(f"   ❌ Restart failed: {e}")
        return False

def main():
    print("🔧 Deep Learning Sensor Check")
    print("=" * 50)
    
    # Step 1: Check sensor devices
    devices_ok = check_sensor_devices()
    
    # Step 2: Check deep learning output
    sensors_active = check_deep_learning_logs()
    
    # Step 3: If issues found, restart
    if not sensors_active:
        print("\n⚠️  Issues detected with sensor processing")
        print("🔄 Attempting to restart deep learning script...")
        
        if restart_deep_learning():
            print("\n✅ Deep learning script restarted")
            print("   Wait 30 seconds then check website for right sensor data")
        else:
            print("\n❌ Failed to restart deep learning script")
            print("   Manual intervention required")
    else:
        print("\n✅ Both sensors appear to be working")
        print("   Issue may be elsewhere in the pipeline")

if __name__ == "__main__":
    main()