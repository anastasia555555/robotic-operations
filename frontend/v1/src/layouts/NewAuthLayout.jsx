import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './NewAuthLayout.css';

export default function NewAuthLayout() {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmedPassword, setConfirmedPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [emailError, setEmailError] = useState('');

  const isValidEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const isValidPassword = (password, confirmedPassword) => {
    return password == confirmedPassword;
  };


  const handleLogin = () => {
    if (!email) {
      setEmailError('Email is required.');
      return;
    } else if (!isValidEmail(email)) {
      setEmailError('Enter a valid email address.');
      return;
    }

    setEmailError('');

    if (!password || !confirmedPassword) {
      setEmailError('Password is required.');
      return;
    } else if (!isValidPassword(password, confirmedPassword)) {
      setEmailError('Enter a valid password.');
      return;
    }

    localStorage.setItem('token', 'your-auth-token');
    navigate('/');
  };

  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev);
  };

  return (
    <div className="page">
      <div className="auth-content">
        <h1>Create account</h1>
  
        <div>
          <input
            type="email"
            value={email}
            placeholder="awesome_surgeon@example.com"
            onChange={(e) => setEmail(e.target.value)}
          />
          {emailError && <p>{emailError}</p>}
        </div>
  
        <div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              placeholder="new password"
              onChange={(e) => setPassword(e.target.value)}
            />
            <input
              type={showPassword ? 'text' : 'password'}
              value={confirmedPassword}
              placeholder="confirm password"
              onChange={(e) => setConfirmedPassword(e.target.value)}
            />
            <button onClick={togglePasswordVisibility}>
              {showPassword ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>
  
        <button onClick={handleLogin}>Save</button>
      </div>
    </div>
  );
  
}
