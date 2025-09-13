import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Plus, X, Circle } from 'lucide-react';

export interface MonitoringNode {
  id: string;
  name: string;
  topic: string;
  status: 'connecting' | 'normal' | 'error';
  lastError?: string;
}

interface MonitoringAreaProps {
  onNotification: (message: string) => void;
}

export function MonitoringArea({ onNotification }: MonitoringAreaProps) {
  const [monitoringNodes, setMonitoringNodes] = useState<MonitoringNode[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newNodeName, setNewNodeName] = useState('');
  const [newNodeTopic, setNewNodeTopic] = useState('');
  const [mqttClient, setMqttClient] = useState<any>(null);

  // Initialize MQTT client
  useEffect(() => {
    const initializeMqtt = async () => {
      try {
        // Dynamic import for MQTT client
        const mqtt = await import('mqtt');
        const client = mqtt.connect('mqtt://localhost:1883');
        
        client.on('connect', () => {
          console.log('MQTT Connected');
          setMqttClient(client);
        });

        client.on('error', (error) => {
          console.error('MQTT Error:', error);
        });

        return client;
      } catch (error) {
        console.error('Failed to initialize MQTT:', error);
      }
    };

    initializeMqtt();

    return () => {
      if (mqttClient) {
        mqttClient.end();
      }
    };
  }, []);

  // Subscribe to monitoring topics when nodes are added
  useEffect(() => {
    if (mqttClient && monitoringNodes.length > 0) {
      monitoringNodes.forEach(node => {
        const topic = `/monitoring/${node.topic}`;
        const errorTopic = `/monitoring/${node.topic}/error`;
        
        mqttClient.subscribe(topic, (err: any) => {
          if (!err) {
            console.log(`Subscribed to ${topic}`);
            updateNodeStatus(node.id, 'normal');
          }
        });

        mqttClient.subscribe(errorTopic, (err: any) => {
          if (!err) {
            console.log(`Subscribed to ${errorTopic}`);
          }
        });

        mqttClient.on('message', (receivedTopic: string, message: Buffer) => {
          const messageStr = message.toString();
          
          if (receivedTopic === errorTopic) {
            try {
              const errorData = JSON.parse(messageStr);
              if (errorData.status === 'error') {
                updateNodeStatus(node.id, 'error', errorData.error_type);
                onNotification(`Detected Anomalies on ${node.name} error detail: ${errorData.error_type}`);
              }
            } catch (e) {
              console.error('Error parsing error message:', e);
            }
          } else if (receivedTopic === topic) {
            try {
              const data = JSON.parse(messageStr);
              if (data.status === 'error') {
                updateNodeStatus(node.id, 'error', data.error_type);
                onNotification(`Detected Anomalies on ${node.name} error detail: ${data.error_type}`);
              } else {
                updateNodeStatus(node.id, 'normal');
              }
            } catch (e) {
              // If not JSON, assume normal status
              updateNodeStatus(node.id, 'normal');
            }
          }
        });
      });
    }
  }, [mqttClient, monitoringNodes]);

  const updateNodeStatus = (nodeId: string, status: 'connecting' | 'normal' | 'error', errorType?: string) => {
    setMonitoringNodes(prev => prev.map(node => 
      node.id === nodeId 
        ? { ...node, status, lastError: errorType }
        : node
    ));
  };

  const handleAddNode = () => {
    if (newNodeName.trim() && newNodeTopic.trim()) {
      const newNode: MonitoringNode = {
        id: Date.now().toString(),
        name: newNodeName.trim(),
        topic: newNodeTopic.trim(),
        status: 'connecting'
      };
      
      setMonitoringNodes([...monitoringNodes, newNode]);
      setNewNodeName('');
      setNewNodeTopic('');
      setShowAddForm(false);
    }
  };

  const removeNode = (id: string) => {
    setMonitoringNodes(monitoringNodes.filter(node => node.id !== id));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'error': return 'text-red-500';
      case 'normal': return 'text-blue-500';
      case 'connecting': return 'text-gray-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'error': return 'Error';
      case 'normal': return 'Normal';
      case 'connecting': return 'Connecting';
      default: return 'Unknown';
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      {/* Monitoring Nodes List */}
      <div className="flex-1 p-4 space-y-2">
        {monitoringNodes.map((node) => (
          <div
            key={node.id}
            className="flex items-center justify-between px-3 py-2 rounded transition-colors hover:bg-gray-600 hover:bg-opacity-20"
            style={{ backgroundColor: '#3d324a' }}
          >
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <Circle 
                  size={8} 
                  className={`fill-current ${getStatusColor(node.status)}`}
                />
                <span className="text-yellow-200">{node.name}</span>
              </div>
              <span className="text-gray-400 text-sm">({node.topic})</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`text-xs ${getStatusColor(node.status)}`}>
                {getStatusText(node.status)}
              </span>
              <button
                onClick={() => removeNode(node.id)}
                className="text-red-400 hover:text-red-300 ml-2 transition-colors"
              >
                <X size={12} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add Monitoring Form */}
      {showAddForm && (
        <div className="p-4 space-y-2" style={{ borderTop: '1px solid #4a3a5c' }}>
          <Input
            placeholder="Monitoring name"
            value={newNodeName}
            onChange={(e) => setNewNodeName(e.target.value)}
            className="border-gray-500 text-gray-100 placeholder-gray-400 focus:border-purple-400 transition-colors"
            style={{ 
              backgroundColor: '#3d324a',
              borderColor: '#5a4d66'
            }}
          />
          <Input
            placeholder="Topic (e.g., sensor1, device2)"
            value={newNodeTopic}
            onChange={(e) => setNewNodeTopic(e.target.value)}
            className="border-gray-500 text-gray-100 placeholder-gray-400 focus:border-purple-400 transition-colors"
            style={{ 
              backgroundColor: '#3d324a',
              borderColor: '#5a4d66'
            }}
          />
          <div className="flex space-x-2">
            <Button
              onClick={handleAddNode}
              className="flex-1 text-white transition-colors"
              style={{ 
                backgroundColor: '#6b46c1',
                '&:hover': { backgroundColor: '#7c3aed' }
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#7c3aed'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#6b46c1'}
            >
              Add
            </Button>
            <Button
              onClick={() => setShowAddForm(false)}
              variant="outline"
              className="flex-1 text-gray-300 hover:text-white hover:bg-gray-600 hover:bg-opacity-30 transition-colors"
              style={{ 
                borderColor: '#5a4d66',
                backgroundColor: 'transparent'
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Add Monitoring Button */}
      {!showAddForm && (
        <div className="p-4" style={{ borderTop: '1px solid #4a3a5c' }}>
          <Button
            onClick={() => setShowAddForm(true)}
            className="w-full text-white flex items-center justify-center space-x-2 transition-colors"
            style={{ 
              backgroundColor: '#6b46c1'
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#7c3aed'}
            onMouseLeave={(e) => e.target.style.backgroundColor = '#6b46c1'}
          >
            <Plus size={16} />
            <span>Add Monitoring</span>
          </Button>
        </div>
      )}
    </div>
  );
}