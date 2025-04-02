from flask import Flask, redirect, request, session, render_template, flash
import requests
import os
from datetime import datetime
from urllib.parse import urlencode
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration - replace with your Django OAuth provider details
OAUTH_PROVIDER = "http://localhost:8000/oauth"  # Your Django server
CLIENT_ID = "23423423"
CLIENT_SECRET = "Ov23lipRJArXBVcwaV9zOv23lipRJArXBVcwaV9z"
API_KEY = "232l4kj23l4j2l34j23l42l34242"
REDIRECT_URI = "http://localhost:5000/callback"  # Your Flask client

@app.route('/')
def index():
    if 'access_token' in session:
        return render_template('dashboard.html')
    return render_template('index.html')

@app.route('/login')
def login():
    # Start OAuth flow by redirecting to authorization endpoint
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'state': os.urandom(16).hex()  # CSRF protection
    }
    auth_url = f"{OAUTH_PROVIDER.rstrip('/')}/authorize/?{urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Handle the callback from the OAuth provider
    error = request.args.get('error')
    if error:
        return f"Authorization failed: {error}"
    
    code = request.args.get('code')
    if not code:
        return "Authorization failed: no code received"
    
    # Exchange code for token
    token_response = requests.post(
        f"{OAUTH_PROVIDER}/token/",
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI
        }
    )
    
    if token_response.status_code != 200:
        return f"Token exchange failed: {token_response.text}"
    
    token_data = token_response.json()
    session['access_token'] = token_data['access_token']
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    """
    Dashboard route using print() for debugging
    """
    print(f"\n[{datetime.now()}] Dashboard accessed - checking session")
    
    # Check if access token exists in session
    if 'access_token' not in session:
        print("No access token found - redirecting to home")
        flash('Please login first', 'error')
        return redirect('/')
    
    try:
        # Fetch user info
        headers = {'Authorization': f'Bearer {session["access_token"]}'}
        print(f"Making request to {OAUTH_PROVIDER}/userinfo/")
        
        user_info = requests.get(
            f"{OAUTH_PROVIDER}/userinfo/",
            headers=headers,
            timeout=5
        )
        
        print(f"User info response: {user_info.status_code}")
        
        # Handle token expiration
        if user_info.status_code == 401:
            print("Token expired or invalid - clearing session")
            session.pop('access_token', None)
            flash('Your session has expired. Please login again.', 'warning')
            return redirect('/login')
        
        user_info.raise_for_status()
        user_data = user_info.json()
        print(f"User data received: {user_data.get('username')}")
        
        # Fetch custom data
        custom_data = {}
        try:
            print(f"Fetching custom data for user {user_data['sub']}")
            data_resp = requests.get(
                f"{OAUTH_PROVIDER}/userdata/{user_data['sub']}/",
                headers={'X-API-Key': API_KEY},
                timeout=3
            )
            print(data_resp)
            if data_resp.status_code == 200:
                custom_data = data_resp.json()
                print("Custom data received successfully")
            else:
                print(f"Custom data response: {data_resp.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Custom data request failed: {str(e)}")
        
        print("Rendering dashboard template")
        return render_template(
            'dashboard.html',
            user=user_data,
            custom_data=custom_data
        )
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {str(e)}")
        session.clear()
        flash('Server communication error. Please try again.', 'error')
        return redirect('/')
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        session.clear()
        flash('An unexpected error occurred.', 'error')
        return redirect('/')

@app.route('/logout')
def logout():
    if 'access_token' in session:
        # Revoke the token server-side
        headers = {'Authorization': f"Bearer {session['access_token']}"}
        data = requests.post(f"{OAUTH_PROVIDER}/logout/", headers=headers)
        print("logout data: ", data)
    # Clear session
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=5000)