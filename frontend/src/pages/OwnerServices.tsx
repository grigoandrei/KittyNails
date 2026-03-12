import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';
import type { NailService, NailServiceCreate, NailServiceUpdate, ApiError } from '../types';
import ErrorMessage from '../components/ErrorMessage';
import LoadingSpinner from '../components/LoadingSpinner';

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
  width: '100%',
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

const editBtnStyle: React.CSSProperties = {
  padding: '6px 14px',
  borderRadius: 6,
  border: '1px solid #e91e8c',
  backgroundColor: '#fff',
  color: '#e91e8c',
  fontSize: 13,
  cursor: 'pointer',
};

const saveBtnStyle: React.CSSProperties = {
  padding: '6px 14px',
  borderRadius: 6,
  border: 'none',
  backgroundColor: '#e91e8c',
  color: '#fff',
  fontSize: 13,
  cursor: 'pointer',
  marginRight: 6,
};

const cancelBtnStyle: React.CSSProperties = {
  padding: '6px 14px',
  borderRadius: 6,
  border: '1px solid #ccc',
  backgroundColor: '#fff',
  color: '#666',
  fontSize: 13,
  cursor: 'pointer',
};

/* ------------------------------------------------------------------ */
/*  Inline-edit row                                                    */
/* ------------------------------------------------------------------ */

interface ServiceRowProps {
  service: NailService;
  onUpdated: (updated: NailService) => void;
}

const ServiceRow: React.FC<ServiceRowProps> = ({ service, onUpdated }) => {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(service.name);
  const [description, setDescription] = useState(service.description ?? '');
  const [duration, setDuration] = useState(String(service.duration_minutes));
  const [price, setPrice] = useState(String(service.price));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetFields = useCallback(() => {
    setName(service.name);
    setDescription(service.description ?? '');
    setDuration(String(service.duration_minutes));
    setPrice(String(service.price));
    setError(null);
  }, [service]);

  const handleCancel = () => {
    resetFields();
    setEditing(false);
  };

  const handleSave = async () => {
    setError(null);

    // Build partial update with only changed fields
    const update: NailServiceUpdate = {};
    if (name !== service.name) update.name = name;
    const newDesc = description || null;
    if (newDesc !== service.description) update.description = newDesc;
    const newDuration = Number(duration);
    if (newDuration !== service.duration_minutes) update.duration_minutes = newDuration;
    const newPrice = Number(price);
    if (newPrice !== service.price) update.price = newPrice;

    if (Object.keys(update).length === 0) {
      setEditing(false);
      return;
    }

    setSaving(true);
    try {
      const updated = await apiClient.put<NailService>(`/services/${service.id}`, update);
      onUpdated(updated);
      setEditing(false);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? 'Failed to update service');
    } finally {
      setSaving(false);
    }
  };

  if (!editing) {
    return (
      <tr>
        <td style={cellStyle}>{service.name}</td>
        <td style={cellStyle}>{service.description ?? '—'}</td>
        <td style={{ ...cellStyle, textAlign: 'center' }}>{service.duration_minutes} min</td>
        <td style={{ ...cellStyle, textAlign: 'right' }}>€{service.price.toFixed(2)}</td>
        <td style={{ ...cellStyle, textAlign: 'center' }}>
          <button
            onClick={() => setEditing(true)}
            style={editBtnStyle}
            aria-label={`Edit ${service.name}`}
          >
            Edit
          </button>
        </td>
      </tr>
    );
  }

  return (
    <>
      <tr>
        <td style={cellStyle}>
          <input
            aria-label="Service name"
            value={name}
            onChange={e => setName(e.target.value)}
            style={inputStyle}
          />
        </td>
        <td style={cellStyle}>
          <input
            aria-label="Service description"
            value={description}
            onChange={e => setDescription(e.target.value)}
            style={inputStyle}
          />
        </td>
        <td style={cellStyle}>
          <input
            aria-label="Duration in minutes"
            type="number"
            min={1}
            max={210}
            value={duration}
            onChange={e => setDuration(e.target.value)}
            style={{ ...inputStyle, width: 70, textAlign: 'center' }}
          />
        </td>
        <td style={cellStyle}>
          <input
            aria-label="Price in euros"
            type="number"
            min={0.01}
            step={0.01}
            value={price}
            onChange={e => setPrice(e.target.value)}
            style={{ ...inputStyle, width: 80, textAlign: 'right' }}
          />
        </td>
        <td style={{ ...cellStyle, textAlign: 'center', whiteSpace: 'nowrap' }}>
          <button onClick={handleSave} disabled={saving} style={saveBtnStyle}>
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button onClick={handleCancel} disabled={saving} style={cancelBtnStyle}>
            Cancel
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
/*  Create-service form                                                */
/* ------------------------------------------------------------------ */

interface CreateFormProps {
  onCreated: (service: NailService) => void;
}

const CreateServiceForm: React.FC<CreateFormProps> = ({ onCreated }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [duration, setDuration] = useState('');
  const [price, setPrice] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const payload: NailServiceCreate = {
      name: name.trim(),
      description: description.trim() || undefined,
      duration_minutes: Number(duration),
      price: Number(price),
    };

    setSubmitting(true);
    try {
      const created = await apiClient.post<NailService>('/services/', payload);
      onCreated(created);
      // Reset form
      setName('');
      setDescription('');
      setDuration('');
      setPrice('');
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? 'Failed to create service');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: 32 }}>
      <h2 style={{ color: '#e91e8c', marginBottom: 12, fontSize: 18 }}>Add New Service</h2>

      <div style={formRowStyle}>
        <label htmlFor="new-name" style={labelStyle}>Name *</label>
        <input
          id="new-name"
          value={name}
          onChange={e => setName(e.target.value)}
          required
          maxLength={100}
          placeholder="e.g. Gel Manicure"
          style={inputStyle}
        />
      </div>

      <div style={formRowStyle}>
        <label htmlFor="new-desc" style={labelStyle}>Description</label>
        <input
          id="new-desc"
          value={description}
          onChange={e => setDescription(e.target.value)}
          maxLength={500}
          placeholder="Optional description"
          style={inputStyle}
        />
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <div style={{ flex: 1 }}>
          <label htmlFor="new-duration" style={labelStyle}>Duration (min) *</label>
          <input
            id="new-duration"
            type="number"
            min={1}
            max={210}
            value={duration}
            onChange={e => setDuration(e.target.value)}
            required
            placeholder="60"
            style={inputStyle}
          />
        </div>
        <div style={{ flex: 1 }}>
          <label htmlFor="new-price" style={labelStyle}>Price (€) *</label>
          <input
            id="new-price"
            type="number"
            min={0.01}
            step={0.01}
            value={price}
            onChange={e => setPrice(e.target.value)}
            required
            placeholder="35.00"
            style={inputStyle}
          />
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      <button type="submit" disabled={submitting} style={primaryBtnStyle}>
        {submitting ? 'Creating…' : 'Create Service'}
      </button>
    </form>
  );
};

/* ------------------------------------------------------------------ */
/*  Main page component                                                */
/* ------------------------------------------------------------------ */

const OwnerServices: React.FC = () => {
  const [services, setServices] = useState<NailService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchServices = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<NailService[]>('/services/');
      setServices(data);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? 'Failed to load services');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchServices();
  }, [fetchServices]);

  const handleCreated = (service: NailService) => {
    setServices(prev => [...prev, service]);
  };

  const handleUpdated = (updated: NailService) => {
    setServices(prev => prev.map(s => (s.id === updated.id ? updated : s)));
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 16 }}>
      <h1 style={{ color: '#e91e8c', marginBottom: 24 }}>Manage Services</h1>

      <CreateServiceForm onCreated={handleCreated} />

      {loading && <LoadingSpinner />}
      {error && <ErrorMessage message={error} />}

      {!loading && !error && services.length === 0 && (
        <p style={{ color: '#888', textAlign: 'center' }}>No services yet. Create one above!</p>
      )}

      {!loading && services.length > 0 && (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #f0e0eb' }}>
              <th style={thStyle}>Name</th>
              <th style={thStyle}>Description</th>
              <th style={{ ...thStyle, textAlign: 'center' }}>Duration</th>
              <th style={{ ...thStyle, textAlign: 'right' }}>Price</th>
              <th style={{ ...thStyle, textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {services.map(service => (
              <ServiceRow
                key={service.id}
                service={service}
                onUpdated={handleUpdated}
              />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default OwnerServices;