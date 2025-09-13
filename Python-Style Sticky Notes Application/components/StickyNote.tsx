import React, { useState } from 'react';
import { NoteArea } from './NoteArea';
import { ReminderArea } from './ReminderArea';

export interface Reminder {
  id: string;
  text: string;
  date: string;
}

export function StickyNote() {
  const [noteContent, setNoteContent] = useState('* ITEMS\n- item_name ( Combat Knife )\n- item_type ( Eq )\n- item_category ( Katana )\n- item_pic ( jpg )\n- item_price ( 0 )\n- item_points ( 0 )\n- item_stat_craft ( 1 )\n- item_stat_drop ( 1 )\n- item_location ( 1 )\n- item_craft_player ( 1 )\n- item_craft_npc ( 1 )\n- item_consume_stat ( )\n\n*Monsters\n- monster_name\n- monster_type\n- monster_element\n- monster_attribute\n- monster_loc\n- monster_drops\n\n{\n\'easy\' : [');
  
  const [reminders, setReminders] = useState<Reminder[]>([
    {
      id: '1',
      text: 'Djr',
      date: '2025-08-20'
    }
  ]);

  const addReminder = (text: string, date: string) => {
    const newReminder: Reminder = {
      id: Date.now().toString(),
      text,
      date
    };
    setReminders([...reminders, newReminder]);
  };

  const removeReminder = (id: string) => {
    setReminders(reminders.filter(reminder => reminder.id !== id));
  };

  const [isMinimized, setIsMinimized] = useState(false);

  const handleNotification = (message: string) => {
    // Show notification to user (you can implement a toast notification system here)
    alert(message);
  };

  return (
    <div className="flex w-[800px] h-[500px] shadow-lg rounded-lg overflow-hidden bg-white">
      <NoteArea 
        content={noteContent}
        onChange={setNoteContent}
      />
      <ReminderArea 
        reminders={reminders}
        onAddReminder={addReminder}
        onRemoveReminder={removeReminder}
        isMinimized={isMinimized}
        onMinimize={() => setIsMinimized(!isMinimized)}
        onNotification={handleNotification}
      />
    </div>
  );
}