from django.shortcuts import redirect


def vendor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (getattr(request.user, 'user_type', None) == 'vendor' or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper


def customer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (getattr(request.user, 'user_type', None) == 'customer' or request.user.is_superuser or getattr(request.user, 'user_type', None) == 'admin'):
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (getattr(request.user, 'user_type', None) == 'admin' or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper
