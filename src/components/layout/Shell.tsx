import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { token } from "@/lib/api";
import Sidebar from "./Sidebar";

export default function Shell({ children }: { children: ReactNode }) {
  if (!token()) return <Navigate to="/login" replace />;
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden">
        <div className="mx-auto max-w-[1400px] px-6 py-8 md:px-10 animate-fade-in-up">
          {children}
        </div>
      </main>
    </div>
  );
}
