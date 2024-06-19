document.getElementById('login-form').addEventListener('submit', async function(event) {
    event.preventDefault();
  
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
  
    const response = await fetch('http://127.0.0.1:8000/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        'username': email,
        'password': password,
      }),
    });
  
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      window.location.href = 'portfolio.html';
    } else {
      alert('Login failed. Please check your credentials.');
    }
  });
  