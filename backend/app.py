from flask import Flask, jsonify, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
import os
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = os.urandom(24)

with open("debug_out.txt", "w") as f:
    f.write("DEBUG LOG\n")
def debug_out(message:str):
    with open("debug_out.txt", "a") as f:
        f.write(str(message) + "\n")

oauth = OAuth(app)

nonce = generate_token()


oauth.register(
    name=os.getenv('OIDC_CLIENT_NAME'),
    client_id=os.getenv('OIDC_CLIENT_ID'),
    client_secret=os.getenv('OIDC_CLIENT_SECRET'),
    #server_metadata_url='http://dex:5556/.well-known/openid-configuration',
    authorization_endpoint="http://localhost:5556/auth",
    token_endpoint="http://dex:5556/token",
    jwks_uri="http://dex:5556/keys",
    userinfo_endpoint="http://dex:5556/userinfo",
    device_authorization_endpoint="http://dex:5556/device/code",
    client_kwargs={'scope': 'openid email profile'}
)

# @app.route('/api/key')
# def get_key():
#     return jsonify({'apiKey': os.getenv('NYT_API_KEY')})

@app.route('/api/articles-query/<int:page>/<string:query>')
def fetch_article_query(page:int, query:str):
    key = os.getenv('NYT_API_KEY')
    return redirect(f"https://api.nytimes.com/svc/search/v2/articlesearch.json?q={query}&api-key={key}&page={page}", code=302)

@app.route('/api/articles-filter/<int:page>/<string:filter>')
def fetch_article_filter(page:int, filter:str):
    key = os.getenv('NYT_API_KEY')
    filter = filter.replace(":","%3A")
    debug_out(f"https://api.nytimes.com/svc/search/v2/articlesearch.json?fq={filter}&api-key={key}&page={page}")
    return redirect(f"https://api.nytimes.com/svc/search/v2/articlesearch.json?fq={filter}&api-key={key}&page={page}", code=302)


@app.route('/')
def home():
    user = session.get('user')
    if user:
        return f"<h2>Logged in as {user['email']}</h2><a href='/logout'>Logout</a>"
    return '<a href="/login">Login with Dex</a>'

@app.route('/login')
def login():
    session['nonce'] = nonce
    redirect_uri = 'http://localhost:8000/authorize'
    return oauth.flask_app.authorize_redirect(redirect_uri, nonce=nonce)

@app.route('/authorize')
def authorize():
    token = oauth.flask_app.authorize_access_token()
    nonce = session.get('nonce')

    user_info = oauth.flask_app.parse_id_token(token, nonce=nonce)  # or use .get('userinfo').json()
    session['user'] = user_info
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)


