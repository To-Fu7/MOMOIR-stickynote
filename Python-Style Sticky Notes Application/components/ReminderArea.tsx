import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { X, Minus, Plus } from 'lucide-react';
import type { Reminder } from './StickyNote';

interface ReminderAreaProps {
  reminders: Reminder[];
  onAddReminder: (text: string, date: string) => void;
  onRemoveReminder: (id: string) => void;
  isMinimized: boolean;
  onMinimize: () => void;
}

export function ReminderArea({ 
  reminders, 
  onAddReminder, 
  onRemoveReminder, 
  isMinimized, 
  onMinimize 
}: ReminderAreaProps) {
  const [newReminderText, setNewReminderText] = useState('');
  const [newReminderDate, setNewReminderDate] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  const handleAddReminder = () => {
    if (newReminderText.trim() && newReminderDate) {
      onAddReminder(newReminderText.trim(), newReminderDate);
      setNewReminderText('');
      setNewReminderDate('');
      setShowAddForm(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return `(${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')})`;
  };

  return (
    <div 
      className="w-80 flex flex-col"
      style={{ backgroundColor: '#2a1f3d' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2" style={{ borderBottom: '1px solid #4a3a5c' }}>
        <span className="text-gray-100 font-medium">REMINDER</span>
        <div className="flex items-center space-x-1">
          <button
            onClick={onMinimize}
            className="w-6 h-6 flex items-center justify-center text-gray-300 hover:text-white hover:bg-gray-600 hover:bg-opacity-30 rounded transition-colors"
          >
            <Minus size={14} />
          </button>
          <button className="w-6 h-6 flex items-center justify-center text-gray-300 hover:text-white hover:bg-gray-600 hover:bg-opacity-30 rounded transition-colors">
            <X size={14} />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Reminders List */}
          <div className="flex-1 p-4 space-y-2">
            {reminders.map((reminder) => (
              <div
                key={reminder.id}
                className="flex items-center justify-between px-3 py-2 rounded transition-colors hover:bg-gray-600 hover:bg-opacity-20"
                style={{ backgroundColor: '#3d324a' }}
              >
                <div>
                  <span className="text-yellow-200">• {reminder.text}</span>
                  <span className="text-gray-400 ml-2">{formatDate(reminder.date)}</span>
                </div>
                <button
                  onClick={() => onRemoveReminder(reminder.id)}
                  className="text-red-400 hover:text-red-300 ml-2 transition-colors"
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>

          {/* Add Reminder Form */}
          {showAddForm && (
            <div className="p-4 space-y-2" style={{ borderTop: '1px solid #4a3a5c' }}>
              <Input
                placeholder="Reminder text"
                value={newReminderText}
                onChange={(e) => setNewReminderText(e.target.value)}
                className="border-gray-500 text-gray-100 placeholder-gray-400 focus:border-purple-400 transition-colors"
                style={{ 
                  backgroundColor: '#3d324a',
                  borderColor: '#5a4d66'
                }}
              />
              <Input
                type="date"
                value={newReminderDate}
                onChange={(e) => setNewReminderDate(e.target.value)}
                className="border-gray-500 text-gray-100 focus:border-purple-400 transition-colors"
                style={{ 
                  backgroundColor: '#3d324a',
                  borderColor: '#5a4d66'
                }}
              />
              <div className="flex space-x-2">
                <Button
                  onClick={handleAddReminder}
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

          {/* Add Reminder Button */}
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
                <span>Add Reminder</span>
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}