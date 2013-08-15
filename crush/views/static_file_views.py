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
def help_privacy(request):
    return render(request,'help_privacy.html')

# -- Contact Us Page --
def help_contact(request):
    return render(request,'help_contact.html')

# -- Facebook Privacy Settings --
def help_fb_privacy_setting(request):
    return render(request,'help_fb_privacy_setting.html')