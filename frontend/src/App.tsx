import { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { Navbar } from "./components/Navbar";
import { Hero } from "./components/Hero";
import { Services } from "./components/Services";
import { Gallery } from "./components/Gallery";
import { Testimonials } from "./components/Testimonials";
import { Footer } from "./components/Footer";
import { BookingModal } from "./components/BookingModal";
import { AuthProvider } from "./admin/AuthContext";
import { AdminLayout } from "./admin/AdminLayout";
import { LoginPage } from "./admin/LoginPage";
import { DashboardPage } from "./admin/DashboardPage";
import { NailTypesPage } from "./admin/NailTypesPage";
import { DesignTiersPage } from "./admin/DesignTiersPage";
import { AvailabilityPage } from "./admin/AvailabilityPage";
import { BlockedTimesPage } from "./admin/BlockedTimesPage";
import { AppointmentsPage } from "./admin/AppointmentsPage";

function PublicSite() {
  const [isBookingOpen, setIsBookingOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar onBookNow={() => setIsBookingOpen(true)} />
      <main>
        <Hero onBookNow={() => setIsBookingOpen(true)} />
        <Services />
        <Gallery />
        <Testimonials />
      </main>
      <Footer />
      <BookingModal open={isBookingOpen} onOpenChange={setIsBookingOpen} />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Toaster position="top-center" richColors />
      <Routes>
        <Route path="/" element={<PublicSite />} />
        <Route path="/admin/login" element={<LoginPage />} />
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="nail-types" element={<NailTypesPage />} />
          <Route path="design-tiers" element={<DesignTiersPage />} />
          <Route path="availability" element={<AvailabilityPage />} />
          <Route path="blocked-times" element={<BlockedTimesPage />} />
          <Route path="appointments" element={<AppointmentsPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
