from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.conf import settings
from crush.models import CrushRelationship,PlatonicRelationship,FacebookUser
import urllib, json
import random 
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


# -- Crush List Page --
@login_required
def crushes_in_progress(request):
    
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
                print "trying to get a user for crushee_id=" + crushee_id
                selected_user=FacebookUser.objects.find_or_create_user(fb_id=crushee_id, fb_access_token=request.user.access_token, fb_profile=None, is_this_for_me=False)
                # now that the user is definitely on the system, add that user to the crush list        
                # only create a new relationship if an existing one between the current user and the selected user does not exist 
               
                
                print "successfully got a new crush user with username: " + selected_user.facebook_username
                if not(request.user.crush_targets.filter(username=selected_user.username).exists()):
                    CrushRelationship.objects.create(target_person=selected_user,source_person=request.user,
                                                               friendship_type=u'FRIEND', updated_flag=True)
                    userlist.append(selected_user)
                else:
                    duplicate_userlist.append(selected_user)
        return HttpResponseRedirect('/crushes_in_progress')
    
    if "delete" in request.GET:
        
        delete_username=request.GET["delete"]
        print "attempting to delete: " + delete_username
            # find the relationship and delete it!
        try:
            request.user.crush_relationship_set_from_source.get(target_person__username=delete_username).delete()
        except CrushRelationship.DoesNotExist:
            "can't find crush relationship to delete!"
            delete_username=''
        return HttpResponseRedirect('/crushes_in_progress/')
        

    # obtain a query set of all CrushRelationship objectse where the target's feeling is unknown (0)
        
    crush_relationships = request.user.crush_relationship_set_from_source
    responded_relationships = crush_relationships.filter(target_status__gt = 3).exclude(is_results_paid=True)

    crush_progressing_relationships = crush_relationships.filter(target_status__lt = 4).order_by('-updated_flag','target_status','target_person__last_name')
    crushes_matched_count = crush_relationships.filter(target_status=4).filter(is_results_paid=True).count()
    crushes_not_matched_count = crush_relationships.filter(target_status=5).filter(is_results_paid=True).count()
    
    return render(request,'crushes.html',
                              {
                               'crush_type': 0, # 0 is in progress, 1 is matched, 2 is not matched
                               'responded_relationships':responded_relationships,
                               'crush_relationships':crush_progressing_relationships,
                               'facebook_app_id': settings.FACEBOOK_APP_ID,
                               'crushes_in_progress_count': crush_progressing_relationships.count(),
                               'crushes_matched_count': crushes_matched_count,
                               'crushes_not_matched_count': crushes_not_matched_count
                               })    
    
# -- Crushes Matched Page --
@login_required
def crushes_matched(request):
   
    crush_relationships = request.user.crush_relationship_set_from_source   
    responded_relationships = crush_relationships.filter(target_status__gt = 3).exclude(is_results_paid=True)
    
    crush_matched_relationships = crush_relationships.filter(target_status = 4).filter(is_results_paid=True).order_by('target_person__last_name')
    crushes_matched_count = crush_matched_relationships.count()
    crushes_not_matched_count = crush_relationships.filter(target_status=5).filter(is_results_paid=True).count()
    crushes_in_progress_count = crush_relationships.filter(target_status__lt = 4).count()
    
    return render(request,'crushes.html',
                              {
                               'crush_type': 1, # 0 is in progress, 1 is matched, 2 is not matched
                               'responded_relationships':responded_relationships,
                               'crush_relationships':crush_matched_relationships,
                               'facebook_app_id': settings.FACEBOOK_APP_ID,
                               'crushes_in_progress_count': crushes_in_progress_count,
                               'crushes_matched_count': crushes_matched_count,
                               'crushes_not_matched_count': crushes_not_matched_count
                               })    

# -- Crushes Not Matched Page --
@login_required
def crushes_not_matched(request):
    
    crush_relationships = request.user.crush_relationship_set_from_source
    responded_relationships = crush_relationships.filter(target_status__gt = 3).exclude(is_results_paid=True)

    crush_not_matched_relationships = crush_relationships.filter(target_status = 5).filter(is_results_paid=True).order_by('target_person__last_name')
    crushes_not_matched_count = crush_not_matched_relationships.count()
    crushes_matched_count = crush_relationships.filter(target_status=4).filter(is_results_paid=True).count()
    crushes_in_progress_count = crush_relationships.filter(target_status__lt = 4).count()
    
    return render(request,'crushes.html',
                              {
                               'crush_type': 2, # 0 is in progress, 1 is matched, 2 is not matched
                               'responded_relationships':responded_relationships,
                               'crush_relationships':crush_not_matched_relationships,
                               'facebook_app_id': settings.FACEBOOK_APP_ID,
                               'crushes_in_progress_count': crushes_in_progress_count,
                               'crushes_matched_count': crushes_matched_count,
                               'crushes_not_matched_count': crushes_not_matched_count
                               })

# -- Admirer List Page --
@login_required
def admirers(request):

    me = request.user 
   
    admirer_relationships = me.crush_relationship_set_from_target
    admirer_progressing_relationships = admirer_relationships.filter(date_lineup_finished=None).order_by('target_status','date_added')
    past_admirers_count = admirer_relationships.exclude(date_lineup_finished=None).count()
    
    # initialize the lineups of any new admirer relationships
        # filter out the new relationships whose lineup member 1 is empty
    if admirer_progressing_relationships:
        uninitialized_relationships = admirer_progressing_relationships.exclude(lineupmember__position__gt = 0) #get all relationships that don't have a lineup member at position 0 (non inititialized)
        if (uninitialized_relationships):
            print "found an uninitialized relationship"
            for relationship in uninitialized_relationships:
                initialize_lineup(request,relationship)

    return render(request,'admirers.html',
                              {'profile': me.get_profile, 
                               'admirer_type': 0, # 0 is in progress, 1 completed
                               'admirer_relationships':admirer_progressing_relationships,
                               'facebook_app_id': settings.FACEBOOK_APP_ID,
                               'past_admirers_count': past_admirers_count})    
    
#relationship_id is unique integer id representing the crush relationship, fql_query is the fql query string that the function should use to
def initialize_lineup(request, relationship):
    print "initializing relationship for admirer: " + relationship.source_person.facebook_username
    me = request.user
    # get sex of admirer
    admirer_gender= 'Male' if relationship.source_person.gender == 'M'  else 'Female'
    # get relationship status of admirer
    #admirer_is_single=relationship.source_person_profile.is_single
    
    # build up a list of all the existing users
    
    #fql_query = "SELECT name, birthday FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = me()) AND substr(sex, 0, 1) = 'f' ORDER BY name"
    # list all friends usernames who do not have a family relationship with me and are of a certain gender 
    #fql_query = "SELECT username, relationship_status FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (SELECT uid FROM family where profile_id=me())))) AND sex = 'female' ORDER_BY friend_count"
    # list all friends usernames who do not have a family relationship with me and are of a certain gender and are not
    #fql_query = "SELECT username, relationship_status, friend_count FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (SELECT uid FROM family where profile_id=me())))) AND sex = '" + admirer_gender + "'  AND NOT (relationship_status IN ('Married', 'Engaged', 'In a relationship', 'In a domestic partnership', 'In a civil union'))  ORDER BY friend_count DESC"
    # list all friends usernames who do not have a family relationship with me and are of a certain gender limited to top 30 results
    exclude_facebook_ids = "'" + str(relationship.source_person.username) + "'"
    fql_query = "SELECT uid, relationship_status FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (SELECT uid FROM family where profile_id=me())) AND NOT (uid2 IN (" + exclude_facebook_ids + "))) ) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT 9"
   
    print "fql query to send out: " + fql_query
    
    fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,me.access_token))
    #print fql_query_results.read()
    try:
        print "attempting to load the json results"
        data = json.load(fql_query_results)['data']
       
        if (len(data) == 0):
            if admirer_gender=='Male':
                data = [{u'username':u'zuck', 'uid':u'zuck'}]
            else:
                data = [{u'username':u'sheryl', 'uid':u'sheryl'}]
        print "data: " + str(data)
    except ValueError:
        print "ValueError on Fql Query Fetch read!"
        return False
    # determine where the admirer should randomly fall into the lineup
    admirer_position=random.randint(0, len(data)) # normally len(data) should be 9
    print "admirer_position: " + str(admirer_position)
    index = 0
    rel_id = relationship.id
    for fql_user in data:
        # if the current lineup position is where the admirer should go, then insert the admirer
        if index==admirer_position:
            new_member_id = rel_id + (.1 * index)
            relationship.lineupmember_set.create(position=new_member_id,LineupUser=relationship.source_person)
            print "put crush in position: " + str(new_member_id) + " from index value: " + str(index)
            index = index + 1            
            # create a lineup member with the given username      
        new_member_id = rel_id + (.1 * index)
        lineup_user=FacebookUser.objects.find_or_create_user(fb_id=fql_user['uid'],fb_access_token=request.user.access_token,is_this_for_me=False)
        relationship.lineupmember_set.create(position=new_member_id, LineupUser=lineup_user)
        print "put friend in position: " + str(new_member_id) + " from index value: " + str(index)
        index = index + 1
        
    if len(data)==admirer_position:
        new_member_id = rel_id + (len(data) * .1)
        relationship.lineupmember_set.create(position=new_member_id,LineupUser=relationship.source_person)
        print "put crush in position: " + str(new_member_id)        

#    print "Number of results: " + str((data['data']).__len__())
    
    return True


# -- Past Admirers Page --
@login_required
def admirers_past(request):
    me = request.user 
   
    admirer_relationships = me.crush_relationship_set_from_target
    admirer_completed_relationships = admirer_relationships.exclude(date_lineup_finished=None).order_by('date_added')
    progressing_admirers_count = admirer_relationships.filter(date_lineup_finished=None).count()
    
    return render(request,'admirers.html',
                              {
                               'admirer_type': 1, # 0 is in progress, 1 completed
                               'admirer_relationships':admirer_completed_relationships,
                               'facebook_app_id': settings.FACEBOOK_APP_ID,
                               'progressing_admirers_count': progressing_admirers_count
                               })    

# -- Just Friends Page --
@login_required
def just_friends(request):
    
    # only for testing purposes:
    if request.method == "POST":
        crushee_id=''
        userlist = []
        
        for key in request.POST:
            crushee_id=request.POST[key]
    
            if key.startswith('to'):    
                # find existing site user with this id or create a new user 
                # called function is in a custom UserProfile manager because it is also used during login/authentication
                print "trying to get a platonic friend user for id=" + crushee_id            
                selected_user=FacebookUser.objects.find_or_create_user(fb_id=crushee_id, fb_access_token=request.user.access_token, fb_profile=None, is_this_for_me=False)
                # now that the user is definitely on the system, add that user to the crush list        
                # only create a new relationship if an existing one between the current user and the selected user does not exist 
    
                if not(request.user.just_friends_targets.filter(username=selected_user.username).exists()):
                        PlatonicRelationship.objects.create(target_person=selected_user,source_person=request.user,
                                                               friendship_type=u'FRIEND', updated_flag=True)
                        userlist.append(selected_user)
        return HttpResponseRedirect('/just_friends')

    # obtain the results of any crush additions or deletions
        # later I can move this into a separate view function
    
    if "delete" in request.GET:
        delete_username=request.GET["delete"]
            # find the relationship and delete it!
        try:
            request.user.platonic_relationship_set_from_source.get(target_person__username=delete_username).delete()
        except PlatonicRelationship.DoesNotExist:
            delete_username=''
        return HttpResponseRedirect('/just_friends')

    platonic_relationships = request.user.platonic_relationship_set_from_source.order_by('-updated_flag','target_person__last_name')
    
    return render(request,'just_friends.html',
                              {
                               'platonic_relationships':platonic_relationships,
                               'add_as_platonic_friends':True,
                               'facebook_app_id': settings.FACEBOOK_APP_ID
                               })    

# -- Friends with Admirers Page --
@login_required
def friends_with_admirers(request):

    return render(request,'friends_with_admirers.html',
                              {
                               'facebook_app_id': settings.FACEBOOK_APP_ID}
                  )

# -- Single Lineup (Ajax Content) Page --
@login_required
def lineup(request,admirer_id):
    try:
        admirer_rel = request.user.crush_relationship_set_from_target.get(admirer_display_id=admirer_id)
    except CrushRelationship.DoesNotExist:
        print "could not find an admirer relationship for the lineup"
    lineup_set = admirer_rel.lineupmember_set.all()
    return render(request,'lineup.html',
                              {
                               'admirer_rel':admirer_rel,
                               'lineup_set': lineup_set,
                               'facebook_app_id': settings.FACEBOOK_APP_ID})

@login_required
def ajax_add_as_crush(request,crush_id):
    # called from lineup.html to add a member to either the crush list or the platonic friend list

    print "adding username as crush: " + crush_id
    try:
        target_user=FacebookUser.objects.get(username=crush_id)
        new_relationship = CrushRelationship.objects.create(source_person=request.user, target_person=target_user)
    except FacebookUser.DoesNotExist:
        print "failed to add lineup member as crush: " + crush_id
        return "Server Error: Could not add friend as crush"
    print "successfully added user: " + target_user.first_name + " as a crush"
    ajax_response = "<div id=\"choice\">" + target_user.first_name + " " + target_user.last_name + " was successfully added as your crush on " + str(new_relationship.date_added) + "</div>"
    print "ajax: " + ajax_response
    return HttpResponse(ajax_response)

    

# -- Notification settings --
@login_required
def modal_delete_crush(request):
    return HttpResponse("Text only, please.", content_type="text/plain")
    

# -- Profile Settings Page --
@login_required
def settings_profile(request):

    return render(request,'settings_profile.html',
                              {
                                'facebook_app_id': settings.FACEBOOK_APP_ID})

# -- Credit Settings Page --
@login_required
def settings_credits(request):

    notification_message=""
    if 'amount' in request.POST:
        new_credits = int(request.POST['amount'])
        print "added credits: " + str(new_credits)
        if new_credits==0:
            request.user.site_credits = 0
        else:
            request.user.site_credits += new_credits
        request.user.save()
        notification_message = "You added " + str(new_credits) + " credits."
    return render(request,'settings_credits.html',
                              {notification_message:notification_message,
                              'facebook_app_id': settings.FACEBOOK_APP_ID})

# -- Notification settings --
@login_required
def settings_notifications(request):
    return HttpResponse(request,"You are at the Notification Settings Page.")
    
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