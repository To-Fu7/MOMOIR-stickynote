#!/usr/bin/env python3
"""
Test script to verify MQTT functionality for the monitoring system.
This script publishes test messages to simulate monitoring data.
"""

import paho.mqtt.client as mqtt
import json
import time
import sys

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
    else:
        print(f"Failed to connect to MQTT broker: {rc}")

def on_publish(client, userdata, mid):
    print(f"Message published with mid: {mid}")

def main():
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        # Connect to MQTT broker
        client.connect("localhost", 1883, 60)
        client.loop_start()
        
        print("MQTT Test Client Started")
        print("Publishing test messages...")
        print("Press Ctrl+C to stop")
        
        # Test data
        test_topics = ["sensor1", "sensor2", "camera1"]
        
        for i in range(10):
            for topic in test_topics:
                # Normal status message
                normal_data = {
                    "status": "normal",
                    "timestamp": time.time(),
                    "value": 25.5 + i
                }
                
                topic_path = f"/monitoring/{topic}"
                client.publish(topic_path, json.dumps(normal_data))
                print(f"Published normal data to {topic_path}")
                
                # Simulate error every 3rd message
                if i % 3 == 0:
                    error_data = {
                        "status": "error",
                        "error_type": "temperature_high",
                        "timestamp": time.time()
                    }
                    
                    error_topic = f"/monitoring/{topic}/error"
                    client.publish(error_topic, json.dumps(error_data))
                    print(f"Published error data to {error_topic}")
            
            time.sleep(2)
        
        client.loop_stop()
        client.disconnect()
        print("Test completed")
        
    except KeyboardInterrupt:
        print("\nStopping test...")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()