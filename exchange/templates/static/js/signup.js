document.getElementById('signup-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const name = document.getElementById('firstname').value;
    const last_name = document.getElementById('lastname').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const signup_payload = {
        'name': name,
        'last_name': last_name,
        'email': email,
        'password': password
    };
    const url = '/api/createUser';

    const postSignupData = async (url, payload) => {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error('Error with the /createUser endpoint');
            }
            return response.json();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }

    try {
        const result = await postSignupData(url, signup_payload);
        console.log('Server response:', result);
        window.location.href = '/login'; // Redirect to login page on successful signup
    } catch (error) {
        alert('Signup failed. Please try again.');
    }
});
