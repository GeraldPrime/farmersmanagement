from django.shortcuts import redirect

# Hardcode the login path to avoid any reverse() failures during middleware execution
_LOGIN_PATH = '/login/'

EXEMPT_PREFIXES = (
    '/login/',              # our own login page — must not loop
    '/vendor/',             # vendor auth handled by @login_required decorators
    '/api/lgas/',           # public AJAX used in registration forms
    '/api/verify-identity/', # shared verify endpoint — vendor + admin pages
    '/static/',
    '/media/',
)


class AdminAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Paths that bypass this middleware entirely
        if any(path.startswith(p) for p in EXEMPT_PREFIXES):
            return self.get_response(request)

        # All other paths require a logged-in staff user
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect(f'{_LOGIN_PATH}?next={path}')

        return self.get_response(request)
