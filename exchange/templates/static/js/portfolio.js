window.addEventListener('load', function() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      window.location.href = 'index.html';
    } else {
      fetch('http://your-api-url/protected-route', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Token validation failed');
        }
        return response.json();
      })
      .then(data => {
        console.log(data);
        // Display user-specific information or perform other actions
      })
      .catch(error => {
        console.error('Error:', error);
        localStorage.removeItem('access_token');
        window.location.href = 'index.html';
      });
    }
  });
  