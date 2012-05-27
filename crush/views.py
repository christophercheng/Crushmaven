from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.conf import settings
from crush.models import *
from django.contrib.auth.models import User
# for search
import urllib, json, urlparse
from django.db import IntegrityError



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
    my_profile = request.user.get_profile()
    # fb_redirect_uri is used by facebook request dialog to redirect back
        # create it from scracth so that any get parameters (e.g. previously selected ID's) are removed
    fb_redirect_uri='http://' + request.get_host()+'/search/'
    crushee_id=''
    if 'to[0]' in request.GET:
        crushee_id=request.GET['to[0]']
        # find site user with this id
        
        try:
        # Try and find existing user
            fb_user = UserProfile.objects.get(facebook_id=crushee_id)
            user = fb_user.user 

        # No existing user, create one
        except UserProfile.DoesNotExist:
            fb_profile = urllib.urlopen('https://graph.facebook.com/' + crushee_id + '/?access_token=%s' % request.user.get_profile().access_token)
            fb_profile = json.load(fb_profile)
          
            username = fb_profile.get('username', fb_profile['id'])# if no username then grab id
            
            user = User.objects.create_user(username=username)
            user.first_name = fb_profile['first_name']
            user.last_name = fb_profile['last_name']
            user.is_active=False
            user.save()

                # Create the FacebookProfile
            fb_user = UserProfile(user=user, facebook_id=crushee_id)
            if ('gender' in fb_profile):
                if fb_profile['gender']==u'male':
                    fb_user.gender=u'M'
                elif fb_profile['gender']==u'female':
                        fb_user.gender=u'F'
            if('interested_in' in fb_profile):
                if len(fb_profile['interested_in'])==1: 
                    if fb_profile['interested_in'][0]==u'female':
                        fb_user.gender_pref=u'F'
                    else: 
                        fb_user.gender_pref=u'M'
                elif len(fb_profile['interested_in']) > 1:
                    fb_user.gender_pref=u'B'
            # Create all of the user's lists
            fb_user.my_crush_list=MyCrushList.objects.create()
            fb_user.my_secret_admirer_list=MySecretAdmirerList.objects.create()
            fb_user.my_open_admirer_list=MyOpenAdmirerList.objects.create()
            fb_user.my_not_interested_list=MyNotInterestedList.objects.create()
            fb_user.my_maybe_list=MyMaybeList.objects.create()
            fb_user.my_featured_maybe_list=MyFeaturedMaybeList.objects.create()
            fb_user.save()
        # now that the user is definitely on the system, add that user to the crush list
            new_crush_relationship = Relationship(other_person=user,crush_list=my_profile.my_crush_list,crush_state=u'WAITING',
                                                  friendship_type=u'FRIEND')
            new_crush_relationship.save()

        
    return render_to_response('search.html',
                              {'facebook_profile': my_profile, 
                               'facebook_app_id': settings.FACEBOOK_APP_ID, 
                               'redirect_uri': fb_redirect_uri,
                               'crushee_id':crushee_id},
                              context_instance=RequestContext(request))
    

# -- Crush List Page --
@login_required
def crush_list(request):
    my_profile = request.user.get_profile()
    if (my_profile.my_crush_list.list_members):
        all_members = my_profile.my_crush_list.list_members.all()
    return render_to_response('crush_list.html',
                              {'facebook_profile': my_profile, 'crushee_list':all_members},
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