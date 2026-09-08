from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm, UserProfileForm
from .models import UserProfile
from competency.services import CompetencyService
from learning.services import RecommendationService

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Update profile info
            profile, _ = UserProfile.objects.get_or_create(user=user)
            dept = form.cleaned_data.get('department')
            role = form.cleaned_data.get('job_role')
            if dept:
                profile.department = dept
            if role:
                profile.job_role = role
            profile.save()

            # Initialize competency profile and recommendations
            CompetencyService.ensure_user_competencies(user)
            RecommendationService.generate_recommendations_for_user(user)

            login(request, user)
            messages.success(request, f"Welcome to SkillStat AI, {user.first_name or user.username}! Your competency profile is initialized.")
            return redirect('dashboard:index')
        else:
            messages.error(request, "Registration could not be completed. Please review errors below.")
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next') or 'dashboard:index'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. You may use demo / demo123.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out securely.")
    return redirect('accounts:login')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data.get('first_name', request.user.first_name)
            request.user.last_name = form.cleaned_data.get('last_name', request.user.last_name)
            request.user.email = form.cleaned_data.get('email', request.user.email)
            request.user.save()
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Error updating profile.")
    else:
        form = UserProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
    })
