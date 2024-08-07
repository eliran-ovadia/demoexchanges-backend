document.getElementById('login-form').addEventListener('submit', async function(event) {
  event.preventDefault();

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  try {
      const response = await fetch('http://127.0.0.1:8000/token', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
              'username': email,
              'password': password,
          }),
      });

      if (!response.ok) {
          throw new Error('Login failed. Please check your credentials.');
      }

      const data = await response.json();
      const token = data.access_token; // Assuming the token is returned in this field
      const token_to_save = "Bearer " + token;
      localStorage.setItem('token', token_to_save); //local stoge save to save the token for navigating to the portfolio page
      console.log('Token to save:', token_to_save);
      console.log('Stored token:', localStorage.getItem('token'));
      window.location.href = 'http://127.0.0.1:8000/portfolio';

  } catch (error) {
      console.error('Login error:', error);
      alert('Login failed. Please try again.');
  }
});
