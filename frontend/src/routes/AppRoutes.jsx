import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { useAdmin } from '../context/AdminContext.jsx';
import FarmerLayout from '../layouts/FarmerLayout.jsx';
import AuthLayout from '../layouts/AuthLayout.jsx';
import AdminLayout from '../layouts/AdminLayout.jsx';
import LoginPage from '../pages/auth/LoginPage.jsx';
import OtpVerifyPage from '../pages/auth/OtpVerifyPage.jsx';
import AdminLoginPage from '../pages/admin/AdminLoginPage.jsx';
import AdminDashboardPage from '../pages/admin/AdminDashboardPage.jsx';
import AdminFarmersPage from '../pages/admin/AdminFarmersPage.jsx';
import AdminCentresPage from '../pages/admin/AdminCentresPage.jsx';
import AdminBookingsPage from '../pages/admin/AdminBookingsPage.jsx';
import AdminCropsPage from '../pages/admin/AdminCropsPage.jsx';
import AdminSlotsPage from '../pages/admin/AdminSlotsPage.jsx';
import AdminReviewsPage from '../pages/admin/AdminReviewsPage.jsx';
import AdminQueuePage from '../pages/admin/AdminQueuePage.jsx';
import AdminProcurementPage from '../pages/admin/AdminProcurementPage.jsx';
import AdminBankPage from '../pages/admin/AdminBankPage.jsx';
import AdminPaymentsPage from '../pages/admin/AdminPaymentsPage.jsx';
import AdminReportsPage from '../pages/admin/AdminReportsPage.jsx';
import AdminIssuesPage from '../pages/admin/AdminIssuesPage.jsx';
import AdminAuditPage from '../pages/admin/AdminAuditPage.jsx';
import AdminMLPage from '../pages/admin/AdminMLPage.jsx';
import DashboardPage from '../pages/farmer/DashboardPage.jsx';
import SellCrop from '../pages/farmer/SellCrop.jsx';
import MyBooking from '../pages/farmer/MyBooking.jsx';
import BankDetails from '../pages/farmer/BankDetails.jsx';
import History from '../pages/farmer/History.jsx';
import CentreListPage from '../pages/farmer/CentreListPage.jsx';
import SlotSelectionPage from '../pages/farmer/SlotSelectionPage.jsx';
import BookingPage from '../pages/farmer/BookingPage.jsx';
import BookingSuccessPage from '../pages/farmer/BookingSuccessPage.jsx';
import QueuePage from '../pages/farmer/QueuePage.jsx';
import BookingDetailPage from '../pages/farmer/BookingDetailPage.jsx';

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function GuestRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : children;
}

function AdminProtectedRoute({ children }) {
  const { isAuthenticated } = useAdmin();
  return isAuthenticated ? children : <Navigate to="/admin/login" replace />;
}

function AdminGuestRoute({ children }) {
  const { isAuthenticated } = useAdmin();
  return isAuthenticated ? <Navigate to="/admin/dashboard" replace /> : children;
}

export default function AppRoutes() {
  return (
    <Routes>
      {/* ── Farmer Auth routes ── */}
      <Route element={<GuestRoute><AuthLayout /></GuestRoute>}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/verify-otp" element={<OtpVerifyPage />} />
      </Route>

      {/* ── Admin Auth routes ── */}
      <Route element={<AdminGuestRoute><AuthLayout /></AdminGuestRoute>}>
        <Route path="/admin/login" element={<AdminLoginPage />} />
      </Route>

      {/* ── Protected farmer routes ── */}
      <Route element={<ProtectedRoute><FarmerLayout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/sell" element={<SellCrop />} />
        <Route path="/my-booking" element={<MyBooking />} />
        <Route path="/bank-details" element={<BankDetails />} />
        <Route path="/history" element={<History />} />
        <Route path="/centres" element={<CentreListPage />} />
        <Route path="/centres/:centreId/slots" element={<SlotSelectionPage />} />
        <Route path="/booking" element={<BookingPage />} />
        <Route path="/booking-success" element={<BookingSuccessPage />} />
        <Route path="/queue/:bookingId" element={<QueuePage />} />
        <Route path="/booking-detail/:bookingId" element={<BookingDetailPage />} />
      </Route>

      {/* ── Protected admin routes ── */}
      <Route element={<AdminProtectedRoute><AdminLayout /></AdminProtectedRoute>}>
        <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
        <Route path="/admin/reviews" element={<AdminReviewsPage />} />
        <Route path="/admin/queue" element={<AdminQueuePage />} />
        <Route path="/admin/procurement" element={<AdminProcurementPage />} />
        <Route path="/admin/bank" element={<AdminBankPage />} />
        <Route path="/admin/payments" element={<AdminPaymentsPage />} />
        <Route path="/admin/reports" element={<AdminReportsPage />} />
        <Route path="/admin/issues" element={<AdminIssuesPage />} />
        <Route path="/admin/audit" element={<AdminAuditPage />} />
        <Route path="/admin/ml" element={<AdminMLPage />} />
        <Route path="/admin/crops" element={<AdminCropsPage />} />
        <Route path="/admin/centres" element={<AdminCentresPage />} />
        <Route path="/admin/slots" element={<AdminSlotsPage />} />
        <Route path="/admin/farmers" element={<AdminFarmersPage />} />
        <Route path="/admin/bookings" element={<AdminBookingsPage />} />
      </Route>

      {/* Root redirect */}
      <Route path="/" element={<Navigate to="/login" replace />} />

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
