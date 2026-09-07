from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm

def register(request):
    if request.method == "POST":
        if 'login_submit' in request.POST:
            login_form = AuthenticationForm(data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                return redirect("/home") 
            else:
                messages.error(request, 'Login failed. Please check the form for errors.')
                return render(request, "register/register.html", {'login_form': login_form})
        elif 'register_submit' in request.POST:
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                register_form.save()
                messages.success(request, 'Thank you for signing up. You can now login.')
                return redirect(request.path_info)  
            else:
                messages.error(request, 'Sign up failed. Please check the form for errors.')
                return render(request, "register/register.html", {'register_form': register_form})
    else:
        login_form = AuthenticationForm()
        register_form = RegisterForm()

    return render(request, "register/register.html", {'login_form': login_form, 'register_form': register_form})
