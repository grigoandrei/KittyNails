import React from 'react';

interface ErrorMessageProps {
  message: string;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ message }) => {
  return (
    <div
      className="error-message"
      role="alert"
      style={{
        backgroundColor: '#fdedef',
        color: '#c0392b',
        padding: '12px 16px',
        borderRadius: 8,
        border: '1px solid #f5c6cb',
        fontSize: 14,
        margin: '8px 0',
      }}
    >
      {message}
    </div>
  );
};

export default ErrorMessage;
