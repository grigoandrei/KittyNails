import React, { useState } from 'react';
import { apiClient } from '../api/client';
import type { WeeklyAvailabilityCreate, BlockedTimeCreate, ApiError } from '../types';
import ErrorMessage from '../components/ErrorMessage';

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const DEFAULT_START = '09:00';
const DEFAULT_END = '17:00';

/* ------------------------------------------------------------------ */
/*  Shared inline styles                                               */
/* ------------------------------------------------------------------ */

const inputStyle: React.CSSProperties = {
  padding: '8px 10px',
  borderRadius: 6,
  border: '1px solid #f0e0eb',
  fontSize: 14,
  boxSizing: 'border-box',
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  marginBottom: 4,
  color: '#666',
  fontSize: 13,
};

const formRowStyle: React.CSSProperties = {
  marginBottom: 12,
};

const primaryBtnStyle: React.CSSProperties = {
  padding: '10px 20px',
  borderRadius: 8,
  border: 'none',
  backgroundColor: '#e91e8c',
  color: '#fff',
  fontSize: 15,
  fontWeight: 'bold',
  cursor: 'pointer',
};

const cellStyle: React.CSSProperties = {
  padding: '10px 8px',
  borderBottom: '1px solid #f0e0eb',
  fontSize: 14,
  verticalAlign: 'middle',
};

const thStyle: React.CSSProperties = {
  padding: '10px 8px',
  textAlign: 'left',
  fontSize: 13,
  color: '#888',
  fontWeight: 600,
};

/* ------------------------------------------------------------------ */
/*  Day row state                                                      */
/* ------------------------------------------------------------------ */

interface DayRow {
  dayOfWeek: number;
  enabled: boolean;
  startTime: string;
  endTime: string;
}

function createInitialRows(): DayRow[] {
  return DAY_NAMES.map((_, i) => ({
    dayOfWeek: i,
    enabled: i < 5, // Mon-Fri enabled by default
    startTime: DEFAULT_START,
    endTime: DEFAULT_END,
  }));
}

/* ------------------------------------------------------------------ */
/*  Weekly Schedule Editor                                             */
/* ------------------------------------------------------------------ */

interface WeeklyEditorProps {
  onError: (msg: string | null) => void;
}

const WeeklyScheduleEditor: React.FC<WeeklyEditorProps> = ({ onError }) => {
  const [rows, setRows] = useState<DayRow[]>(createInitialRows);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  const updateRow = (index: number, patch: Partial<DayRow>) => {
    setRows(prev => prev.map((r, i) => (i === index ? { ...r, ...patch } : r)));
    setSuccess(false);
  };

  const handleSave = async () => {
    onError(null);
    setSuccess(false);

    const payload: WeeklyAvailabilityCreate[] = rows
      .filter(r => r.enabled)
      .map(r => ({
        day_of_week: r.dayOfWeek,
        start_time: r.startTime,
        end_time: r.endTime,
      }));

    setSaving(true);
    try {
      await apiClient.put('/availability/weekly', payload);
      setSuccess(true);
    } catch (err) {
      const apiErr = err as ApiError;
      onError(apiErr.detail ?? 'Failed to save weekly schedule');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ marginBottom: 40 }}>
      <h2 style={{ color: '#e91e8c', marginBottom: 12, fontSize: 18 }}>Weekly Schedule</h2>

      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 16 }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #f0e0eb' }}>
            <th style={thStyle}>Day</th>
            <th style={{ ...thStyle, textAlign: 'center' }}>Enabled</th>
            <th style={thStyle}>Start Time</th>
            <th style={thStyle}>End Time</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.dayOfWeek}>
              <td style={cellStyle}>{DAY_NAMES[row.dayOfWeek]}</td>
              <td style={{ ...cellStyle, textAlign: 'center' }}>
                <input
                  type="checkbox"
                  checked={row.enabled}
                  onChange={e => updateRow(i, { enabled: e.target.checked })}
                  aria-label={`Enable ${DAY_NAMES[row.dayOfWeek]}`}
                />
              </td>
              <td style={cellStyle}>
                <input
                  type="time"
                  value={row.startTime}
                  onChange={e => updateRow(i, { startTime: e.target.value })}
                  disabled={!row.enabled}
                  aria-label={`${DAY_NAMES[row.dayOfWeek]} start time`}
                  style={{ ...inputStyle, opacity: row.enabled ? 1 : 0.4 }}
                />
              </td>
              <td style={cellStyle}>
                <input
                  type="time"
                  value={row.endTime}
                  onChange={e => updateRow(i, { endTime: e.target.value })}
                  disabled={!row.enabled}
                  aria-label={`${DAY_NAMES[row.dayOfWeek]} end time`}
                  style={{ ...inputStyle, opacity: row.enabled ? 1 : 0.4 }}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {success && (
        <p style={{ color: '#27ae60', fontSize: 14, marginBottom: 8 }}>
          Weekly schedule saved successfully!
        </p>
      )}

      <button onClick={handleSave} disabled={saving} style={primaryBtnStyle}>
        {saving ? 'Saving…' : 'Save Schedule'}
      </button>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/*  Block Time Form                                                    */
/* ------------------------------------------------------------------ */

interface BlockFormProps {
  onError: (msg: string | null) => void;
}

const BlockTimeForm: React.FC<BlockFormProps> = ({ onError }) => {
  const [blockedDate, setBlockedDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    onError(null);
    setSuccess(false);

    const payload: BlockedTimeCreate = {
      blocked_date: blockedDate,
      start_time: startTime || null,
      end_time: endTime || null,
      reason: reason.trim() || null,
    };

    setSubmitting(true);
    try {
      await apiClient.post('/availability/block', payload);
      setSuccess(true);
      // Reset form
      setBlockedDate('');
      setStartTime('');
      setEndTime('');
      setReason('');
    } catch (err) {
      const apiErr = err as ApiError;
      onError(apiErr.detail ?? 'Failed to block time');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2 style={{ color: '#e91e8c', marginBottom: 12, fontSize: 18 }}>Block Time</h2>

      <div style={formRowStyle}>
        <label htmlFor="block-date" style={labelStyle}>Date *</label>
        <input
          id="block-date"
          type="date"
          value={blockedDate}
          onChange={e => { setBlockedDate(e.target.value); setSuccess(false); }}
          required
          style={inputStyle}
        />
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <div style={{ flex: 1 }}>
          <label htmlFor="block-start" style={labelStyle}>Start Time (optional)</label>
          <input
            id="block-start"
            type="time"
            value={startTime}
            onChange={e => { setStartTime(e.target.value); setSuccess(false); }}
            style={{ ...inputStyle, width: '100%' }}
          />
        </div>
        <div style={{ flex: 1 }}>
          <label htmlFor="block-end" style={labelStyle}>End Time (optional)</label>
          <input
            id="block-end"
            type="time"
            value={endTime}
            onChange={e => { setEndTime(e.target.value); setSuccess(false); }}
            style={{ ...inputStyle, width: '100%' }}
          />
        </div>
      </div>

      <div style={formRowStyle}>
        <label htmlFor="block-reason" style={labelStyle}>Reason (optional)</label>
        <input
          id="block-reason"
          value={reason}
          onChange={e => { setReason(e.target.value); setSuccess(false); }}
          placeholder="e.g. Personal appointment"
          style={{ ...inputStyle, width: '100%' }}
        />
      </div>

      {success && (
        <p style={{ color: '#27ae60', fontSize: 14, marginBottom: 8 }}>
          Time blocked successfully!
        </p>
      )}

      <button type="submit" disabled={submitting} style={primaryBtnStyle}>
        {submitting ? 'Blocking…' : 'Block Time'}
      </button>
    </form>
  );
};

/* ------------------------------------------------------------------ */
/*  Main page component                                                */
/* ------------------------------------------------------------------ */

const OwnerAvailability: React.FC = () => {
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [blockError, setBlockError] = useState<string | null>(null);

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 16 }}>
      <h1 style={{ color: '#e91e8c', marginBottom: 24 }}>Manage Availability</h1>

      {scheduleError && <ErrorMessage message={scheduleError} />}
      <WeeklyScheduleEditor onError={setScheduleError} />

      {blockError && <ErrorMessage message={blockError} />}
      <BlockTimeForm onError={setBlockError} />
    </div>
  );
};

export default OwnerAvailability;
