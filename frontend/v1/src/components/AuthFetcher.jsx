
export const authFetch = (url, options = {}) => {
    const token = localStorage.getItem('token');
    return fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
  };