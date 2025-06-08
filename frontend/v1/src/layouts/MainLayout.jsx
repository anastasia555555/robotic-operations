import './MainLayout.css'
import React from 'react';
import { Outlet } from 'react-router-dom';
import Toolbar from '../components/Toolbar.jsx';

const MainLayout = () => {
  
  return (
    <div className="page">
      <header className="toolbar">
        <Toolbar />
      </header>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;
