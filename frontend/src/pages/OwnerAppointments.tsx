import React, { useState, useCallback } from 'react';
import { apiClient } from '../api/client';
import type { DaySchedule, AppointmentResponse, ApiError } from '../types';
import ErrorMessage from '../components/ErrorMessage';
import LoadingSpinner from '../components/LoadingSpinner';
import DatePicker from '../components/DatePicker';
import { getTodayISO } from '../utils/date';

/* ------------------------------------------------------------------ */
/*  Shared inline styles                                               */
/* ------------------------------------------------------------------ */

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

const inputStyle: React.CSSProperties = {
  padding: '8px 10px',
  borderRadius: 6,
  border: '1px solid #f0e0eb',
  fontSize: 14,
  boxSizing: 'border-box',
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

const cancelBtnStyle: React.CSSProperties = {
  padding: '6px 14px',
  borderRadius: 6,
  border: '1px solid #c0392b',
  backgroundColor: '#fff',
  color: '#c0392b',
  fontSize: 13,
  cursor: 'pointer',
};

/* ------------------------------------------------------------------ */
/*  Appointment detail card with cancel                                */
/* ------------------------------------------------------------------ */

interface AppointmentCardProps {
  appointment: AppointmentResponse;
  onCancelled: (id: number) => void;
}

const AppointmentCard: React.FC<AppointmentCardProps> = ({ appointment, onCancelled }) => {
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cancelled, setCancelled] = useState(false);

  const handleCancel = async () => {
    setError(null);
    setCancelling(true);
    try {
      await apiClient.delete(`/appointments/${appointment.id}`);
      setCancelled(true);
      onCancelled(appointment.id);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? 'Failed to cancel appointment');
    } finally {
      setCancelling(false);
    }
  };

  if (cancelled) {
    return (
      <div
        role="status"
        style={{
          backgroundColor: '#f0fdf4',
          borderRadius: 12,
          padding: 16,
          marginBottom: 16,
          textAlign: 'center',
        }}
      >
        <p style={{ color: '#27ae60', fontWeight: 600 }}>
          Appointment #{appointment.id} has been cancelled.
        </p>
      </div>
    );
  }

  return (
    <div
      data-testid="appointment-details"
      style={{
        backgroundColor: '#fdf2f8',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p style={{ margin: '4px 0' }}><strong>Client:</strong> {appointment.client_name}</p>
          <p style={{ margin: '4px 0' }}><strong>Service:</strong> {appointment.service.name}</p>
          <p style={{ margin: '4px 0' }}>
            <strong>Time:</strong> {appointment.appointment_time} – {appointment.end_time}
          </p>
          <p style={{ margin: '4px 0' }}><strong>Date:</strong> {appointment.appointment_date}</p>
          <p style={{ margin: '4px 0' }}><strong>ID:</strong> {appointment.id}</p>
        </div>
        <button
          onClick={handleCancel}
          disabled={cancelling}
          style={cancelBtnStyle}
          aria-label={`Cancel appointment for ${appointment.client_name}`}
        >
          {cancelling ? 'Cancelling…' : 'Cancel'}
        </button>
      </div>
      {error && <ErrorMessage message={error} />}
    </div>
  );
};


/* ------------------------------------------------------------------ */
/*  Main page component                                                */
/* ------------------------------------------------------------------ */

const OwnerAppointments: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState(getTodayISO());
  const [schedule, setSchedule] = useState<DaySchedule | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Appointment lookup state
  const [appointmentId, setAppointmentId] = useState('');
  const [lookedUpAppointments, setLookedUpAppointments] = useState<AppointmentResponse[]>([]);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState<string | null>(null);

  const fetchSchedule = useCallback(async (date: string) => {
    setLoading(true);
    setError(null);
    setSchedule(null);

    try {
      const daySchedule = await apiClient.get<DaySchedule>('/availability/', { date });
      setSchedule(daySchedule);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? 'Failed to load schedule');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDateChange = (date: string) => {
    setSelectedDate(date);
    fetchSchedule(date);
  };

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedId = appointmentId.trim();
    if (!trimmedId) return;

    setLookupLoading(true);
    setLookupError(null);

    try {
      const appt = await apiClient.get<AppointmentResponse>(`/appointments/${trimmedId}`);
      // Avoid duplicates
      setLookedUpAppointments(prev => {
        if (prev.some(a => a.id === appt.id)) return prev;
        return [...prev, appt];
      });
      setAppointmentId('');
    } catch (err) {
      const apiErr = err as ApiError;
      if (apiErr.status === 404) {
        setLookupError('Appointment not found. Please check the ID.');
      } else {
        setLookupError(apiErr.detail ?? 'Failed to look up appointment');
      }
    } finally {
      setLookupLoading(false);
    }
  };

  const handleAppointmentCancelled = (id: number) => {
    setLookedUpAppointments(prev => prev.filter(a => a.id !== id));
    // Refresh schedule to reflect changes
    if (selectedDate) {
      fetchSchedule(selectedDate);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 16 }}>
      <h1 style={{ color: '#e91e8c', marginBottom: 24 }}>Appointments</h1>

      {/* Date picker for day schedule */}
      <div style={{ marginBottom: 24 }}>
        <label
          htmlFor="appointment-date"
          style={{ display: 'block', marginBottom: 4, color: '#666', fontSize: 13 }}
        >
          Select Date
        </label>
        <DatePicker value={selectedDate} onChange={handleDateChange} />
      </div>

      {loading && <LoadingSpinner />}
      {error && <ErrorMessage message={error} />}

      {!loading && schedule && !schedule.is_working_day && (
        <p style={{ color: '#888', textAlign: 'center', padding: 24 }}>
          This is not a working day. No appointments scheduled.
        </p>
      )}

      {!loading && schedule && schedule.is_working_day && (
        <>
          <h2 style={{ color: '#e91e8c', marginBottom: 12, fontSize: 18 }}>
            Day Schedule — {schedule.date}
          </h2>

          {schedule.slots.length === 0 ? (
            <p style={{ color: '#888', textAlign: 'center' }}>No slots configured for this day.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 24 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #f0e0eb' }}>
                  <th style={thStyle}>Start Time</th>
                  <th style={thStyle}>End Time</th>
                  <th style={thStyle}>Status</th>
                </tr>
              </thead>
              <tbody>
                {schedule.slots.map((slot, i) => (
                  <tr key={i}>
                    <td style={cellStyle}>{slot.start_time}</td>
                    <td style={cellStyle}>{slot.end_time}</td>
                    <td style={cellStyle}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '4px 10px',
                          borderRadius: 12,
                          fontSize: 12,
                          fontWeight: 600,
                          backgroundColor: slot.available ? '#e8f8f0' : '#fdedef',
                          color: slot.available ? '#27ae60' : '#c0392b',
                        }}
                      >
                        {slot.available ? 'Available' : 'Booked'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}

      {/* Appointment lookup and cancel section */}
      <div style={{ marginTop: 32, borderTop: '2px solid #f0e0eb', paddingTop: 24 }}>
        <h2 style={{ color: '#e91e8c', marginBottom: 12, fontSize: 18 }}>
          Look Up &amp; Cancel Appointment
        </h2>

        <form onSubmit={handleLookup} style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={appointmentId}
              onChange={e => { setAppointmentId(e.target.value); setLookupError(null); }}
              placeholder="Enter appointment ID"
              aria-label="Appointment ID"
              required
              style={{ ...inputStyle, flex: 1 }}
            />
            <button type="submit" disabled={lookupLoading} style={primaryBtnStyle}>
              {lookupLoading ? 'Looking up…' : 'Look Up'}
            </button>
          </div>
        </form>

        {lookupError && <ErrorMessage message={lookupError} />}

        {lookedUpAppointments.map(appt => (
          <AppointmentCard
            key={appt.id}
            appointment={appt}
            onCancelled={handleAppointmentCancelled}
          />
        ))}
      </div>
    </div>
  );
};

export default OwnerAppointments;
