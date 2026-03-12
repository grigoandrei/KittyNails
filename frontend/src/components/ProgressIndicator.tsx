import React from 'react';

interface ProgressIndicatorProps {
  currentStep: number;
  steps: string[];
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ currentStep, steps }) => {
  return (
    <div className="progress-indicator" style={{ display: 'flex', justifyContent: 'center', gap: '8px', margin: '16px 0' }}>
      {steps.map((label, index) => (
        <div
          key={index}
          data-testid={`step-${index}`}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: index === currentStep ? '#e91e8c' : '#f0e0eb',
              color: index === currentStep ? '#fff' : '#999',
              fontWeight: index === currentStep ? 'bold' : 'normal',
              fontSize: 14,
            }}
          >
            {index + 1}
          </div>
          <span
            style={{
              fontSize: 14,
              color: index === currentStep ? '#e91e8c' : '#999',
              fontWeight: index === currentStep ? 'bold' : 'normal',
            }}
            data-active={index === currentStep}
          >
            {label}
          </span>
          {index < steps.length - 1 && (
            <span style={{ margin: '0 4px', color: '#ccc' }}>›</span>
          )}
        </div>
      ))}
    </div>
  );
};

export default ProgressIndicator;
