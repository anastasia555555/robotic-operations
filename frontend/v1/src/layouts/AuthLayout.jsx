import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './AuthLayout.css';

export default function AuthLayout() {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [loginError, setLoginError] = useState('');

  const isValidEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const handleLogin = async () => {
    if (!email) {
      setEmailError('Email is required.');
      return;
    } else if (!isValidEmail(email)) {
      setEmailError('Enter a valid email address.');
      return;
    }

    setEmailError('');
    setLoginError('');

    try {
      const response = await fetch('http://127.0.0.1:8000/users/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        setLoginError(data.detail || 'Login failed.');
        return;
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token);

      const meResponse = await fetch('http://127.0.0.1:8000/users/me', {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      });

      if (!meResponse.ok) {
        setLoginError('Failed to fetch user profile.');
        return;
      }

      const meData = await meResponse.json();
      localStorage.setItem('username', meData.username);
      localStorage.setItem('role', meData.role);

        navigate('/');

    } catch (error) {
      setLoginError('Unable to connect to the server.');
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev);
  };

  const handleForgotPassword = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/users/set_temp_password?username=${email}`, {
        method: 'POST'
      });

      if (response.ok) {
        navigate('/change-auth');
      } else {
        const data = await response.json();
        setEmailError(data.detail || 'Failed to reset password.');
      }
    } catch (error) {
      setEmailError('Unable to connect to the server.');
    }
  };

  return (
    <div className="page">
      <div className="auth-content">
        <h1>Login</h1>

        <div>
          <input
            type="email"
            value={email}
            placeholder="awesome_surgeon@example.com"
            onChange={(e) => setEmail(e.target.value)}
          />
          {emailError && <p style={{ color: 'red' }}>{emailError}</p>}
        </div>

        <div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              placeholder="password"
              onChange={(e) => setPassword(e.target.value)}
            />
            <button onClick={togglePasswordVisibility}>
              {showPassword ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>

        {loginError && <p style={{ color: 'red' }}>{loginError}</p>}

        <button onClick={handleLogin}>Log In</button>
        <button onClick={handleForgotPassword}>Forgot password?</button>
      </div>
    </div>
  );
}
