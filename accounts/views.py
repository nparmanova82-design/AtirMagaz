from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import LoginForm, ProfileForm, RegisterForm


class SignInView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Xush kelibsiz, {user.first_name}! Hisobingiz yaratildi.")
        return redirect(request.GET.get("next") or "accounts:profile")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ma'lumotlaringiz saqlandi.")
        return redirect("accounts:profile")
    orders = request.user.orders.prefetch_related("items")
    return render(request, "accounts/profile.html", {"form": form, "orders": orders})
