from django.middleware.security import SecurityMiddleware
from whitenoise.middleware import WhiteNoiseMiddleware
from django.middleware.csrf import CsrfViewMiddleware
from django.middleware.clickjacking import XFrameOptionsMiddleware
from axes.middleware import AxesMiddleware
from django.core.exceptions import SuspiciousOperation
from django.core.cache import cache
from django.shortcuts import redirect
import hashlib
import base64
import os

# Middleware to validate the host header
class HostHeaderValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.get_host() != 'sscegov.com':
            raise SuspiciousOperation("Invalid Host Header")
        
        response = self.get_response(request)
        return response

# Middleware to add X-XSS-Protection header
class XSSProtectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-XSS-Protection'] = '1; mode=block'
        return response

# Middleware to disable client-side caching
class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

# Middleware to set Content Security Policy (CSP) with nonce for inline scripts
class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Generate a nonce for inline scripts
        nonce = base64.b64encode(os.urandom(16)).decode('utf-8')

        # Define the Content Security Policy (CSP) header
        csp_header = (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' cdn.amcharts.com; "
            f"img-src 'self' data: https://cdn.gtranslate.net/ https://i.ytimg.com/; "
            f"font-src 'self' https://fonts.googleapis.com/ https://fonts.gstatic.com/; "
            f"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com/; "
            f"frame-ancestors 'self' https://open.spotify.com; "
            f"frame-src 'self' https://open.spotify.com; "
            f"connect-src 'self' https://sscegov.com/; "
            f"worker-src 'self'; "
            f"report-uri /csp-report-endpoint;"
        )
        
        # Attach the CSP header to the response
        response["Content-Security-Policy"] = csp_header
        response["Content-Security-Policy-Report-Only"] = csp_header  # Optional: Only for monitoring
        
        # Add nonce to the response context if needed for templates
        response.context_data = {"csp_nonce": nonce}

        return response

# Middleware to ensure single session per user
class SingleSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_session_key = request.session.session_key
            stored_session_key = cache.get(f'session_key_for_user_{request.user.pk}')
            if stored_session_key and stored_session_key != current_session_key:
                request.session.flush()  # Terminate the current session
                return redirect('login')
            cache.set(f'session_key_for_user_{request.user.pk}', current_session_key)

        response = self.get_response(request)
        return response

# Updated MIDDLEWARE list
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',  # Brute-force attack protection
    'path.to.HostHeaderValidationMiddleware',  # Activate Host Header validation
    'path.to.XSSProtectionMiddleware',  # XSS protection header
    'path.to.NoCacheMiddleware',  # Disable caching
    'path.to.ContentSecurityPolicyMiddleware',  # CSP with nonce
    'path.to.SingleSessionMiddleware',  # Single session enforcement
]
