import React, { useState } from 'react';
import { apiClient } from '../api/client';
import ErrorMessage from '../components/ErrorMessage';
import LoadingSpinner from '../components/LoadingSpinner';
import type { AppointmentResponse, ApiError } from '../types';

const AppointmentLookup: React.FC = () => {
  const [appointmentId, setAppointmentId] = useState('');
  const [appointment, setAppointment] = useState<AppointmentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [cancelled, setCancelled] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedId = appointmentId.trim();
    if (!trimmedId) return;

    setLoading(true);
    setError(null);
    setNotFound(false);
    setAppointment(null);
    setCancelled(false);

    try {
      const result = await apiClient.get<AppointmentResponse>(`/appointments/${trimmedId}`);
      setAppointment(result);
    } catch (err) {
      const apiErr = err as ApiError;
      if (apiErr.status === 404) {
        setNotFound(true);
      } else {
        setError(apiErr.detail || 'Something went wrong. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!appointment) return;

    setCancelling(true);
    setError(null);

    try {
      await apiClient.delete(`/appointments/${appointment.id}`);
      setCancelled(true);
      setAppointment(null);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail || 'Could not cancel appointment. Please try again.');
    } finally {
      setCancelling(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: 16 }}>
      <h1 style={{ textAlign: 'center', color: '#e91e8c', marginBottom: 8 }}>
        Look Up Your Appointment
      </h1>

      <form onSubmit={handleLookup} style={{ marginBottom: 24 }}>
        <label htmlFor="appointment-id" style={{ display: 'block', marginBottom: 4, color: '#666' }}>
          Appointment ID
        </label>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            id="appointment-id"
            type="text"
            value={appointmentId}
            onChange={e => setAppointmentId(e.target.value)}
            placeholder="Enter your appointment ID"
            required
            style={{
              flex: 1,
              padding: '8px 12px',
              borderRadius: 8,
              border: '1px solid #f0e0eb',
              fontSize: 14,
            }}
          />
          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '8px 20px',
              borderRadius: 8,
              border: 'none',
              backgroundColor: '#e91e8c',
              color: '#fff',
              fontSize: 14,
              fontWeight: 'bold',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'Searching...' : 'Look Up'}
          </button>
        </div>
      </form>

      {loading && <LoadingSpinner />}

      {error && <ErrorMessage message={error} />}

      {notFound && (
        <div
          role="alert"
          style={{
            textAlign: 'center',
            padding: 24,
            backgroundColor: '#fdf2f8',
            borderRadius: 12,
          }}
        >
          <p style={{ color: '#666', fontSize: 16 }}>
            Appointment not found. Please check the ID and try again.
          </p>
        </div>
      )}

      {cancelled && (
        <div
          role="status"
          style={{
            textAlign: 'center',
            padding: 24,
            backgroundColor: '#f0fdf4',
            borderRadius: 12,
          }}
        >
          <h2 style={{ color: '#16a34a', marginBottom: 8 }}>Appointment Cancelled</h2>
          <p style={{ color: '#666' }}>Your appointment has been successfully cancelled.</p>
        </div>
      )}

      {appointment && (
        <div
          data-testid="appointment-details"
          style={{
            backgroundColor: '#fdf2f8',
            borderRadius: 12,
            padding: 24,
          }}
        >
          <h2 style={{ color: '#333', marginBottom: 12 }}>Appointment Details</h2>
          <p><strong>ID:</strong> {appointment.id}</p>
          <p><strong>Service:</strong> {appointment.service.name}</p>
          <p><strong>Date:</strong> {appointment.appointment_date}</p>
          <p><strong>Time:</strong> {appointment.appointment_time} – {appointment.end_time}</p>
          <p><strong>Client:</strong> {appointment.client_name}</p>
          <p><strong>Status:</strong> {appointment.status}</p>

          <button
            onClick={handleCancel}
            disabled={cancelling}
            style={{
              marginTop: 16,
              width: '100%',
              padding: '12px',
              borderRadius: 8,
              border: '2px solid #c0392b',
              backgroundColor: '#fff',
              color: '#c0392b',
              fontSize: 16,
              fontWeight: 'bold',
              cursor: cancelling ? 'not-allowed' : 'pointer',
              opacity: cancelling ? 0.7 : 1,
            }}
          >
            {cancelling ? 'Cancelling...' : 'Cancel Appointment'}
          </button>
        </div>
      )}
    </div>
  );
};

export default AppointmentLookup;
