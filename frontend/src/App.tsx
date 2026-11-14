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
import { MonthlySetsSection } from "./components/MonthlySetsSection";
import type { MonthlySetDesign } from "./api";
import { BookingSuccess, BookingCancelled } from "./components/BookingResult";
import { AuthProvider } from "./admin/AuthContext";
import { AdminLayout } from "./admin/AdminLayout";
import { LoginPage } from "./admin/LoginPage";
import { DashboardPage } from "./admin/DashboardPage";
import { NailTypesPage } from "./admin/NailTypesPage";
import { DesignTiersPage } from "./admin/DesignTiersPage";
import { AvailabilityPage } from "./admin/AvailabilityPage";
import { BlockedTimesPage } from "./admin/BlockedTimesPage";
import { AppointmentsPage } from "./admin/AppointmentsPage";
import { MonthlySetsPage } from "./admin/MonthlySetsPage";

function PublicSite() {
  const [isBookingOpen, setIsBookingOpen] = useState(false);
  // Set when booking starts from the monthly set section so the modal opens on it.
  const [initialMonthlySet, setInitialMonthlySet] = useState<MonthlySetDesign | null>(null);

  function openBooking(design: MonthlySetDesign | null = null) {
    setInitialMonthlySet(design);
    setIsBookingOpen(true);
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar onBookNow={() => openBooking()} />
      <main>
        <Hero onBookNow={() => openBooking()} />
        <Services />
        <MonthlySetsSection onBook={openBooking} />
        <Gallery />
        <Testimonials />
      </main>
      <Footer />
      <BookingModal
        open={isBookingOpen}
        onOpenChange={setIsBookingOpen}
        initialMonthlySet={initialMonthlySet}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Toaster position="top-center" richColors />
      <Routes>
        <Route path="/" element={<PublicSite />} />
        <Route path="/booking/success" element={<BookingSuccess />} />
        <Route path="/booking/cancelled" element={<BookingCancelled />} />
        <Route path="/admin/login" element={<LoginPage />} />
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="nail-types" element={<NailTypesPage />} />
          <Route path="design-tiers" element={<DesignTiersPage />} />
          <Route path="availability" element={<AvailabilityPage />} />
          <Route path="blocked-times" element={<BlockedTimesPage />} />
          <Route path="appointments" element={<AppointmentsPage />} />
          <Route path="monthly-sets" element={<MonthlySetsPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
