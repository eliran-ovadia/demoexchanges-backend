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


    

});
