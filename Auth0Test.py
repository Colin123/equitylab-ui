import os
from flask import Flask, redirect, request, jsonify, session, render_template, url_for
from authlib.integrations.flask_client import OAuth
from urllib.parse import urlencode
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or "your-secret-key"  # Replace with a real secret key in production

# Auth0 configuration
AUTH0_CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET")
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN")
AUTH0_CALLBACK_URL = os.environ.get("AUTH0_CALLBACK_URL")
AUTH0_AUDIENCE = os.environ.get("AUTH0_AUDIENCE") 

# Initialize OAuth
oauth = OAuth(app)

# Register Auth0 client
auth0 = oauth.register(
    'auth0',
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    api_base_url=f"https://{AUTH0_DOMAIN}",
    access_token_url=f"https://{AUTH0_DOMAIN}/oauth/token",
    authorize_url=f"https://{AUTH0_DOMAIN}/authorize",
    jwks_uri=f"https://{AUTH0_DOMAIN}/.well-known/jwks.json", 
    client_kwargs={
        'scope': 'openid profile email',
    },
)

# Login required decorator
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

# Routes
@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Auth0 Login</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }
            .container { width: 80%; margin: 0 auto; padding: 20px; }
            .jumbotron { background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); }
            .btn { display: inline-block; padding: 10px 15px; background-color: #007bff; color: white; text-decoration: none; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="jumbotron">
                <h1>Welcome to the Auth0 Flask App</h1>
                <p>Click the button below to log in:</p>
                <a class="btn" href="/login">Login</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri=AUTH0_CALLBACK_URL)

@app.route('/callback')
def callback_handling():
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()
    
    # Store user information in session
    session['jwt_payload'] = userinfo
    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo.get('name', ''),
        'picture': userinfo.get('picture', ''),
        'email': userinfo.get('email', '')
    }
    
    return redirect('/dashboard')

@app.route('/health', methods=['GET'])
def health():
    print('Health check called')
    return jsonify(status="healthy"), 200 

@app.route('/dashboard')
@requires_auth
def dashboard():
    userinfo = session['profile']
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ width: 80%; margin: 0 auto; padding: 20px; }}
            .profile {{ background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); }}
            .profile-header {{ display: flex; align-items: center; margin-bottom: 20px; }}
            .profile-header img {{ width: 80px; height: 80px; border-radius: 50%; margin-right: 20px; }}
            .btn {{ display: inline-block; padding: 10px 15px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="profile">
                <div class="profile-header">
                    <img src="{userinfo['picture']}" alt="Profile picture">
                    <div>
                        <h2>{userinfo['name']}</h2>
                        <p>{userinfo['email']}</p>
                    </div>
                </div>
                <h3>User Information</h3>
                <p>User ID: {userinfo['user_id']}</p>
                <a class="btn" href="/logout">Logout</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/logout')
def logout():
    session.clear()
    params = {'returnTo': url_for('home', _external=True), 'client_id': AUTH0_CLIENT_ID}
    return redirect(f"https://{AUTH0_DOMAIN}/v2/logout?{urlencode(params)}")

if __name__ == '__main__':
    app.run(debug=True)

# if __name__ == '__main__':
#     app.run(host='localhost', debug=True, port=5000)