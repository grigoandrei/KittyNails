import React from 'react';

const LoadingSpinner: React.FC = () => {
  return (
    <div
      className="loading-spinner"
      role="status"
      aria-label="Loading"
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 24,
      }}
    >
      <div
        style={{
          width: 32,
          height: 32,
          border: '3px solid #f0e0eb',
          borderTopColor: '#e91e8c',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
};

export default LoadingSpinner;
