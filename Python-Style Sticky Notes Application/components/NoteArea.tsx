import React from 'react';

interface NoteAreaProps {
  content: string;
  onChange: (content: string) => void;
}

export function NoteArea({ content, onChange }: NoteAreaProps) {
  return (
    <div className="flex-1 flex flex-col" style={{ backgroundColor: '#121212' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-600">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-3 flex flex-col justify-between">
            <div className="w-full h-0.5 bg-gray-400"></div>
            <div className="w-full h-0.5 bg-gray-400"></div>
            <div className="w-full h-0.5 bg-gray-400"></div>
          </div>
          <span className="text-white font-medium">NOTE</span>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 p-4">
        <textarea
          value={content}
          onChange={(e) => onChange(e.target.value)}
          className="w-full h-full bg-transparent text-yellow-300 resize-none outline-none font-mono text-sm leading-relaxed"
          style={{ 
            backgroundColor: 'transparent',
            color: '#FDE047',
            fontFamily: 'Consolas, Monaco, "Courier New", monospace'
          }}
          placeholder="Enter your notes here..."
        />
      </div>

      {/* Resize Handle */}
      <div className="w-2 absolute right-0 top-0 h-full cursor-ew-resize bg-gray-700 hover:bg-gray-600 transition-colors">
        <div className="w-full h-full flex items-center justify-center">
          <div className="w-0.5 h-8 bg-gray-500"></div>
        </div>
      </div>
    </div>
  );
}