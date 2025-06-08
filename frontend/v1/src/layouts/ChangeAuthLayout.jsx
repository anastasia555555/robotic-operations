import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './ChangeAuthLayout.css';

export default function ChangeAuthLayout() {
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/auth');
      return;
    }

    fetch('http://127.0.0.1:8000/users/me', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(data => setUsername(data.username))
      .catch(() => {
        localStorage.removeItem('token');
        navigate('/auth');
      });
  }, []);

  const handleSave = async () => {
    if (!currentPassword || !newPassword) {
      setError('Both current and new passwords are required.');
      return;
    }

    try {
      const response = await fetch(`http://127.0.0.1:8000/users/update_password?username=${username}&temp_password=${currentPassword}&new_password=${newPassword}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        localStorage.removeItem('token');
        localStorage.removeItem('role');
        localStorage.removeItem('username');
        navigate('/auth');
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to update password.');
      }
    } catch (error) {
      setError('Unable to connect to the server.');
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(prev => !prev);
  };

  const returnToAuthLayout = () => {
    navigate('/auth');
  };

  return (
    <div className="page">
      <div className="auth-content">
        <h1>Change password</h1>

        {username && <p>For: {username}</p>}

        <div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type={showPassword ? 'text' : 'password'}
              value={currentPassword}
              placeholder="current password"
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
            <input
              type={showPassword ? 'text' : 'password'}
              value={newPassword}
              placeholder="new password"
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <button onClick={togglePasswordVisibility}>
              {showPassword ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>

        {error && <p style={{ color: 'red' }}>{error}</p>}

        <button onClick={handleSave}>Save</button>
        <h5 onClick={returnToAuthLayout} style={{ cursor: 'pointer' }}>Go back</h5>
      </div>
    </div>
  );
}
