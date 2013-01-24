from django.shortcuts import render

# -- How It Works Page --
def help_how_it_works(request):
    return render(request,'help_how_it_works.html')

# -- FAQ Page --
def help_faq(request):
    return render(request,'help_faq.html')

# -- Terms & Conditions Page --
def help_terms(request):
    return render(request,'help_terms.html')

# -- Privacy Policy Page --
def help_privacy_policy(request):
    return render(request,'privacy_policy.html')