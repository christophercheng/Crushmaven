from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext

# -- Home Page --
# handles both member and guest home page
def home(request):
#    return HttpResponse("You are at the home page.")
    if request.user.is_authenticated():
        facebook_profile = request.user.get_profile().get_facebook_profile()
        return render_to_response('home.html',
                              {'facebook_profile': facebook_profile},
                              context_instance=RequestContext(request))
    else:
        return render(request,'home.html')

# -- Crush Search Page --
def search(request):
    return HttpResponse("You are at the crush search page.")

# -- Crush List Page --
def crush_list(request):
    return HttpResponse("You are at the My Crush List page.")

# -- Admirer List Page --
def admirer_list(request):
    return HttpResponse("You are at the My Admirer List page.")

# -- Not Interested List Page --
def not_interested_list(request):
    return HttpResponse("You are at the Not Interested List page.")

# -- Admirer Lineup Page --
def admirer_lineup(request):
    return HttpResponse("You are at the Admirer Lineup page.")

# -- Invite Friends Page --
def invite(request):
    return HttpResponse("You are at the Invite Friends page.")

# -- My Profile Page --
def my_profile(request):
    return HttpResponse("You are at the My Profile page.")

# -- My Credits Page --
def my_credits(request):
    return HttpResponse("You are at the My Credits page.")

# -- FAQ Page --
def faq(request):
    return HttpResponse("You are at the FAQ page.")

# -- Terms & Conditions Page --
def terms(request):
    return HttpResponse("You are at the Terms and Conditions page.")