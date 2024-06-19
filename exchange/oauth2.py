from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from . import token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class RedirectException(HTTPException):
    def __init__(self, redirect_url: str):
        super().__init__(status_code=307, detail="Redirecting to login page")
        self.redirect_url = redirect_url
        
        

def get_current_user(data: str = Depends(oauth2_scheme)):
    credentials_exception = RedirectException(redirect_url="/") #if JWT bearer not found
    return token.verify_token(data, credentials_exception)