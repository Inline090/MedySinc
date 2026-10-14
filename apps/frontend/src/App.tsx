import { Route, Routes } from "react-router-dom";

import AppShell from "@/layouts/AppShell";
import AuthShell from "@/layouts/AuthShell";
import Ask from "@/pages/Ask";
import Dashboard from "@/pages/Dashboard";
import DocumentDetail from "@/pages/DocumentDetail";
import Documents from "@/pages/Documents";
import Home from "@/pages/Home";
import Medications from "@/pages/Medications";
import SignIn from "@/pages/SignIn";
import SignUp from "@/pages/SignUp";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />

      <Route element={<AuthShell />}>
        <Route path="/sign-in" element={<SignIn />} />
        <Route path="/sign-up" element={<SignUp />} />
      </Route>

      <Route element={<AppShell />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/documents/:id" element={<DocumentDetail />} />
        <Route path="/medications" element={<Medications />} />
        <Route path="/ask" element={<Ask />} />
      </Route>
    </Routes>
  );
}
