from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from urllib.parse import urlencode
import json
from datetime import timedelta
from django.utils import timezone
from .models import Client, AuthorizationCode, AccessToken, UserData
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate

@require_http_methods(["GET"])
def authorize(request):
    print("Received authorize request with params:", request.GET)  # Debug logging
    
    # Get all parameters - both from initial request and form submission
    client_id = request.GET.get('client_id')
    redirect_uri = request.GET.get('redirect_uri')
    response_type = request.GET.get('response_type')
    state = request.GET.get('state', '')
    authorize_action = request.GET.get('authorize')
    
    # Validate required parameters
    if not all([client_id, redirect_uri, response_type == 'code']):
        return HttpResponseBadRequest("Invalid request parameters")
    
    try:
        client = Client.objects.get(client_id=client_id)
    except Client.DoesNotExist:
        return HttpResponseBadRequest("Invalid client_id")
    
    if redirect_uri not in client.get_redirect_uris():
        return HttpResponseBadRequest("Invalid redirect_uri")
    
    # If user is not authenticated, redirect to login
    if not request.user.is_authenticated:
        login_url = '/login/?' + urlencode({
            'next': request.get_full_path(),
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'state': state,
        })
        return redirect(login_url)
    
    # If this is the authorization decision
    if authorize_action is not None:
        if authorize_action == '1':
            code = AuthorizationCode.create_code(request.user, client)
            
            # Include ALL original parameters in the redirect
            params = {
                'code': code.code,
                'state': state,
            }
            return redirect(f"{redirect_uri}?{urlencode(params)}")
        else:
            # User denied authorization
            return redirect(f"{redirect_uri}?error=access_denied&state={state}")
    
    # Show authorization page
    return render(request, 'oauth/authorize.html', {
        'client': client,
        'state': state,
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': response_type,
    })

@csrf_exempt
@require_http_methods(["POST"])
def token(request):
    grant_type = request.POST.get('grant_type')
    code = request.POST.get('code')
    client_id = request.POST.get('client_id')
    client_secret = request.POST.get('client_secret')
    redirect_uri = request.POST.get('redirect_uri')
    
    if grant_type != 'authorization_code':
        return JsonResponse({'error': 'unsupported_grant_type'}, status=400)
    
    try:
        client = Client.objects.get(client_id=client_id, client_secret=client_secret)
    except Client.DoesNotExist:
        return JsonResponse({'error': 'invalid_client'}, status=400)
    
    try:
        auth_code = AuthorizationCode.objects.get(
            code=code,
            client=client,
            used=False,
            expires_at__gt=timezone.now()
        )
    except AuthorizationCode.DoesNotExist:
        return JsonResponse({'error': 'invalid_grant'}, status=400)
    
    auth_code.used = True
    auth_code.save()
    
    token = AccessToken.create_token(auth_code.user, client)

    user = auth_code.user
    UserData.objects.get_or_create(
        user=user,
        defaults={
            'data': {
                'basic_info': {
                    'name': user.get_full_name(),
                    'email': user.email,
                    'username': user.username,
                    'date_joined': user.date_joined.isoformat()
                },
                'preferences': {},
                'created_at': timezone.now().isoformat()
            }
        }
    )
    
    return JsonResponse({
        'access_token': token.token,
        'token_type': 'Bearer',
        'expires_in': int((token.expires_at - timezone.now()).total_seconds()),
    })

@csrf_exempt  # If making POST requests later
@require_http_methods(["GET"])
def userinfo(request):
    # Check for Bearer token in Authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'invalid_token'}, status=401)
    
    token_str = auth_header[7:]  # Remove 'Bearer ' prefix
    
    try:
        token = AccessToken.objects.get(
            token=token_str,
            expires_at__gt=timezone.now()
        )
        user = token.user
    except AccessToken.DoesNotExist:
        return JsonResponse({'error': 'invalid_token'}, status=401)
    
    return JsonResponse({
        'sub': user.id,
        'username': user.username,
        'email': user.email,
        # Add other user fields as needed
    })

@csrf_exempt 
@require_http_methods(["POST"])
def logout(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'invalid_token'}, status=401)
    
    token_str = auth_header[7:]
    
    try:
        token = AccessToken.objects.get(token=token_str)
        token.delete()
    except AccessToken.DoesNotExist:
        pass
    
    AuthorizationCode.objects.filter(user=token.user, client=token.client).delete()
    
    return JsonResponse({'success': True})

@require_http_methods(["GET", "POST", "PUT", "PATCH", "DELETE"])
def userdata(request, user_id):
    api_key = request.headers.get('X-API-Key') or request.GET.get('api_key')
    
    if not api_key:
        return JsonResponse({'error': 'api_key_required'}, status=401)
    
    try:
        client = Client.objects.get(api_key=api_key)
    except Client.DoesNotExist:
        return JsonResponse({'error': 'invalid_api_key'}, status=401)
    
    try:
        user_data = UserData.objects.get(user__id=user_id)
    except UserData.DoesNotExist:
        if request.method in ['GET', 'DELETE']:
            return JsonResponse({'error': 'not_found'}, status=404)
        user_data = UserData.objects.create(user_id=user_id, data={})
    
    if request.method == 'GET':
        return JsonResponse(user_data.data)
    elif request.method == 'POST':
        try:
            new_data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid_json'}, status=400)
        user_data.data = new_data
        user_data.save()
        return JsonResponse(user_data.data)
    elif request.method in ['PUT', 'PATCH']:
        try:
            update_data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid_json'}, status=400)
        if request.method == 'PUT':
            user_data.data = update_data
        else:
            user_data.data.update(update_data)
        user_data.save()
        return JsonResponse(user_data.data)
    elif request.method == 'DELETE':
        user_data.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'method_not_allowed'}, status=405)