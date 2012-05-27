from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.conf import settings

# -- Home Page --
# handles both member and guest home page
def home(request):
#    return HttpResponse("You are at the home page.")
    if request.user.is_authenticated():
        facebook_profile = request.user.get_profile().get_facebook_profile()
        return render_to_response('member_home.html',
                              {'facebook_profile': facebook_profile},
                              context_instance=RequestContext(request))
    else:
        return render(request,'guest_home.html')

# -- Crush Search Page --
@login_required(redirect_field_name='/')
def search(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    # fb_redirect_uri is used by facebook request dialog to redirect back
        # create it from scracth so that any get parameters (e.g. previously selected ID's) are removed
    fb_redirect_uri='http://' + request.get_host()+'/search/'
    crushee_id=''
    if 'to[0]' in request.GET:
        crushee_id=request.GET['to[0]']
    return render_to_response('search.html',
                              {'facebook_profile': facebook_profile, 
                               'facebook_app_id': settings.FACEBOOK_APP_ID, 
                               'redirect_uri': fb_redirect_uri,
                               'crushee_id':crushee_id},
                              context_instance=RequestContext(request))
    

# -- Crush List Page --
@login_required
def crush_list(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('crush_list.html',
                              {'facebook_profile': facebook_profile},
                              context_instance=RequestContext(request))

# -- Admirer List Page --
@login_required
def secret_admirer_list(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('secret_admirer_list.html',
                              {'facebook_profile': facebook_profile},
                              context_instance=RequestContext(request))

# -- Not so Secret Admirer List Page --
@login_required
def open_admirer_list(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('open_admirer_list.html',
                              {'facebook_profile': facebook_profile},
                              context_instance=RequestContext(request))

# -- Not Interested List Page --
@login_required
def not_interested_list(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('not_interested_list.html',
                              {'facebook_profile': facebook_profile},
                              context_instance=RequestContext(request))

# -- Admirer Lineup Page --
@login_required
def admirer_lineup(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('admirer_list.html',
                              {'facebook_profile': facebook_profile},
                              context_instance=RequestContext(request))

# -- Invite Friends Page --
@login_required
def invite(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('invite.html',
                              {'facebook_profile': facebook_profile},
                              context_instance=RequestContext(request))

# -- My Profile Page --
@login_required
def my_profile(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('my_profile.html',
                              {'facebook_profile': facebook_profile},
                              context_instance=RequestContext(request))

# -- My Credits Page --
@login_required
def my_credits(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('my_credits.html',
                              {'facebook_profile': facebook_profile},
                              context_instance=RequestContext(request))
    
# -- Logout --
@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/home/")

# -- FAQ Page --
def faq(request):
    return HttpResponse("You are at the FAQ page.")

# -- Terms & Conditions Page --
def terms(request):
    return HttpResponse("You are at the Terms and Conditions page.")