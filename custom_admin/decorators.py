from django.shortcuts import redirect
from functools import wraps

def admin_login_required(function=None, session_key='email'):
    def decorator(view_func):
        @wraps(view_func)
        def f(request, *args, **kwargs):
            if session_key in request.session:
                return view_func(request, *args, **kwargs)
            return redirect('login')
        return f
    if function is not None:
        return decorator(function)
    return decorator