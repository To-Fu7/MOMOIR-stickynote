#!/usr/bin/env python3
"""
MQTT Test Script for Memoir Application Monitoring
This script simulates monitoring devices sending status updates and errors
to test the dot status indicators and notification functionality.
"""

import paho.mqtt.client as mqtt
import json
import time
import sys
import threading
from datetime import datetime
import random

class MQTTTester:
    def __init__(self, broker_host="10.11.0.34", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
        # Test monitoring nodes
        self.test_nodes = [
            {"name": "sensor1", "topic": "sensor1"},
            {"name": "camera1", "topic": "camera1"},
            {"name": "server1", "topic": "server1"},
            {"name": "database", "topic": "database"}
        ]
        
        self.running = False
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            print("📡 Ready to send test messages")
        else:
            print(f"❌ Failed to connect to MQTT broker: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        print(f"🔌 Disconnected from MQTT broker")
    
    def on_publish(self, client, userdata, mid):
        pass  # Uncomment for verbose logging: print(f"Message {mid} published")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print(f"🔄 Connecting to MQTT broker {self.broker_host}:{self.broker_port}...")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            time.sleep(1)  # Give connection time to establish
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
    
    def send_status_message(self, node_topic, status, additional_data=None):
        """Send a status message for a monitoring node"""
        topic = f"/monitoring/{node_topic}"
        
        message = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "node": node_topic
        }
        
        if additional_data:
            message.update(additional_data)
        
        payload = json.dumps(message, indent=2)
        result = self.client.publish(topic, payload)
        
        status_emoji = "🟢" if status == "normal" else "🔴" if status == "error" else "🟡"
        print(f"{status_emoji} Sent {status} status for {node_topic}")
        return result.rc == 0
    
    def send_error_message(self, node_topic, error_type, error_details=None):
        """Send an error message for a monitoring node"""
        topic = f"/monitoring/{node_topic}/error"
        
        message = {
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error_type": error_type,
            "node": node_topic
        }
        
        if error_details:
            message["details"] = error_details
        
        payload = json.dumps(message, indent=2)
        result = self.client.publish(topic, payload)
        
        print(f"🚨 Sent ERROR ({error_type}) for {node_topic}")
        return result.rc == 0
    
    def test_normal_status(self):
        """Test normal status updates for all nodes"""
        print("\n📊 Testing Normal Status Updates...")
        for node in self.test_nodes:
            self.send_status_message(
                node["topic"], 
                "normal",
                {
                    "cpu_usage": random.randint(10, 40),
                    "memory_usage": random.randint(20, 60),
                    "uptime": random.randint(3600, 86400)
                }
            )
            time.sleep(0.5)
    
    def test_error_conditions(self):
        """Test error conditions for random nodes"""
        print("\n⚠️  Testing Error Conditions...")
        
        error_scenarios = [
            {"type": "high_cpu", "details": "CPU usage above 95%"},
            {"type": "memory_leak", "details": "Memory usage above 90%"},
            {"type": "connection_lost", "details": "Lost connection to mqtt"},
            {"type": "disk_full", "details": "Disk usage above 95%"},
            {"type": "temperature_high", "details": "Temperature above safe threshold"},
            {"type": "authentication_failed", "details": "Failed login attempts detected"}
        ]
        
        # Send errors for random nodes
        selected_nodes = random.sample(self.test_nodes, random.randint(1, 3))
        
        for node in selected_nodes:
            error = random.choice(error_scenarios)
            self.send_error_message(
                node["topic"],
                error["type"],
                error["details"]
            )
            time.sleep(1)
    
    def test_mixed_status(self):
        """Test mixed status updates (some normal, some errors)"""
        print("\n🔄 Testing Mixed Status Updates...")
        
        for node in self.test_nodes:
            # Randomly choose status
            if random.random() < 0.3:  # 30% chance of error
                error_types = ["high_cpu", "memory_leak", "timeout", "connection_error"]
                error_type = random.choice(error_types)
                self.send_error_message(node["topic"], error_type)
            else:
                self.send_status_message(
                    node["topic"], 
                    "normal",
                    {"last_check": datetime.now().isoformat()}
                )
            time.sleep(0.8)
    
    def continuous_monitoring_simulation(self, duration_seconds=60):
        """Simulate continuous monitoring with periodic updates"""
        print(f"\n🔄 Starting continuous monitoring simulation for {duration_seconds} seconds...")
        print("Press Ctrl+C to stop early")
        
        self.running = True
        start_time = time.time()
        
        try:
            while self.running and (time.time() - start_time) < duration_seconds:
                # Send periodic normal status updates
                for node in self.test_nodes:
                    if not self.running:
                        break
                        
                    # 10% chance of error per update
                    if random.random() < 0.1:
                        error_types = ["timeout", "high_load", "connection_issue"]
                        self.send_error_message(node["topic"], random.choice(error_types))
                    else:
                        self.send_status_message(node["topic"], "normal")
                    
                    time.sleep(2)  # 2 seconds between node updates
                
                if self.running:
                    print(f"⏱️  {int(time.time() - start_time)}s elapsed...")
                    time.sleep(5)  # 5 seconds between full cycles
                    
        except KeyboardInterrupt:
            print("\n⏹️  Stopping simulation...")
            self.running = False
    
    def interactive_mode(self):
        """Interactive mode for manual testing"""
        print("\n🎮 Interactive Mode - Choose your test:")
        print("1. Send normal status for all nodes")
        print("2. Send error for specific node")
        print("3. Send mixed status updates")
        print("4. Start continuous simulation")
        print("5. Clear all statuses (send normal)")
        print("0. Exit")
        
        while True:
            try:
                choice = input("\nEnter your choice (0-5): ").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    self.test_normal_status()
                elif choice == "2":
                    self.manual_error_test()
                elif choice == "3":
                    self.test_mixed_status()
                elif choice == "4":
                    duration = input("Enter duration in seconds (default 60): ").strip()
                    duration = int(duration) if duration.isdigit() else 60
                    self.continuous_monitoring_simulation(duration)
                elif choice == "5":
                    self.clear_all_errors()
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n⏹️  Exiting interactive mode...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def manual_error_test(self):
        """Manual error testing for specific nodes"""
        print("\n📋 Available nodes:")
        for i, node in enumerate(self.test_nodes, 1):
            print(f"  {i}. {node['name']} ({node['topic']})")
        
        try:
            choice = input("Select node number: ").strip()
            node_idx = int(choice) - 1
            
            if 0 <= node_idx < len(self.test_nodes):
                node = self.test_nodes[node_idx]
                error_type = input("Enter error type (e.g., high_cpu, timeout): ").strip()
                error_details = input("Enter error details (optional): ").strip()
                
                self.send_error_message(
                    node["topic"], 
                    error_type if error_type else "generic_error",
                    error_details if error_details else None
                )
            else:
                print("❌ Invalid node selection")
        except (ValueError, IndexError):
            print("❌ Invalid input")
    
    def clear_all_errors(self):
        """Send normal status to clear all error states"""
        print("\n🧹 Clearing all error states...")
        for node in self.test_nodes:
            self.send_status_message(node["topic"], "normal")
            time.sleep(0.3)
        print("✅ All nodes set to normal status")

def main():
    print("🔧 MQTT Test Script for Memoir Application")
    print("=" * 50)
    
    # Configuration
    broker_host = input("Enter MQTT broker host (default: 10.11.0.34): ").strip()
    if not broker_host:
        broker_host = "10.11.0.34"
    
    broker_port_input = input("Enter MQTT broker port (default: 1883): ").strip()
    broker_port = int(broker_port_input) if broker_port_input.isdigit() else 1883
    
    # Create tester instance
    tester = MQTTTester(broker_host, broker_port)
    
    # Connect to broker
    if not tester.connect():
        print("❌ Failed to connect. Exiting.")
        return
    
    try:
        # Run tests
        print("\n🚀 Starting automated tests...")
        
        # Test 1: Normal status for all nodes
        tester.test_normal_status()
        time.sleep(3)
        
        # Test 2: Error conditions
        tester.test_error_conditions()
        time.sleep(3)
        
        # Test 3: Mixed status
        tester.test_mixed_status()
        time.sleep(2)
        
        print("\n✅ Automated tests completed!")
        
        # Ask if user wants interactive mode
        choice = input("\nEnter interactive mode? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            tester.interactive_mode()
    
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        print("\n🔌 Disconnecting from broker...")
        tester.disconnect()
        print("👋 Test script finished")

if __name__ == "__main__":
    main()