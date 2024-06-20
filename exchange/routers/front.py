from fastapi import APIRouter, Depends
from .. import database, schemas
from ..oauth2 import get_current_user
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(tags = ['frontEnd'])

check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)

@router.get('/', response_class=HTMLResponse)
def get_index():
    with open("exchange/templates/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)
    
@router.get('/portfolio', response_class=HTMLResponse)
def get_portfolio(current_user: schemas.User = check_auth):
    with open("exchange/templates/portfolio.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)