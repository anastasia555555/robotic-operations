import './Toolbar.css';
import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Toolbar = () => {
  const [accountName, setAccountName] = useState('');
  const [role, setRole] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAccountName = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/auth');
        return;
      }

      try {
        const response = await fetch(`http://127.0.0.1:8000/users/me`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          setAccountName(data.username);
          setRole(data.role);
          localStorage.setItem('role', data.role);
        } else {
          localStorage.removeItem('token');
          navigate('/auth');
        }
      } catch (error) {
        localStorage.removeItem('token');
        navigate('/auth');
      }
    };

    fetchAccountName();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('username');
    navigate('/auth');
  };

  const handleChangePassword = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/users/set_temp_password?username=${accountName}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        navigate('/change-auth');
      } else {
        alert('Failed to initiate password change.');
      }
    } catch (error) {
      alert('Error connecting to the server.');
    }
  };

  return (
    <div className="toolbar-item">
      <div className="logo-section">
        <Link to="/file-picking">
          <img src="/klipartz.com.white.png" alt="Logo" className="logo" />
        </Link>
      </div>

      <div className="operation-planing">
        <Link to="/op-planning" className="tab-title">Operation Planning</Link>
      </div>

      <div className="pre-op-positioning">
        <Link to="/pre-op-positioning" className="tab-title">Pre-Op Positioning</Link>
      </div>

      <div className="account-dropdown">
        <span className="account-name">{accountName}</span>
        <ul className="dropdown-menu">
          <li onClick={handleChangePassword} style={{ cursor: 'pointer' }}>Change password</li>
          <li onClick={handleLogout} style={{ cursor: 'pointer' }}>Log out</li>
        </ul>
      </div>
    </div>
  );
};

export default Toolbar;
