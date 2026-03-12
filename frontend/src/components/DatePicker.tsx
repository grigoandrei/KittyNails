import React from 'react';
import { getTodayISO } from '../utils/date';

interface DatePickerProps {
  value: string;
  onChange: (date: string) => void;
  minDate?: string;
}

const DatePicker: React.FC<DatePickerProps> = ({ value, onChange, minDate }) => {
  const min = minDate ?? getTodayISO();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.value;
    if (selected >= min) {
      onChange(selected);
    }
  };

  return (
    <input
      type="date"
      className="date-picker"
      value={value}
      min={min}
      onChange={handleChange}
      style={{
        padding: '8px 12px',
        borderRadius: 8,
        border: '1px solid #f0e0eb',
        fontSize: 14,
        color: '#333',
      }}
    />
  );
};

export default DatePicker;
