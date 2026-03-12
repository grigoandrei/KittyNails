import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';

const navStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 8,
  padding: '12px 24px',
  backgroundColor: '#fff0f6',
  borderBottom: '2px solid #f0e0eb',
  flexWrap: 'wrap',
};

const linkBase: React.CSSProperties = {
  padding: '8px 16px',
  borderRadius: 8,
  fontSize: 15,
  fontWeight: 500,
  textDecoration: 'none',
  color: '#e91e8c',
  transition: 'background-color 0.2s, color 0.2s',
};

const activeLinkStyle: React.CSSProperties = {
  ...linkBase,
  backgroundColor: '#e91e8c',
  color: '#fff',
};

const logoutBtnStyle: React.CSSProperties = {
  marginLeft: 'auto',
  padding: '8px 18px',
  borderRadius: 8,
  border: '1px solid #e91e8c',
  backgroundColor: '#fff',
  color: '#e91e8c',
  fontSize: 14,
  fontWeight: 600,
  cursor: 'pointer',
};

const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { logout } = useAuth();

  return (
    <div>
      <nav style={navStyle} aria-label="Owner dashboard navigation">
        <NavLink
          to="/owner/dashboard/services"
          style={({ isActive }) => (isActive ? activeLinkStyle : linkBase)}
        >
          Services
        </NavLink>
        <NavLink
          to="/owner/dashboard/availability"
          style={({ isActive }) => (isActive ? activeLinkStyle : linkBase)}
        >
          Availability
        </NavLink>
        <NavLink
          to="/owner/dashboard/appointments"
          style={({ isActive }) => (isActive ? activeLinkStyle : linkBase)}
        >
          Appointments
        </NavLink>
        <button onClick={logout} style={logoutBtnStyle}>
          Logout
        </button>
      </nav>
      <main>{children}</main>
    </div>
  );
};

export default DashboardLayout;
