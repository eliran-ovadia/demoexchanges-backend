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

      // Fetch the portfolio page using the token
      const portfolioResponse = await fetch('http://127.0.0.1:8000/portfolio', {
          method: 'GET',
          headers: {
              'Content-Type': 'text/html',
              'Authorization': `Bearer ${token}`,
          },
      });

      if (!portfolioResponse.ok) {
          throw new Error('Failed to load portfolio.');
      }

      const portfolioHtml = await portfolioResponse.text();

      // Insert the portfolio HTML into the current document
      document.body.innerHTML = portfolioHtml;

  } catch (error) {
      console.error('Login error:', error);
      alert('Login failed. Please try again.');
  }
});
