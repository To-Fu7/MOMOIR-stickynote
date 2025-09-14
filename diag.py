#!/usr/bin/env python3
"""
Fixed Windows MQTT diagnostic script compatible with paho-mqtt 2.0+
"""

import sys
import time
import json
import socket

def pause_for_input(message="Press Enter to continue..."):
    """Pause execution and wait for user input"""
    input(f"\n{message}")

def check_python_version():
    """Check Python version compatibility"""
    print("=== Python Version Check ===")
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 6):
        print("WARNING: Python 3.6+ recommended")
    else:
        print("✓ Python version OK")
    return True

def check_paho_mqtt():
    """Check if paho-mqtt is installed and get version"""
    print("\n=== MQTT Library Check ===")
    try:
        import paho.mqtt.client as mqtt
        print("✓ paho-mqtt library is installed")
        
        # Try to get version
        version = "Unknown"
        if hasattr(mqtt, '__version__'):
            version = mqtt.__version__
        elif hasattr(mqtt, 'VERSION_NUMBER'):
            version = f"{mqtt.VERSION_NUMBER}"
        
        print(f"Version: {version}")
        
        # Check if it's version 2.0+
        try:
            # Try to access CallbackAPIVersion (only exists in 2.0+)
            if hasattr(mqtt, 'CallbackAPIVersion'):
                print("✓ Detected paho-mqtt 2.0+ (using new callback API)")
                return True, "2.0+"
            else:
                print("✓ Detected paho-mqtt 1.x (using legacy callback API)")
                return True, "1.x"
        except:
            print("✓ Using legacy callback API")
            return True, "1.x"
            
    except ImportError as e:
        print("✗ paho-mqtt library NOT installed")
        print(f"Error: {e}")
        print("\nTo install, run:")
        print("pip install paho-mqtt")
        return False, None

def check_network_connectivity():
    """Check basic network connectivity"""
    print("\n=== Network Connectivity Check ===")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('8.8.8.8', 53))
        sock.close()
        
        if result == 0:
            print("✓ Internet connectivity OK")
            return True
        else:
            print("✗ No internet connectivity detected")
            return False
    except Exception as e:
        print(f"✗ Network check failed: {e}")
        return False

def check_mqtt_broker_port():
    """Check if MQTT broker is running on localhost:1883"""
    print("\n=== MQTT Broker Check ===")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('10.11.0.34', 1883))
        sock.close()
        
        if result == 0:
            print("✓ MQTT broker is running on localhost:1883")
            return True
        else:
            print("✗ No MQTT broker found on localhost:1883")
            print(f"Connection error code: {result}")
            return False
    except Exception as e:
        print(f"✗ Error checking MQTT broker: {e}")
        return False

def show_mqtt_installation_guide():
    """Show MQTT broker installation instructions for Windows"""
    print("\n=== MQTT Broker Installation Guide for Windows ===")
    print("\nOption 1: Eclipse Mosquitto (Recommended)")
    print("1. Download from: https://mosquitto.org/download/")
    print("2. Choose 'mosquitto-x.x.x-install-windows-x64.exe'")
    print("3. Install with default settings")
    print("4. Mosquitto will start automatically as a Windows service")
    print("\nOption 2: Using Command Line")
    print("1. Open Command Prompt as Administrator")
    print("2. Run: winget install EclipseFoundation.Mosquitto")
    print("\nOption 3: Using Docker")
    print("1. Install Docker Desktop")
    print("2. Run: docker run -it -p 1883:1883 eclipse-mosquitto")

def simple_mqtt_test(mqtt_version):
    """Perform a simple MQTT test compatible with both v1.x and v2.0+"""
    print("\n=== Simple MQTT Test ===")
    
    try:
        import paho.mqtt.client as mqtt
        
        print("Creating MQTT client...")
        
        # Create client compatible with both versions
        if mqtt_version == "2.0+":
            # For paho-mqtt 2.0+, specify the callback API version
            client = mqtt.Client(
                client_id="windows_test_client",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1  # Use v1 callbacks for compatibility
            )
        else:
            # For paho-mqtt 1.x
            client = mqtt.Client(client_id="windows_test_client")
        
        # Connection tracking
        connected = [False]
        connect_error = [None]
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                connected[0] = True
                print("✓ Successfully connected to MQTT broker")
            else:
                error_messages = {
                    1: "Connection refused - incorrect protocol version",
                    2: "Connection refused - invalid client identifier", 
                    3: "Connection refused - server unavailable",
                    4: "Connection refused - bad username or password",
                    5: "Connection refused - not authorized"
                }
                error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
                print(f"✗ Connection failed: {error_msg}")
                connect_error[0] = error_msg
        
        def on_publish(client, userdata, mid):
            print(f"✓ Message published successfully (ID: {mid})")
        
        def on_disconnect(client, userdata, rc):
            if rc != 0:
                print(f"Unexpected disconnection (code: {rc})")
            else:
                print("✓ Cleanly disconnected from broker")
        
        # Set callbacks
        client.on_connect = on_connect
        client.on_publish = on_publish  
        client.on_disconnect = on_disconnect
        
        print(f"Attempting to connect to localhost:1883... (using MQTT {mqtt_version})")
        try:
            client.connect("localhost", 1883, 60)
            client.loop_start()
            
            # Wait up to 10 seconds for connection
            for i in range(10):
                if connected[0] or connect_error[0]:
                    break
                time.sleep(1)
                print(f"Waiting for connection... ({i+1}/10)")
            
            if connected[0]:
                print("✓ MQTT connection test successful!")
                
                # Try publishing a test message
                print("Publishing test message...")
                test_data = {
                    "status": "test",
                    "message": "Hello from Windows diagnostic tool!",
                    "timestamp": time.time(),
                    "mqtt_version": mqtt_version
                }
                
                result = client.publish("/test/diagnostic", json.dumps(test_data), qos=1)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print("✓ Test message queued for publishing")
                    time.sleep(1)  # Give it time to publish
                else:
                    print(f"✗ Failed to publish test message: {result.rc}")
                    
            elif connect_error[0]:
                print(f"✗ Connection failed: {connect_error[0]}")
            else:
                print("✗ Connection timeout - broker may not be running")
            
            client.loop_stop()
            client.disconnect()
            time.sleep(1)  # Give it time to disconnect cleanly
            
        except Exception as e:
            print(f"✗ Connection attempt failed: {e}")
            
    except ImportError:
        print("Cannot perform MQTT test - paho-mqtt not installed")

def show_code_fix_instructions(mqtt_version):
    """Show how to fix the main application code"""
    print("\n=== Code Fix Instructions ===")
    if mqtt_version == "2.0+":
        print("Your main application needs to be updated for paho-mqtt 2.0+")
        print("\nIn your main application, change the MQTT client creation from:")
        print("  self.mqtt_client = mqtt.Client()")
        print("\nTo:")
        print("  self.mqtt_client = mqtt.Client(")
        print("      callback_api_version=mqtt.CallbackAPIVersion.VERSION1")
        print("  )")
        print("\nOr alternatively, downgrade to paho-mqtt 1.x:")
        print("  pip uninstall paho-mqtt")
        print("  pip install paho-mqtt==1.6.1")
    else:
        print("Your paho-mqtt version should be compatible with the existing code")

def main():
    """Main diagnostic function"""
    print("MQTT Diagnostic Tool for Windows (Fixed for v2.0+)")
    print("=" * 60)
    
    # Step 1: Check Python
    check_python_version()
    pause_for_input()
    
    # Step 2: Check MQTT library
    mqtt_available, mqtt_version = check_paho_mqtt()
    pause_for_input()
    
    # Step 3: Check network
    check_network_connectivity()
    pause_for_input()
    
    # Step 4: Check MQTT broker
    broker_running = check_mqtt_broker_port()
    pause_for_input()
    
    # Step 5: Show installation guide if needed
    if not broker_running:
        show_mqtt_installation_guide()
        pause_for_input()
    
    # Step 6: Simple test if everything looks good
    if mqtt_available and broker_running:
        simple_mqtt_test(mqtt_version)
        pause_for_input()
    else:
        print("\n=== Cannot perform MQTT test ===")
        if not mqtt_available:
            print("- Install paho-mqtt library first")
        if not broker_running:
            print("- Install and start MQTT broker first")
        pause_for_input()
    
    # Step 7: Show code fix instructions
    if mqtt_available:
        show_code_fix_instructions(mqtt_version)
        pause_for_input()
    
    print("\n=== Diagnostic Summary ===")
    print(f"MQTT Library: {'✓' if mqtt_available else '✗'}")
    if mqtt_available:
        print(f"MQTT Version: {mqtt_version}")
    print(f"MQTT Broker:  {'✓' if broker_running else '✗'}")
    
    if mqtt_available and broker_running:
        print("\n✓ Your system should be ready for MQTT!")
        if mqtt_version == "2.0+":
            print("⚠ Remember to update your main application code for v2.0+ compatibility")
    else:
        print("\n✗ Please fix the issues above before using MQTT features")
    
    pause_for_input("\nDiagnostic complete. Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted by user")
        pause_for_input("Press Enter to exit...")
    except Exception as e:
        print(f"\n\nUnexpected error occurred: {e}")
        print("Please share this error message for further help")
        import traceback
        traceback.print_exc()
        pause_for_input("Press Enter to exit...")