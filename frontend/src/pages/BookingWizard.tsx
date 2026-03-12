import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { isValidName, isValidPhone } from '../utils/validation';
import { getTodayISO } from '../utils/date';
import ProgressIndicator from '../components/ProgressIndicator';
import ServiceCard from '../components/ServiceCard';
import DatePicker from '../components/DatePicker';
import SlotButton from '../components/SlotButton';
import ErrorMessage from '../components/ErrorMessage';
import LoadingSpinner from '../components/LoadingSpinner';
import type { NailService, AppointmentResponse, TimeSlot, ApiError } from '../types';

interface BookingState {
  step: 'service' | 'datetime' | 'contact' | 'confirmation';
  selectedService: NailService | null;
  selectedDate: string | null;
  selectedTime: string | null;
  clientName: string;
  clientPhone: string;
  clientEmail: string;
  confirmedAppointment: AppointmentResponse | null;
}

const STEPS = ['Service', 'Date & Time', 'Contact', 'Confirmation'];

function stepIndex(step: BookingState['step']): number {
  switch (step) {
    case 'service': return 0;
    case 'datetime': return 1;
    case 'contact': return 2;
    case 'confirmation': return 3;
  }
}

const BookingWizard: React.FC = () => {
  const [state, setState] = useState<BookingState>({
    step: 'service',
    selectedService: null,
    selectedDate: null,
    selectedTime: null,
    clientName: '',
    clientPhone: '',
    clientEmail: '',
    confirmedAppointment: null,
  });

  // Service step state
  const [services, setServices] = useState<NailService[]>([]);
  const [servicesLoading, setServicesLoading] = useState(false);
  const [servicesError, setServicesError] = useState<string | null>(null);

  // DateTime step state
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [slotsError, setSlotsError] = useState<string | null>(null);

  // Contact step state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [nameError, setNameError] = useState<string | null>(null);
  const [phoneError, setPhoneError] = useState<string | null>(null);

  // Fetch services on mount
  useEffect(() => {
    if (state.step === 'service') {
      setServicesLoading(true);
      setServicesError(null);
      apiClient.get<NailService[]>('/services/')
        .then(setServices)
        .catch((err: ApiError) => {
          setServicesError(err.detail || 'Could not load services');
        })
        .finally(() => setServicesLoading(false));
    }
  }, [state.step]);

  // Fetch slots when date changes
  useEffect(() => {
    if (state.step === 'datetime' && state.selectedDate && state.selectedService) {
      setSlotsLoading(true);
      setSlotsError(null);
      apiClient.get<TimeSlot[]>('/appointments/available', {
        date: state.selectedDate,
        service_id: String(state.selectedService.id),
      })
        .then(setSlots)
        .catch((err: ApiError) => {
          setSlotsError(err.detail || 'Could not load available slots');
        })
        .finally(() => setSlotsLoading(false));
    }
  }, [state.step, state.selectedDate, state.selectedService]);

  const handleServiceSelect = (service: NailService) => {
    setState(prev => ({ ...prev, step: 'datetime', selectedService: service, selectedDate: getTodayISO() }));
    setSlots([]);
    setSlotsError(null);
  };

  const handleDateChange = (date: string) => {
    setState(prev => ({ ...prev, selectedDate: date, selectedTime: null }));
    setSlots([]);
  };

  const handleSlotSelect = (slot: TimeSlot) => {
    setState(prev => ({ ...prev, step: 'contact', selectedTime: slot.start_time }));
    setSubmitError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setNameError(null);
    setPhoneError(null);
    setSubmitError(null);

    // Validate
    let hasError = false;
    if (!isValidName(state.clientName)) {
      setNameError('Name must be between 1 and 100 characters');
      hasError = true;
    }
    if (!isValidPhone(state.clientPhone)) {
      setPhoneError('Phone must be between 7 and 20 characters');
      hasError = true;
    }
    if (hasError) return;

    setSubmitting(true);
    try {
      const appointment = await apiClient.post<AppointmentResponse>('/appointments/', {
        client_name: state.clientName.trim(),
        client_phone: state.clientPhone.trim(),
        client_email: state.clientEmail.trim() || null,
        service_id: state.selectedService!.id,
        appointment_date: state.selectedDate!,
        appointment_time: state.selectedTime!,
      });
      setState(prev => ({ ...prev, step: 'confirmation', confirmedAppointment: appointment }));
    } catch (err) {
      const apiErr = err as ApiError;
      if (apiErr.status === 409) {
        setState(prev => ({ ...prev, step: 'datetime', selectedTime: null }));
        setSlotsError('That slot is no longer available. Please choose another time.');
      } else {
        setSubmitError(apiErr.detail || 'Something went wrong. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: 16 }}>
      <h1 style={{ textAlign: 'center', color: '#e91e8c', marginBottom: 8 }}>Book Your Appointment</h1>
      <ProgressIndicator currentStep={stepIndex(state.step)} steps={STEPS} />

      {/* Step 1: Service Selection */}
      {state.step === 'service' && (
        <div>
          <h2 style={{ color: '#333', marginBottom: 12 }}>Choose a Service</h2>
          {servicesLoading && <LoadingSpinner />}
          {servicesError && <ErrorMessage message={servicesError} />}
          {!servicesLoading && !servicesError && services.length === 0 && (
            <p>No services available at the moment.</p>
          )}
          {services.map(service => (
            <ServiceCard
              key={service.id}
              service={service}
              onSelect={() => handleServiceSelect(service)}
            />
          ))}
        </div>
      )}

      {/* Step 2: Date & Time Selection */}
      {state.step === 'datetime' && (
        <div>
          <h2 style={{ color: '#333', marginBottom: 12 }}>Pick a Date & Time</h2>
          {slotsError && <ErrorMessage message={slotsError} />}
          <div style={{ marginBottom: 16 }}>
            <label htmlFor="date-picker" style={{ display: 'block', marginBottom: 4, color: '#666' }}>
              Select a date:
            </label>
            <DatePicker
              value={state.selectedDate || ''}
              onChange={handleDateChange}
            />
          </div>
          {slotsLoading && <LoadingSpinner />}
          {!slotsLoading && state.selectedDate && slots.length === 0 && !slotsError && (
            <p>No availability for this date. Please try another date.</p>
          )}
          {!slotsLoading && slots.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {slots.map(slot => (
                <SlotButton
                  key={slot.start_time}
                  slot={slot}
                  onSelect={() => handleSlotSelect(slot)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Step 3: Contact Info */}
      {state.step === 'contact' && (
        <div>
          <h2 style={{ color: '#333', marginBottom: 12 }}>Your Details</h2>
          {submitError && <ErrorMessage message={submitError} />}
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 12 }}>
              <label htmlFor="client-name" style={{ display: 'block', marginBottom: 4, color: '#666' }}>
                Name *
              </label>
              <input
                id="client-name"
                type="text"
                value={state.clientName}
                onChange={e => setState(prev => ({ ...prev, clientName: e.target.value }))}
                required
                style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid #f0e0eb', fontSize: 14, boxSizing: 'border-box' }}
              />
              {nameError && <span style={{ color: '#c0392b', fontSize: 13 }}>{nameError}</span>}
            </div>
            <div style={{ marginBottom: 12 }}>
              <label htmlFor="client-phone" style={{ display: 'block', marginBottom: 4, color: '#666' }}>
                Phone *
              </label>
              <input
                id="client-phone"
                type="tel"
                value={state.clientPhone}
                onChange={e => setState(prev => ({ ...prev, clientPhone: e.target.value }))}
                required
                style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid #f0e0eb', fontSize: 14, boxSizing: 'border-box' }}
              />
              {phoneError && <span style={{ color: '#c0392b', fontSize: 13 }}>{phoneError}</span>}
            </div>
            <div style={{ marginBottom: 16 }}>
              <label htmlFor="client-email" style={{ display: 'block', marginBottom: 4, color: '#666' }}>
                Email (optional)
              </label>
              <input
                id="client-email"
                type="email"
                value={state.clientEmail}
                onChange={e => setState(prev => ({ ...prev, clientEmail: e.target.value }))}
                style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid #f0e0eb', fontSize: 14, boxSizing: 'border-box' }}
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: 8,
                border: 'none',
                backgroundColor: '#e91e8c',
                color: '#fff',
                fontSize: 16,
                fontWeight: 'bold',
                cursor: submitting ? 'not-allowed' : 'pointer',
                opacity: submitting ? 0.7 : 1,
              }}
            >
              {submitting ? 'Booking...' : 'Confirm Booking'}
            </button>
          </form>
        </div>
      )}

      {/* Step 4: Confirmation */}
      {state.step === 'confirmation' && state.confirmedAppointment && (
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ color: '#333', marginBottom: 12 }}>Booking Confirmed!</h2>
          <div
            data-testid="booking-confirmation"
            style={{
              backgroundColor: '#fdf2f8',
              borderRadius: 12,
              padding: 24,
              marginBottom: 16,
            }}
          >
            <p><strong>Appointment ID:</strong> {state.confirmedAppointment.id}</p>
            <p><strong>Service:</strong> {state.confirmedAppointment.service.name}</p>
            <p><strong>Date:</strong> {state.confirmedAppointment.appointment_date}</p>
            <p><strong>Time:</strong> {state.confirmedAppointment.appointment_time} – {state.confirmedAppointment.end_time}</p>
          </div>
        </div>
      )}

      {/* Owner login link */}
      <div style={{ textAlign: 'center', marginTop: 32 }}>
        <Link
          to="/owner/login"
          style={{ color: '#bbb', fontSize: 12, textDecoration: 'none' }}
        >
          Owner Login
        </Link>
      </div>
    </div>
  );
};

export default BookingWizard;
