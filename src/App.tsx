import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Shell from "@/components/layout/Shell";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import LiveOTP from "./pages/LiveOTP";
import Numbers from "./pages/Numbers";
import Services from "./pages/Services";
import Countries from "./pages/Countries";
import Users from "./pages/Users";
import Withdrawals from "./pages/Withdrawals";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner theme="dark" />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Shell><Dashboard /></Shell>} />
          <Route path="/otp" element={<Shell><LiveOTP /></Shell>} />
          <Route path="/numbers" element={<Shell><Numbers /></Shell>} />
          <Route path="/services" element={<Shell><Services /></Shell>} />
          <Route path="/countries" element={<Shell><Countries /></Shell>} />
          <Route path="/users" element={<Shell><Users /></Shell>} />
          <Route path="/withdrawals" element={<Shell><Withdrawals /></Shell>} />
          <Route path="/settings" element={<Shell><Settings /></Shell>} />
          <Route path="/404" element={<NotFound />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
