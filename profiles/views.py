from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from .forms import UserProfileForm
from orders.models import Order

# Create your views here.


@login_required
def view_profile(request):
    """ Display user profile and order history"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=profile.user).order_by('-created')
    return render(
        request, 'profiles/view_profile.html', {'profile': profile,
                                                'orders': orders}
    )


@login_required
def edit_profile(request):
    """ Edit user profile """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profiles:view_profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'profiles/edit_profile.html', {'form': form})


@login_required
def delete_profile(request):
    """ Delete user profile """
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        profile.delete()
        messages.success(request, 'Profile deleted!')
        return redirect('home')

    return render(
        request, 'profiles/delete_profile.html', {'profile': profile}
    )

