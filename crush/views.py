from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.conf import settings
from crush.models import UserProfile, SecretCrushRelationship,CrushRelationship, OpenCrushRelationship
from django.middleware import csrf
#from django.contrib.auth.models import Use
# to allow app to run in facebook canvas without csrf error:
from django.views.decorators.csrf import csrf_exempt 


# -- Home Page --
# handles both member and guest home page
@csrf_exempt
def home(request):
#    return HttpResponse("You are at the home page.")
    if request.user.is_authenticated():
        return render_to_response('member_home.html',
                              {'profile': request.user.get_profile,
                                'facebook_app_id': settings.FACEBOOK_APP_ID},
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
    secret_userlist = []
    open_userlist=[]
    duplicate_userlist=[]
    is_open=False;
    if 'open' in request.POST:
        is_open=True
    
    for key in request.POST:
        crushee_id=request.POST[key]

        if key.startswith('to'):    
            # find existing site user with this id or create a new user 
            # called function is in a custom UserProfile manager because it is also used during login/authentication
            selected_user=UserProfile.objects.find_or_create_user(fb_id=crushee_id, fb_access_token=request.user.get_profile().access_token, fb_profile=None, is_this_for_me=False)
            # now that the user is definitely on the system, add that user to the crush list        
            # only create a new relationship if an existing one between the current user and the selected user does not exist
            if is_open==True:
                if not(my_profile.open_crushees.filter(username=selected_user.username).exists()):
                    OpenCrushRelationship.objects.create(target_person=selected_user,source_person_profile=my_profile,
                                                           friendship_type=u'FRIEND')
                    open_userlist.append(selected_user)
                else:
                    duplicate_userlist.append(selected_user)
                    
            else:
                if not(my_profile.secret_crushees.filter(username=selected_user.username).exists()):
                    SecretCrushRelationship.objects.create(target_person=selected_user,source_person_profile=my_profile,
                                                           friendship_type=u'FRIEND')
                    secret_userlist.append(selected_user)
                else:
                    duplicate_userlist.append(selected_user)          
     
    return render_to_response('search.html',
                              {'token':csrf.get_token(request),
                               'profile': my_profile, 
                               'facebook_app_id': settings.FACEBOOK_APP_ID, 
                               'redirect_uri': fb_redirect_uri,
                               'secret_userlist':secret_userlist,
                               'open_userlist':open_userlist,
                               'duplicate_userlist':duplicate_userlist},
                              context_instance=RequestContext(request))  

# -- Crush List Page --
@login_required
def crush_list(request):
    my_profile = request.user.get_profile()  
    
    if "delete_secret" in request.GET:
        delete_username=request.GET["delete_secret"]
        # find the relationship and delete it!
        delete_user=my_profile.secret_crushees.get(username=delete_username)
        my_profile.secretcrushrelationship_set.get(target_person=delete_user).delete()
    else:             
        if "delete_open" in request.GET:
            delete_username=request.GET["delete_open"]
            delete_user=my_profile.open_crushees.get(username=delete_username)
            my_profile.opencrushrelationship_set.get(target_person=delete_user).delete()
            
    # build a list of all crush relationship objects to send to the template file
    secret_crush_relationships = []
    open_crush_relationships = []
    for crushee in my_profile.secret_crushees.all():
        secret_crush_relationships.append(SecretCrushRelationship.objects.get(source_person_profile=my_profile,target_person=crushee))
    for crushee in my_profile.open_crushees.all():
        open_crush_relationships.append(OpenCrushRelationship.objects.get(source_person_profile=my_profile,target_person=crushee))        
    
    redirect_uri='http://' + request.get_host()+'/crush_list/'
    
    return render_to_response('crush_list.html',
                              {'profile': my_profile, 'secret_crush_relationships':secret_crush_relationships,
                               'open_crush_relationships':open_crush_relationships,
                               'redirect_uri':redirect_uri,
                               'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request))    

# -- Admirer List Page --
@login_required
def secret_admirer_list(request):
    my_profile = request.user.get_profile() 
    admirers= request.user.secret_crushees_set.all()
    return render_to_response('secret_admirer_list.html',
                              {'profile': my_profile,
                               'admirers':admirers,
                                'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request)) 

# -- Not so Secret Admirer List Page --
@login_required
def open_admirer_list(request):    
    my_profile = request.user.get_profile() 
    admirers= request.user.open_crushees_set.all()
    return render_to_response('open_admirer_list.html',
                              {'profile': my_profile,
                               'admirers':admirers,
                                'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request)) 

# -- Not Interested List Page --
@login_required
def not_interested_list(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('not_interested_list.html',
                              {'profile': facebook_profile,
                               'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request))

# -- Admirer Lineup Page --
@login_required
def admirer_lineup(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('admirer_list.html',
                              {'profile': facebook_profile,
                                'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request))

# -- Invite Friends Page --
@login_required
def invite(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('invite.html',
                              {'profile': facebook_profile,
                                'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request))

# -- My Profile Page --
@login_required
def my_profile(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('my_profile.html',
                              {'profile': facebook_profile,
                                'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request))

# -- My Credits Page --
@login_required
def site_credits(request):
    user_profile = request.user.get_profile()
    notification_message=""
    if 'amount' in request.POST:
        new_credits = int(request.POST['amount'])
        print "added credits: " + str(new_credits)
        if new_credits==0:
            user_profile.site_credits = 0
        else:
            user_profile.site_credits += new_credits
        user_profile.save()
        notification_message = "You added " + str(new_credits) + " credits."
    return render_to_response('site_credits.html',
                              {'profile': user_profile,notification_message:notification_message,
                              'facebook_app_id': settings.FACEBOOK_APP_ID},
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