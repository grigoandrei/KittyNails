import React from 'react';
import { TimeSlot } from '../types';

interface SlotButtonProps {
  slot: TimeSlot;
  onSelect: () => void;
}

const SlotButton: React.FC<SlotButtonProps> = ({ slot, onSelect }) => {
  return (
    <button
      className="slot-button"
      data-testid={`slot-${slot.start_time}`}
      onClick={onSelect}
      disabled={!slot.available}
      style={{
        padding: '8px 16px',
        borderRadius: 8,
        border: '1px solid #f0e0eb',
        backgroundColor: slot.available ? '#fff' : '#f5f5f5',
        color: slot.available ? '#e91e8c' : '#ccc',
        cursor: slot.available ? 'pointer' : 'not-allowed',
        fontSize: 14,
        fontWeight: 'bold',
      }}
    >
      {slot.start_time}
    </button>
  );
};

export default SlotButton;
