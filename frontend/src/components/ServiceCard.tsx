import React from 'react';
import { NailService } from '../types';

interface ServiceCardProps {
  service: NailService;
  onSelect?: () => void;
}

const ServiceCard: React.FC<ServiceCardProps> = ({ service, onSelect }) => {
  return (
    <div
      className="service-card"
      data-testid={`service-card-${service.id}`}
      onClick={onSelect}
      style={{
        border: '1px solid #f0e0eb',
        borderRadius: 12,
        padding: 16,
        cursor: onSelect ? 'pointer' : 'default',
        backgroundColor: '#fff',
        marginBottom: 12,
      }}
    >
      <h3 style={{ margin: '0 0 4px', color: '#333' }}>{service.name}</h3>
      {service.description && (
        <p style={{ margin: '0 0 8px', color: '#666', fontSize: 14 }}>{service.description}</p>
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, color: '#888' }}>
        <span>{service.duration_minutes} min</span>
        <span style={{ fontWeight: 'bold', color: '#e91e8c' }}>€{Number(service.price).toFixed(2)}</span>
      </div>
    </div>
  );
};

export default ServiceCard;
