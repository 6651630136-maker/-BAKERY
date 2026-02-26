from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

# load configuration from .env (CLIENT_ID, CLIENT_SECRET, DATABASE_URL, etc.)
config = Config('.env')

oauth = OAuth(config)
oauth.register(
    name='github',
    client_id=config('GITHUB_CLIENT_ID', default=''),
    client_secret=config('GITHUB_CLIENT_SECRET', default=''),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

app = FastAPI()

# simple in-memory store for demo
users = {}

@app.get('/')
async def root():
    return {'message': 'Hello from backend'}

@app.get('/login/github')
async def login_via_github(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.github.authorize_redirect(request, redirect_uri)

@app.get('/auth')
async def auth(request: Request):
    token = await oauth.github.authorize_access_token(request)
    user = await oauth.github.parse_id_token(request, token)
    # or fetch profile: await oauth.github.get('user', token=token)
    users[user['login']] = token
    # in production return a cookie or JWT
    return JSONResponse({'username': user['login']})

@app.get('/protected')
async def protected(username: str = Depends(lambda: None)):
    if not username:
        raise HTTPException(status_code=401, detail='Not authenticated')
    return {'secret': 'data for ' + username}
