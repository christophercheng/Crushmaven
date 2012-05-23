from django.http import HttpResponse

# -- Home Page --
# handles both member and guest home page
def home(request):
    return HttpResponse("You are at the home page.")

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