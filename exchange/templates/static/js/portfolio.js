document.addEventListener('DOMContentLoaded', function() {

    const token = localStorage.getItem("token"); //get the token from local storage

    if (!token) {
        window.location.href = 'http://127.0.0.1:8000/login'; //check to see if the token exists
    }

    const token_parts = token.split('.'); //split token to parts
    const token_payload = JSON.parse(atob(token_parts[1])); //get the payload from the token

    console.log(token_payload); //print token payload to console (for debugging purposes)
    if (token_payload.exp < Date.now() / 1000) {
        window.location.href = 'http://127.0.0.1:8000/login'; //check to see if the token is still valid
      }


    if (token_parts.length !== 3) {
       throw new Error('Invalid JWT token'); //check if token contains all 3 parts
    }

    console.log(token); //print token to console (for debugging purposes)


    const current_user_name = token_payload.name; //get the name from the token
    document.getElementById('name').innerHTML = current_user_name; //display the name in the summeray section

    //JWT and name handling ------------------------------------------------------------

    const BASE_API_URL = 'http://127.0.0.1:8000/api';

    const fetchWithToken = async (url, token) => {  //a function to easly fetch data with the token
        try {
        const response = await fetch(url, {
            headers: {
                Authorization: token
            },
        });
        return response.json();
    } catch (error) {
        console.error('Error:', error);
    }
    };//------------------------

    const updateDOMWithPortfolioData = (data) => {
        if (!data || !data.balance || typeof data.balance === 'undefined') {
            console.error('Error: Portfolio data or account value is undefined.');
            return;
        }
        
        // Extract balance data from 'data' object
        const { balance } = data;
    
        // Update DOM elements with portfolio data
        try {
            document.querySelector('#account_value p').textContent = `$${balance.account_value.toFixed(2)}`;
            document.querySelector('#buying_power p').textContent = `$${balance.Buying_power.toFixed(2)}`;
            document.querySelector('#portfolio_value p').textContent = `$${balance.portfolio_value.toFixed(2)}`;
            document.querySelector('#total_return p').textContent = `$${balance.total_return.toFixed(2)}`;
            document.querySelector('#total_return_percent p').textContent = `${balance.total_return_percent.toFixed(2)}%`;
        } catch (error) {
            console.error('Error updating DOM with portfolio data:', error);
        }
    };//--------------------------

    fetchWithToken(BASE_API_URL + '/getPortfolio', token) //fetching getportfolio for the account summary cube
            .then(data => {
                if (data) {
                    updateDOMWithPortfolioData(data);
                }
            })
            .catch(error => console.error('(promiseError) Error in fetchWithToken:', error));
    //-------------------------
    
});
