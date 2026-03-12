import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider } from './auth/AuthProvider';
import { RequireAuth } from './auth/RequireAuth';
import { BookingWizard } from './pages/BookingWizard';
import { AppointmentLookup } from './pages/AppointmentLookup';
import { OwnerLogin } from './pages/OwnerLogin';
import { OwnerServices } from './pages/OwnerServices';
import { OwnerAvailability } from './pages/OwnerAvailability';
import { OwnerAppointments } from './pages/OwnerAppointments';

function NotFound() {
  return (
    <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
      <h1>404</h1>
      <p>Page not found</p>
      <Link to="/">Back to home</Link>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<BookingWizard />} />
          <Route path="/appointment" element={<AppointmentLookup />} />
          <Route path="/owner/login" element={<OwnerLogin />} />
          <Route
            path="/owner/dashboard/services"
            element={
              <RequireAuth>
                <OwnerServices />
              </RequireAuth>
            }
          />
          <Route
            path="/owner/dashboard/availability"
            element={
              <RequireAuth>
                <OwnerAvailability />
              </RequireAuth>
            }
          />
          <Route
            path="/owner/dashboard/appointments"
            element={
              <RequireAuth>
                <OwnerAppointments />
              </RequireAuth>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
