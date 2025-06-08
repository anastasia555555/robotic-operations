import React from 'react';
import ReactDOM from 'react-dom/client';
import { Navigate, HashRouter, Routes, Route } from 'react-router-dom';
import AuthLayout from './layouts/AuthLayout';
import MainLayout from './layouts/MainLayout';
import NewAuthLayout from './layouts/NewAuthLayout';
import ChangeAuthLayout from './layouts/ChangeAuthLayout';
import OpPlanning from './pages/OpPlanning';
import PreOpPositioning from './pages/PreOpPositioning';
import RequireAuth from './components/RequireAuth';
import FilePicking from './pages/FilePicking';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <HashRouter>
      <Routes>
        <Route path="/" element={
          <RequireAuth>
            <MainLayout />
          </RequireAuth>
        }>
          <Route index element={<Navigate to="file-picking" replace />} />
          <Route path="file-picking" element={<FilePicking />} />
          <Route path="op-planning" element={<OpPlanning />} />
          <Route path="pre-op-positioning" element={<PreOpPositioning />} />
        </Route>
        <Route path="auth" element={<AuthLayout />} />
        <Route path="new-auth" element={<NewAuthLayout />} />
        <Route path="change-auth" element={<ChangeAuthLayout />} />
      </Routes>
    </HashRouter>
  </React.StrictMode>
);
