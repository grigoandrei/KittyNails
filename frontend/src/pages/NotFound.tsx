import { Link } from 'react-router-dom';

const NotFound: React.FC = () => {
  return (
    <div style={{ textAlign: 'center', padding: '4rem 1rem', maxWidth: 480, margin: '0 auto' }}>
      <h1 style={{ color: '#e91e8c', fontSize: 64, marginBottom: 8 }}>404</h1>
      <p style={{ color: '#666', fontSize: 18, marginBottom: 24 }}>
        Oops, this page doesn't exist.
      </p>
      <Link
        to="/"
        style={{
          display: 'inline-block',
          padding: '12px 24px',
          borderRadius: 8,
          backgroundColor: '#e91e8c',
          color: '#fff',
          textDecoration: 'none',
          fontSize: 16,
          fontWeight: 'bold',
        }}
      >
        Back to Home
      </Link>
    </div>
  );
};

export default NotFound;
