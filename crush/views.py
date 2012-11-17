from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.conf import settings
from crush.models import UserProfile,CrushRelationship,PlatonicRelationship
from django.middleware import csrf
#from django.contrib.auth.models import Use
# to allow app to run in facebook canvas without csrf error:
from django.views.decorators.csrf import csrf_exempt 


# -- Home Page --
# handles both member and guest home page
@csrf_exempt
def home(request):
    
    if request.user.is_authenticated():
        return HttpResponseRedirect('/crushes_in_progress/')

    else:
        return render(request,'guest_home.html')

# -- Crush Search Page --
@login_required
#(redirect_field_name='/')
def search(request):
    my_profile = request.user.get_profile()
    # fb_redirect_uri is used by facebook request dialog to redirect back
        # create it from scracth so that any get parameters (e.g. previously selected ID's) are removed
    fb_redirect_uri='http://' + request.get_host()+'/search/'
    crushee_id=''
    userlist = []
    duplicate_userlist=[]
    
    for key in request.POST:
        crushee_id=request.POST[key]

        if key.startswith('to'):    
            # find existing site user with this id or create a new user 
            # called function is in a custom UserProfile manager because it is also used during login/authentication
            selected_user=UserProfile.objects.find_or_create_user(fb_id=crushee_id, fb_access_token=request.user.get_profile().access_token, fb_profile=None, is_this_for_me=False)
            # now that the user is definitely on the system, add that user to the crush list        
            # only create a new relationship if an existing one between the current user and the selected user does not exist


            if not(my_profile.crush_targets.filter(username=selected_user.username).exists()):
                CrushRelationship.objects.create(target_person=selected_user,source_person_profile=my_profile,
                                                              target_starting_active_status=selected_user.is_active,
                                                              friendship_type=u'FRIEND')
                userlist.append(selected_user)
            else:
                duplicate_userlist.append(selected_user)          
     
    return render_to_response('search.html',
                              {'token':csrf.get_token(request),
                               'profile': my_profile, 
                               'facebook_app_id': settings.FACEBOOK_APP_ID, 
                               'redirect_uri': fb_redirect_uri,
                               'userlist':userlist,
                               'duplicate_userlist':duplicate_userlist},
                              context_instance=RequestContext(request))  




# -- Crush List Page --
@login_required
def crushes_in_progress(request):
    my_profile = request.user.get_profile() 
    
    # obtain the results of any crush additions or deletions
        # later I can move this into a separate view function
    
    if request.method == "POST":
        crushee_id=''
        userlist = []
        duplicate_userlist=[]
        
        for key in request.POST:
            crushee_id=request.POST[key]
    
            if key.startswith('to'):    
                # find existing site user with this id or create a new user 
                # called function is in a custom UserProfile manager because it is also used during login/authentication
                selected_user=UserProfile.objects.find_or_create_user(fb_id=crushee_id, fb_access_token=request.user.get_profile().access_token, fb_profile=None, is_this_for_me=False)
                # now that the user is definitely on the system, add that user to the crush list        
                # only create a new relationship if an existing one between the current user and the selected user does not exist 
    
                if not(my_profile.crush_targets.filter(username=selected_user.username).exists()):
                    CrushRelationship.objects.create(target_person=selected_user,source_person_profile=my_profile,
                                                               friendship_type=u'FRIEND', updated_flag=True)
                    userlist.append(selected_user)
                else:
                    duplicate_userlist.append(selected_user)
        return HttpResponseRedirect('/crushes_in_progress')
    
    if "delete" in request.GET:
        delete_username=request.GET["delete"]
            # find the relationship and delete it!
        try:
            my_profile.crushrelationship_set.get(target_person__username=delete_username).delete()
        except CrushRelationship.DoesNotExist:
            delete_username=''
        return HttpResponseRedirect('/crushes_in_progress/')
        

    # obtain a query set of all CrushRelationship objects from the user profile where the target's feeling is unknown (0)
        # obtaining CrushRelationship objects backwards and from the user profile generates crush relationships where given user is admirer
        # obtaining CrushRelationship objects backwards from the user object generates crush relationships where given user is admired
        
    responded_relationships = my_profile.crushrelationship_set.filter(target_status__gt = 3).exclude(is_results_paid=True)
    crush_relationships = my_profile.crushrelationship_set

    crush_progressing_relationships = crush_relationships.filter(target_status__lt = 4).order_by('-updated_flag','target_status','target_person__last_name')
    crushes_in_progress_count = crush_relationships.count() + responded_relationships.count()
    crushes_matched_count = crush_relationships.filter(target_status=4).filter(is_results_paid=True).count()
    crushes_not_matched_count = crush_relationships.filter(target_status=5).filter(is_results_paid=True).count()
    
    return render_to_response('crushes.html',
                              {'profile': my_profile, 
                               'crush_type': 0, # 0 is in progress, 1 is matched, 2 is not matched
                               'responded_relationships':responded_relationships,
                               'crush_relationships':crush_progressing_relationships,
                               'facebook_app_id': settings.FACEBOOK_APP_ID,
                               'crushes_in_progress_count': crushes_in_progress_count,
                               'crushes_matched_count': crushes_matched_count,
                               'crushes_not_matched_count': crushes_not_matched_count},
                              context_instance=RequestContext(request))    
    
# -- Crushes Matched Page --
@login_required
def crushes_matched(request):
    my_profile = request.user.get_profile() 
   
    responded_relationships = my_profile.crushrelationship_set.filter(target_status__gt = 3).exclude(is_results_paid=True)
    crush_relationships = my_profile.crushrelationship_set

    crush_matched_relationships = crush_relationships.filter(target_status = 4).filter(is_results_paid=True).order_by('target_person__last_name')
    crushes_matched_count = crush_matched_relationships.count()
    crushes_not_matched_count = crush_relationships.filter(target_status=5).filter(is_results_paid=True).count()
    crushes_in_progress_count = crush_relationships.filter(target_status__lt = 4).count() + responded_relationships.count()
    
    return render_to_response('crushes.html',
                              {'profile': my_profile, 
                               'crush_type': 1, # 0 is in progress, 1 is matched, 2 is not matched
                               'responded_relationships':responded_relationships,
                               'crush_relationships':crush_matched_relationships,
                               'facebook_app_id': settings.FACEBOOK_APP_ID,
                               'crushes_in_progress_count': crushes_in_progress_count,
                               'crushes_matched_count': crushes_matched_count,
                               'crushes_not_matched_count': crushes_not_matched_count},
                              context_instance=RequestContext(request))    

# -- Crushes Not Matched Page --
@login_required
def crushes_not_matched(request):
    my_profile = request.user.get_profile() 
   
    responded_relationships = my_profile.crushrelationship_set.filter(target_status__gt = 3).exclude(is_results_paid=True)
    crush_relationships = my_profile.crushrelationship_set

    crush_not_matched_relationships = crush_relationships.filter(target_status = 5).filter(is_results_paid=True).order_by('target_person__last_name')
    crushes_not_matched_count = crush_not_matched_relationships.count()
    crushes_matched_count = crush_relationships.filter(target_status=4).filter(is_results_paid=True).count()
    crushes_in_progress_count = crush_relationships.filter(target_status__lt = 4).count() + responded_relationships.count()
    
    return render_to_response('crushes.html',
                              {'profile': my_profile, 
                               'crush_type': 2, # 0 is in progress, 1 is matched, 2 is not matched
                               'responded_relationships':responded_relationships,
                               'crush_relationships':crush_not_matched_relationships,
                               'facebook_app_id': settings.FACEBOOK_APP_ID,
                               'crushes_in_progress_count': crushes_in_progress_count,
                               'crushes_matched_count': crushes_matched_count,
                               'crushes_not_matched_count': crushes_not_matched_count},
                              context_instance=RequestContext(request))

# -- Admirer List Page --
@login_required
def admirers(request):
    my_profile = request.user.get_profile() 
    admirers= request.user.secret_crushees_set.all()
    return render_to_response('admirers.html',
                              {'profile': my_profile,
                               'admirers':admirers,
                                'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request)) 

# -- Past Admirers Page --
@login_required
def admirers_past(request):
    my_profile = request.user.get_profile() 
    admirers= request.user.secret_crushees_set.all()
    return render_to_response('admirers_past.html',
                              {'profile': my_profile,
                               'admirers':admirers,
                                'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request)) 

# -- Just Friends Page --
@login_required
def just_friends(request):
    my_profile = request.user.get_profile() 
    
    # only for testing purposes:
    if request.method == "POST":
        crushee_id=''
        userlist = []
        
        for key in request.POST:
            crushee_id=request.POST[key]
    
            if key.startswith('to'):    
                # find existing site user with this id or create a new user 
                # called function is in a custom UserProfile manager because it is also used during login/authentication
                selected_user=UserProfile.objects.find_or_create_user(fb_id=crushee_id, fb_access_token=request.user.get_profile().access_token, fb_profile=None, is_this_for_me=False)
                # now that the user is definitely on the system, add that user to the crush list        
                # only create a new relationship if an existing one between the current user and the selected user does not exist 
    
                if not(my_profile.just_friends_targets.filter(username=selected_user.username).exists()):
                        PlatonicRelationship.objects.create(target_person=selected_user,source_person_profile=my_profile,
                                                               friendship_type=u'FRIEND', updated_flag=True)
                        userlist.append(selected_user)
        return HttpResponseRedirect('/just_friends')
    
    
    # obtain the results of any crush additions or deletions
        # later I can move this into a separate view function
    
    if "delete" in request.GET:
        delete_username=request.GET["delete"]
            # find the relationship and delete it!
        try:
            my_profile.platonicrelationship_set.get(target_person__username=delete_username).delete()
        except PlatonicRelationship.DoesNotExist:
            delete_username=''
        return HttpResponseRedirect('/just_friends')
        

    # obtain a query set of all PlatonicRelationship objects from the user profile 
        # obtaining PlatonicRelationship objects backwards and from the user profile generates Platonic relationships where given user is source
        # obtaining PlatonicRelationship objects backwards from the user object generates platonic relationships where given user is the target

    platonic_relationships = my_profile.platonicrelationship_set.order_by('-updated_flag','target_person__last_name')
    
    return render_to_response('just_friends.html',
                              {'profile': my_profile, 
                               'platonic_relationships':platonic_relationships,
                               'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request))    

# -- Friends with Admirers Page --
@login_required
def friends_with_admirers(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('friends_with_admirers.html',
                              {'profile': facebook_profile,
                               'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request))


# -- Notification settings --
@login_required
def modal_delete_crush(request):
    return HttpResponse("Text only, please.", content_type="text/plain")
    

# -- Profile Settings Page --
@login_required
def settings_profile(request):
    facebook_profile = request.user.get_profile().get_facebook_profile()
    return render_to_response('settings_profile.html',
                              {'profile': facebook_profile,
                                'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request))

# -- Credit Settings Page --
@login_required
def settings_credits(request):
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
    return render_to_response('settings_credits.html',
                              {'profile': user_profile,notification_message:notification_message,
                              'facebook_app_id': settings.FACEBOOK_APP_ID},
                              context_instance=RequestContext(request))

# -- Notification settings --
@login_required
def settings_notifications(request):
    return HttpResponse("You are at the Notification Settings Page.")
    
# -- Logout --
@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/home/")

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