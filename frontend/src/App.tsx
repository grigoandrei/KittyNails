import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './auth/AuthProvider';
import { RequireAuth } from './auth/RequireAuth';
import BookingWizard from './pages/BookingWizard';
import AppointmentLookup from './pages/AppointmentLookup';
import OwnerLogin from './pages/OwnerLogin';
import OwnerServices from './pages/OwnerServices';
import OwnerAvailability from './pages/OwnerAvailability';
import OwnerAppointments from './pages/OwnerAppointments';
import NotFound from './pages/NotFound';
import DashboardLayout from './components/DashboardLayout';

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
                <DashboardLayout>
                  <OwnerServices />
                </DashboardLayout>
              </RequireAuth>
            }
          />
          <Route
            path="/owner/dashboard/availability"
            element={
              <RequireAuth>
                <DashboardLayout>
                  <OwnerAvailability />
                </DashboardLayout>
              </RequireAuth>
            }
          />
          <Route
            path="/owner/dashboard/appointments"
            element={
              <RequireAuth>
                <DashboardLayout>
                  <OwnerAppointments />
                </DashboardLayout>
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
