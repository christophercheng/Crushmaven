from django.http import HttpResponse

# -- How It Works Page --
def help_how_it_works(request):
    return HttpResponse("You are at the How It Works page.")

# -- FAQ Page --
def help_faq(request):
    return HttpResponse("You are at the FAQ page.")

# -- Terms & Conditions Page --
def help_terms(request):
    return HttpResponse("You are at the Terms and Conditions page.")

# -- Privacy Policy Page --
def help_privacy_policy(request):
    return HttpResponse("You are at the Privacy Policy page.")