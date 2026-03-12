import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';
import type { AppointmentResponse, ApiError } from '../types';
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
/*  Appointment row with cancel                                        */
/* ------------------------------------------------------------------ */

interface AppointmentRowProps {
  appointment: AppointmentResponse;
  onCancelled: (id: number) => void;
}

const AppointmentRow: React.FC<AppointmentRowProps> = ({ appointment, onCancelled }) => {
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCancel = async () => {
    setError(null);
    setCancelling(true);
    try {
      await apiClient.delete(`/appointments/${appointment.id}`);
      onCancelled(appointment.id);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? 'Failed to cancel appointment');
    } finally {
      setCancelling(false);
    }
  };

  return (
    <>
      <tr>
        <td style={cellStyle}>{appointment.appointment_time} – {appointment.end_time}</td>
        <td style={cellStyle}>{appointment.client_name}</td>
        <td style={cellStyle}>{appointment.client_phone}</td>
        <td style={cellStyle}>{appointment.service.name}</td>
        <td style={{ ...cellStyle, textAlign: 'center' }}>
          <button
            onClick={handleCancel}
            disabled={cancelling}
            style={cancelBtnStyle}
            aria-label={`Cancel appointment for ${appointment.client_name}`}
          >
            {cancelling ? 'Cancelling…' : 'Cancel'}
          </button>
        </td>
      </tr>
      {error && (
        <tr>
          <td colSpan={5} style={{ padding: '0 8px 8px' }}>
            <ErrorMessage message={error} />
          </td>
        </tr>
      )}
    </>
  );
};

/* ------------------------------------------------------------------ */
/*  Main page component                                                */
/* ------------------------------------------------------------------ */

const OwnerAppointments: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState(getTodayISO());
  const [appointments, setAppointments] = useState<AppointmentResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAppointments = useCallback(async (date: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<AppointmentResponse[]>('/appointments/', { date });
      setAppointments(data);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? 'Failed to load appointments');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAppointments(selectedDate);
  }, [selectedDate, fetchAppointments]);

  const handleDateChange = (date: string) => {
    setSelectedDate(date);
  };

  const handleCancelled = (id: number) => {
    setAppointments(prev => prev.filter(a => a.id !== id));
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 16 }}>
      <h1 style={{ color: '#e91e8c', marginBottom: 24 }}>Appointments</h1>

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

      {!loading && !error && appointments.length === 0 && (
        <p style={{ color: '#888', textAlign: 'center', padding: 24 }}>
          No appointments on this day.
        </p>
      )}

      {!loading && appointments.length > 0 && (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #f0e0eb' }}>
              <th style={thStyle}>Time</th>
              <th style={thStyle}>Client</th>
              <th style={thStyle}>Phone</th>
              <th style={thStyle}>Service</th>
              <th style={{ ...thStyle, textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {appointments.map(appt => (
              <AppointmentRow
                key={appt.id}
                appointment={appt}
                onCancelled={handleCancelled}
              />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default OwnerAppointments;
