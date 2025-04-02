## Django Custom OAuth2 Provider - Flask Client Documentation

## Overview
This document explains how to integrate a Django OAuth2 provider with a Flask client.

## Variables
```
Base URL:         http://localhost:8000/oauth
Client ID:        23423423
Client Secret:    Ov23lipRJArXBVcwaV9zOv23lipRJArXBVcwaV9z
API Key:          232l4kj23l4j2l34j23l42l34242
Redirect URI:     http://localhost:5000/callback
Flask Client:     http://localhost:5000
```

## 1. Start Authorization Flow
To start the OAuth flow, visit the following link in your browser or use it in your application:
```
http://localhost:5000/login
```

## 2. Authorization Endpoint (Django)
This is where the `/login` route redirects to:
```
GET http://localhost:8000/oauth/authorize/?client_id=23423423&redirect_uri=http://localhost:5000/callback&response_type=code&state=random_state_string
```
Headers:
```
Accept: application/json
```

## 3. Token Exchange (Django)
Handled in the Flask `/callback` route:
```
POST http://localhost:8000/oauth/token/
```
Headers:
```
Content-Type: application/x-www-form-urlencoded
```
Body:
```
grant_type=authorization_code&code={{authorization_code}}&client_id=23423423&client_secret=Ov23lipRJArXBVcwaV9zOv23lipRJArXBVcwaV9z&redirect_uri=http://localhost:5000/callback
```

## 4. Get User Info (Django)
Handled in Flask `/dashboard` route:
```
GET http://localhost:8000/oauth/userinfo/
```
Headers:
```
Authorization: Bearer {{access_token}}
Accept: application/json
```

## 5. Get User Data (Django)
Handled in Flask `/dashboard` route:
```
GET http://localhost:8000/oauth/userdata/{{user_id}}/
```
Headers:
```
X-API-Key: {{apiKey}}
Accept: application/json
```

## 6. Logout (Django)
Handled in Flask `/logout` route:
```
POST http://localhost:8000/oauth/logout/
```
Headers:
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

## 7. Flask Client Endpoints

### Home Page
```
GET http://localhost:5000/
```

### Login Initiation
```
GET http://localhost:5000/login
```

### OAuth Callback (Handled Automatically)
```
GET http://localhost:5000/callback?code={{authorization_code}}&state=random_state_string
```

### Dashboard (Protected)
```
GET http://localhost:5000/dashboard
```
Headers:
```
Cookie: session={{session_cookie}}
```

### Logout
```
GET http://localhost:5000/logout
```

## Example Usage Flow
1. Visit `http://localhost:5000/login` in a browser.
2. You'll be redirected to the Django authorization page.
3. After login, you'll be redirected back to `http://localhost:5000/callback`.
4. Finally, you’ll be redirected to `http://localhost:5000/dashboard`.

## Notes
- Replace `{{authorization_code}}`, `{{access_token}}`, `{{user_id}}`, and `{{session_cookie}}` with actual values when testing.
- The Flask client runs on port `5000` by default.
- The Django OAuth provider runs on port `8000` by default.
- CSRF protection is handled via the `state` parameter.

## Contribution 
- You are welcome to add new features.
- Remember make it simple do not add complex features. (For full oauth2 and oidc suppor many packages are available)
- Add features that other oauth2+openid connect do not provide like it has userdata feature which can be use to store/get json object for userdata
- Recomended for adding security features

## Contact
``` contact@himelrana.com ```
``` www.himelrana.com ```
