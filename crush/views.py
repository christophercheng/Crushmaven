from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.conf import settings
from crush.models import CrushRelationship,PlatonicRelationship,FacebookUser,LineupMember, Purchase, EmailRecipient, initialize_lineup
import urllib, json
import paypal
from django.views.decorators.http import require_POST
import datetime
from crush.appinviteform import AppInviteForm
from crush.select_crush_by_id_form import SelectCrushIDForm
from crush.notification_settings_form import NotificationSettingsForm
from crush.profile_settings_form import ProfileSettingsForm
from smtplib import SMTPException
from multiprocessing import Pool
from django.http import HttpResponseNotFound
import time



#from django.contrib.auth.models import Use
# to allow app to run in facebook canvas without csrf error:
from django.views.decorators.csrf import csrf_exempt 
# for mail testing 
from django.core.mail import send_mass_mail

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

    
            if key.startswith('to'):    
                crushee_id=request.POST[key][:-1] #handle a hack where last character is the friend type

                friend_type= int(request.POST[key][-1])
                # find existing site user with this id or create a new user 
                # called function is in a custom UserProfile manager because it is also used during login/authentication
                print "trying to get a user for crushee_id=" + crushee_id
                selected_user=FacebookUser.objects.find_or_create_user(fb_id=crushee_id, fb_access_token=request.user.access_token, fb_profile=None, is_this_for_me=False)
                # now that the user is definitely on the system, add that user to the crush list        
                # only create a new relationship if an existing one between the current user and the selected user does not exist 
               
                
                print "successfully got a new crush user with username: " + selected_user.facebook_username
                if not(request.user.crush_targets.filter(username=selected_user.username).exists()):
                    new_crush = CrushRelationship.objects.create(target_person=selected_user,source_person=request.user,
                                                               friendship_type=friend_type, updated_flag=True)
                    
                    if friend_type != 0: # for crushes with non-friends, the lineup must be initialized while the admirer is still logged in
                        pool=Pool()
                        pool.apply_async(initialize_lineup,[new_crush],) #initialize lineup asynchronously
            
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
    crushes_completed_count = crush_relationships.filter(is_results_paid=True).count()
#    crushes_matched_count = crush_relationships.filter(target_status=4).filter(is_results_paid=True).count()
#    crushes_not_matched_count = crush_relationships.filter(target_status=5).filter(is_results_paid=True).count()
    
    return render(request,'crushes.html',
                              {
                               'crush_type': 0, # 0 is in progress, 1 is matched, 2 is not matched
                               'responded_relationships':responded_relationships,
                               'crush_relationships':crush_progressing_relationships,
                               'crushes_in_progress_count': crush_progressing_relationships.count(),
                               'crushes_completed_count':crushes_completed_count
#                               'crushes_matched_count': crushes_matched_count,
#                               'crushes_not_matched_count': crushes_not_matched_count
                               })    

# -- Crushes Completed Page --
@login_required
def crushes_completed(request,reveal_crush_id=None):
    
    crush_relationships = request.user.crush_relationship_set_from_source 
    
    if (( reveal_crush_id) and request.user.site_credits >= settings.FEATURES['2']['COST']):
        try:
            reveal_crush_relationship = crush_relationships.get(target_person__username=reveal_crush_id)
            reveal_crush_relationship.is_results_paid=True
            reveal_crush_relationship.updated_flag=True
            reveal_crush_relationship.save(update_fields=['is_results_paid','updated_flag'])
            request.user.site_credits -=  settings.FEATURES['2']['COST']
            request.user.save(update_fields=['site_credits'])
        except CrushRelationship.DoesNotExist:
            print("Could not find the relationship to reveal or not enough credit")
   
    responded_relationships = crush_relationships.filter(target_status__gt = 3).exclude(is_results_paid=True)
    
#    crush_matched_relationships = crush_relationships.filter(target_status = 4).filter(is_results_paid=True).order_by('target_person__last_name')
#    crushes_matched_count = crush_matched_relationships.count()
#    crushes_not_matched_count = crush_relationships.filter(target_status=5).filter(is_results_paid=True).count()
    crushes_completed_relationships = crush_relationships.filter(is_results_paid=True).order_by('target_person__last_name')
    crushes_in_progress_count = crush_relationships.filter(target_status__lt = 4).count()
    
    return render(request,'crushes.html',
                              {
                               'crush_type': 1, # 0 is in progress, 1 is matched, 2 is not matched
                               'responded_relationships':responded_relationships,
                               'crush_relationships':crushes_completed_relationships,
                               'crushes_in_progress_count': crushes_in_progress_count,
                               'crushes_completed_count' : crushes_completed_relationships.count
#                               'crushes_matched_count': crushes_matched_count,
#                               'crushes_not_matched_count': crushes_not_matched_count
                               })   

@login_required    
def app_invite_form(request, crush_username):
    print "APP INVITE FORM!"
    # crush_name should be first name last name
    if request.method == 'POST': # if the form has been submitted...
        print "METHOD IS POST"
        form = AppInviteForm(request.POST)
        if form.is_valid():
            # send out the emails here
            crush_email_list=form.cleaned_data['crush_emails']
            friend_email_list=form.cleaned_data['mutual_friend_emails']
            try:
                crush_user = FacebookUser.objects.get(username=crush_username)
            except FacebookUser.DoesNotExist:
                return render(request,"error.html",{ 'error': "App Invite Send encountered an unusual error.  Plese try again later." })
            
            crush_name = crush_user.first_name + " " + crush_user.last_name
            crush_subject = 'Your Facebook friend is attracted to you - find out who.'
            crush_body='Visit http://crushvibes.com to find out whom.'
            friend_subject = 'Your friend ' + crush_name + ' has a secret admirer and needs your help.'
            friend_body='Please forward this message to your friend, ' + crush_name + ':\n\n' + crush_body

            message_list = []
            for email in crush_email_list:
                message_list.append((crush_subject, crush_body, 'info@crushvibes.com',[email]))
            for email in friend_email_list:
                message_list.append((friend_subject, friend_body, 'info@crushvibes.com',[email]))
            print str(message_list)
            try:
                send_mass_mail(message_list,fail_silently=False)
                try: 
                    crush_relationship = request.user.crush_relationship_set_from_source.get(target_person=crush_user)
                    crush_relationship.date_invite_last_sent=datetime.datetime.now()
                    crush_relationship.target_status = 1
                    crush_relationship.save(update_fields=['date_invite_last_sent','target_status'])
                    for email in crush_email_list:
                        EmailRecipient.objects.create(crush_relationship=crush_relationship,recipient_address=email,date_sent=datetime.datetime.now(),is_email_crush=True)
                        
                    for email in friend_email_list:
                        EmailRecipient.objects.create(crush_relationship=crush_relationship,recipient_address=email,date_sent=datetime.datetime.now(),is_email_crush=False)                    
                except CrushRelationship.DoesNotExist:
                    pass #the database won't store app invite history, but that's ok as long as the actual emails were successfully sent
            except SMTPException:
                return render(request,"error.html",{ 'error': "App Invite Send encountered an unusual error.  Plese try again later." })
            if request.is_ajax():
                print "success and returning rendered template"
                return render(request,'app_invite_success.html',{'crush_email_list':crush_email_list,
                                                                 'friend_email_list':friend_email_list})
            else:
                print "success and redirecting"                
                return redirect('app_invite_success')
    else:
        # find mutual friends to pass to the app invite form
        friend_profile = urllib.urlopen('https://graph.facebook.com/' + request.user.username + '/mutualfriends/' + crush_username + '/?access_token=%s' % request.user.access_token)
        friend_profile = json.load(friend_profile)
        friendlist_string=''
        if len(friend_profile['data'])>0:
            for friend in friend_profile['data']:
                friendlist_string+=friend['name'] + ', '
            friendlist_string=friendlist_string[:-2] # strip out last comma 
        print "friendlist_string: " + friendlist_string
        form=AppInviteForm(friendlist_string=friendlist_string)
        print "instantiated form instance"
    return render(request, 'app_invite_form.html',{'form':form,'crush_username':crush_username})

@login_required
def ajax_find_fb_user(request):
    response_data = dict()
    try:
        username=''
        username=request.REQUEST['username']
        me=request.user 
        access_token = me.access_token
        print "accessing user: " + username
        # call fb api to get user info and put it in the cleaned_data function
        fb_profile = urllib.urlopen('https://graph.facebook.com/' + username + '/?access_token=%s' % access_token)
        fb_profile = json.load(fb_profile)
        print "resulant profile: " + str(fb_profile)   

        #raises KeyError if no id key/value pair exists in the fb_profile dictionary
        crush_id = fb_profile['id']
        if crush_id==me.username:
            response_data['error_message']='Invalid user: you cannot add yourself'
            return HttpResponse(json.dumps(response_data), mimetype="application/json")
        try:
            me.crush_targets.get(username=fb_profile['id'])
            response_data['error_message'] = 'You already added ' + fb_profile['name'] + ' as a crush.'
        except FacebookUser.DoesNotExist:
            friend_profile = urllib.urlopen('https://graph.facebook.com/' + me.username + '/friends/' + crush_id + '/?access_token=%s' % access_token)
            friend_profile = json.load(friend_profile)
            if len(friend_profile['data'])>0:
                friend_type=0
            else:
                friend_profile = urllib.urlopen('https://graph.facebook.com/' + me.username + '/mutualfriends/' + crush_id + '/?access_token=%s' % access_token)
                friend_profile = json.load(friend_profile)
                if len(friend_profile['data'])>0:
                    friend_type=1
                else:
                    friend_type=2
            response_data['id']=fb_profile['id']
            response_data['name']=fb_profile['name']
            response_data['friend_type']=friend_type
    except KeyError: # username not found on fb
        response_data['error_message'] = 'Invalid facebook username: ' + username     
    return HttpResponse(json.dumps(response_data), mimetype="application/json")
 

# -- Admirer List Page --
@login_required
def admirers(request):

    me = request.user 

    # get list of responded (so we can filter them out the admirers )
    progressing_crush_list = me.crush_targets.filter(crush_relationship_set_from_target__target_status__gt = 3,crush_relationship_set_from_target__is_results_paid=False)   
    
    # build a list of incomplete admirer relationship by filtering them in the following order:
    #     filter through only those admirer relationships who have not finished their lineup (progressing relationships)
    #     filter out those progressing relationships who are also progressing crushes AND who have not yet instantiated a lineup
    #        if they are also a progressing crush, but a lineup has already been created, then don't filter them out
    admirer_relationships = me.crush_relationship_set_from_target
    progressing_admirer_relationships = admirer_relationships.filter(date_lineup_finished=None).exclude(source_person__in = progressing_crush_list,is_lineup_initialized=False).order_by('target_status','date_added') # valid progressing relationships 

    past_admirers_count = admirer_relationships.exclude(date_lineup_finished=None).count()
    
    # initialize the lineups of any new admirer relationships
        # filter out the new relationships whose lineup member 1 is empty
    
    uninitialized_relationships = progressing_admirer_relationships.filter(is_lineup_initialized = False) #get all relationships that don't already have a lineup (number of lineump members is zero)
    if (uninitialized_relationships):
        print "hey, found an uninitialized relationship"
        pool=Pool(processes=len(uninitialized_relationships))
        for relationship in uninitialized_relationships:
            pool.apply_async(initialize_lineup,[relationship],) #initialize lineup asynchronously
 

    return render(request,'admirers.html',
                              {'profile': me.get_profile, 
                               'admirer_type': 0, # 0 is in progress, 1 completed
                               'admirer_relationships':progressing_admirer_relationships,
                               'past_admirers_count': past_admirers_count})    

# -- Single Lineup (Ajax Content) Page --
@login_required
def lineup(request,admirer_id):
    me = request.user
    try:
        admirer_rel = me.crush_relationship_set_from_target.get(admirer_display_id=admirer_id)
    except CrushRelationship.DoesNotExist:
        return HttpResponse("Error: Could not find an admirer relationship for the lineup.")
    # detract credit if lineup not already paid for
    if (not admirer_rel.is_lineup_paid):
        if (me.site_credits >= settings.FEATURES['1']['COST']):
            me.site_credits -= int(settings.FEATURES['1']['COST'])
            me.save(update_fields=['site_credits']) 
            admirer_rel.is_lineup_paid=True
            admirer_rel.target_status=3
            admirer_rel.updated_flag=True
            admirer_rel.save(update_fields=['is_lineup_paid','target_status','updated_flag'])
        else:
            return HttpResponse("Error: not enough credits to see lineup")
    lineup_set = admirer_rel.lineupmember_set.all()
    # need to cleanse the lineup members each time the lineup is run 
    #    reason: while lineup is not complete, user may have added one of the lineup member as either a crush or a platonic frined
        
    return render(request,'lineup.html',
                              {
                               'admirer_rel':admirer_rel,
                               'lineup_set': lineup_set})

@login_required
def ajax_add_lineup_member(request,add_type,admirer_display_id,facebook_id):
    print "adding member to a list"
    # called from lineup.html to add a member to either the crush list or the platonic friend list
    try:
        target_user=FacebookUser.objects.get(username=facebook_id)
        try:
            admirer_rel=request.user.crush_relationship_set_from_target.get(admirer_display_id=admirer_display_id)
        except CrushRelationship.DoesNotExist:
            return HttpResponse("Server Error: Could not add given lineup user")
        try:
            member=target_user.lineupmember_set.get(LineupUser=target_user,LineupRelationship=admirer_rel)

        except LineupMember.DoesNotExist:
            print "could not find lineup member"
            return HttpResponse("Server Error: Could not add given lineup user")
        if add_type=='crush':
            new_relationship = CrushRelationship.objects.create(source_person=request.user, target_person=target_user)
            ajax_response = "<div id=\"choice\">" + target_user.first_name + " " + target_user.last_name + " was successfully added as a crush on " + str(new_relationship.date_added) + "</div>"
            member.decision=True
        else:
            new_relationship = PlatonicRelationship.objects.create(source_person=request.user, target_person=target_user)
            ajax_response = "<div id=\"choice\">" + target_user.first_name + " " + target_user.last_name + " was successfully added as just-a-friend on " + str(new_relationship.date_added) + "</div>"
            member.decision=False
        member.save(update_fields=['decision'])
        #admirer_rel.number_unrated_lineup_members=F('number_unrated_lineup_members') - 1
        admirer_rel.number_unrated_lineup_members -= 1
        if admirer_rel.number_unrated_lineup_members == 0:
                admirer_rel.date_lineup_finished= datetime.datetime.now()
        admirer_rel.save(update_fields=['date_lineup_finished', 'number_unrated_lineup_members'])
    except FacebookUser.DoesNotExist:
        print "failed to add lineup member: " + facebook_id
        return HttpResponse("Server Error: Could not add given lineup user")  
    return HttpResponse(ajax_response)

@login_required
def ajax_are_lineups_initialized(request):
    print "call to ajax_are_lineups_initialized"
    counter = 0
    while True:
        admirer_rels=request.user.crush_relationship_set_from_target.filter(is_lineup_initialized=False)
        if len(admirer_rels)==0:
            return HttpResponse()
        elif counter==10: 
            # wait up to 5 seconds total before returning control back to client side
            return HttpResponseNotFound()
        else:
            time.sleep(.5)
            counter+=1
            # wait a half second before checking again
            
@login_required
def ajax_display_lineup(request, display_id):
    int_display_id=int(display_id)
    print "ajax initialize lineup with display id: " + str(int_display_id)
    ajax_response = ""
    try:    
        admirer_rel=request.user.crush_relationship_set_from_target.get(admirer_display_id=int_display_id)
 
        if admirer_rel.is_lineup_initialized == False:
            return HttpResponseNotFound(str(display_id),content_type="text/plain")
            #raise Http404 # don't do anything until the initialization is done
 

        for counter, member in enumerate(admirer_rel.lineupmember_set.all()):
            if counter < 2 or member.decision!=None:
                ajax_response +=  '<img src="http://graph.facebook.com/' + member.LineupUser.username + '/picture" height=40 width=40>'
            else:
                ajax_response += '<img src = "http://a3.twimg.com/profile_images/1649076583/facebook-profile-picture-no-pic-avatar_reasonably_small.jpg" height =40 width = 40>'

        ajax_response += '<BR>'
        
        if admirer_rel.is_lineup_paid:
            if admirer_rel.date_lineup_finished:
                ajax_response += 'Line-up completed ' + str(admirer_rel.date_lineup_finished)
                ajax_response += '<a href="/lineup/' + display_id + '/"><BR>View Completed Lineup</a>'
            else:
                ajax_response += '<a href="/lineup/' + display_id + '/">Finish Lineup</a>'
      
        else:
            ajax_response += '<a class="check_credit" href="#" feature_id="1" cancel_url="' + request.build_absolute_uri() + '" success_path="/lineup/' + display_id + '">Start Lineup</a>'
    except CrushRelationship.DoesNotExist:
        print "could not find admirer relationship"
        ajax_response="Sorry, there is a problem processing the lineup for this admirer.  We are working on fixing this issue."

    
    return HttpResponse(ajax_response)
    
@login_required
def ajax_reconsider(request):

    rel_id = request.POST['rel_id']
    
    try:
        rel=request.user.platonic_relationship_set_from_source.get(id=rel_id)
        rel_target_person=rel.target_person
        try:
            request.user.get_all_crush_relations().get(target_person__username=rel_target_person.username)         
            # for some reason crush relationship already exists, but kill this platonic relationship anyway before leaving
            rel.delete()
            return HttpResponse("success") # crush relationship already exists for this person so don't do anything mo
        except CrushRelationship.DoesNotExist:
            # create a new crushrelationship
            new_crush=CrushRelationship.objects.create(target_person=rel_target_person,source_person=request.user,friendship_type=rel.friendship_type,updated_flag=True)
           
            if rel.friendship_type != 0: # for crushes with non-friends, the lineup must be initialized while the admirer is still logged in
               pool=Pool()
               pool.apply_async(initialize_lineup,[new_crush],) #initialize lineup asynchronously
               rel.delete()
    except PlatonicRelationship.DoesNotExist:
        return HttpResponseNotFound("can't find the original platonic relationship") #can't find original platonic relationships so don't do anything more
    
    return HttpResponse("success")


@login_required
def ajax_update_num_platonic_friends(request):

    ajax_response = str(request.user.just_friends_targets.all().count())
    return HttpResponse(ajax_response)
@login_required
def ajax_update_num_crushes_in_progress(request):
    ajax_response = str(request.user.crush_targets.all().count())
    return HttpResponse(ajax_response)

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
                                                               friendship_type=0, updated_flag=True)
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
                               'add_as_platonic_friends':True
                               })    

# -- Friends with Admirers Page --
@login_required
def friends_with_admirers(request):

    return render(request,'friends_with_admirers.html',
                              {}
                  )

# -- Friends with Admirers Section (Ajax Content) --
@login_required
def friends_with_admirers_section(request):
    print " called friends-with-admirers-section"
    ajax_response=""
    me=request.user

    me.find_inactive_friends_of_activated_user()
    for counter,inactive_crush_friend in enumerate(me.friends_with_admirers.all()):
        print "creating html for: " + inactive_crush_friend.username
        ajax_response+="<div id='friend_admirer" + str(counter) + "'>"
        ajax_response +="<img src='" + inactive_crush_friend.get_facebook_picture() + "' width=20 height=20><small>" + inactive_crush_friend.first_name + "&nbsp;&nbsp;" + inactive_crush_friend.last_name
        num_admirers = len(inactive_crush_friend.get_all_admirer_relations())
        ajax_response += "<br>" + str(num_admirers) + " secret admirer"
        if num_admirers > 1:
            ajax_response += "s"
        elapsed_days = (datetime.datetime.now() - inactive_crush_friend.get_all_admirer_relations()[num_admirers-1].date_added).days
        if elapsed_days==0:
            elapsed_days = "today"
        elif elapsed_days == 1:
            elapsed_days = "yesterday"
        elif elapsed_days > 60:
            elapsed_days = str(elapsed_days/30) + " months ago"
        elif elapsed_days > 30:
            elapsed_days = "1 month ago"
        else:
            elapsed_days = str(elapsed_days) + " days ago"
            
        ajax_response += " (" + elapsed_days + ")"
        ajax_response +='<br><span class="app_invite_link"><a class="app_invite" crush_username="' + inactive_crush_friend.username + '" href="#">help them sign up</a>'
        ajax_response+="</small></span></div>"
    if ajax_response=="":
        ajax_response="You have no friends with admirers."
    return HttpResponse(ajax_response)

# -- Temporary content for select crush by id --
@login_required
def select_crush_by_id(request):
    # contains form which accepts as input a facebook uid
    # validates the uid 
        # cannot be a previously crushed ID
        # fetch it via facebook graph api
    # if successful fetch, then display the contents, else display error message
    
    print "SELECT CRUSH BY ID FORM!"
    # crush_name should be first name last name
    if request.method == 'POST': # if the form has been submitted...
        print "METHOD IS POST"
        form = SelectCrushIDForm(request.POST,request=request)

        if form.is_valid():
            # the work to find/create the user and add the was moved to the overriden form clean function for efficiency sake
                # since it has to make a call to facebook graph api to validate username already
            return redirect('/crushes_in_progress')
    else:
        form=SelectCrushIDForm(request=request)
    return render(request, 'select_crush_by_id_form.html',{'form':form})
    
# -- Notification settings --
@login_required
def modal_delete_crush(request):
    return HttpResponse("Text only, please.", content_type="text/plain")
    

# -- Profile Settings Page --
@login_required
def settings_profile(request):
    print "Settings Profile Form!"
    # crush_name should be first name last name
    if request.method == 'POST': # if the form has been submitted...
        print "METHOD IS POST"
        data=request.POST
        if 'cancel' in data:
            return redirect('/settings_profile/')
        else:
            form = ProfileSettingsForm(request.POST)
            if form.is_valid():
                me=request.user
                for element in data:
                    print "element: " + str(element) + " value: " + str(data[element])
                updated_fields=[]
                if 'gender' in data: 
                    me.gender=data['gender']
                    updated_fields.append('gender')                    
                if 'gender_pref' in data: 
                    me.gender_pref=data['gender_pref']
                    updated_fields.append('gender_pref')
                me.is_single=data.get('is_single',False)
                updated_fields.append('is_single')
                if 'birthday_year' in data and data['birthday_year']:
                    me.birthday_year=data['birthday_year']
                    updated_fields.append('birthday_year')
                if 'age_pref_min' in data and data['age_pref_min']: 
                    me.age_pref_min=data['age_pref_min']
                    updated_fields.append('age_pref_min')
                if 'age_pref_max' in data and data['age_pref_max']:
                    me.age_pref_max=data['age_pref_max']
                    updated_fields.append('age_pref_max')
                me.save(update_fields=updated_fields)
                #return redirect('/settings_profile/')
                return render(request,'settings_profile.html',
                              { 'form': form,'updated':True})
    else:
        print "instantiating profile form"
        form=ProfileSettingsForm(instance=request.user)
    return render(request,'settings_profile.html',
                              { 'form': form})
    
# -- Notification settings --
@login_required
def settings_notifications(request):

    print "Settings Notification Form!"
    # crush_name should be first name last name
    if request.method == 'POST': # if the form has been submitted...
        print "METHOD IS POST"
        data=request.POST
        if 'cancel' in data:
            return redirect('/settings_notifications/')
        else:
            form = NotificationSettingsForm(request.POST)
            if form.is_valid():
                for element in request.POST:
                    print str(element) + " value: " + str(request.POST[element])
                request.user.email=data['email']
                settings=request.user.notification_settings
                settings.bNotify_crush_signed_up=data.get('bNotify_crush_signed_up',False)
                settings.bNotify_crush_signed_up=data.get('bNotify_crush_signed_up',False)
                settings.bNotify_crush_signup_reminder = data.get('bNotify_crush_signup_reminder',False)
                settings.bNotify_crush_started_lineup=data.get('bNotify_crush_started_lineup',False)
                settings.bNotify_crush_responded=data.get('bNotify_crush_responded',False)  
                settings.bNotify_new_admirer=data.get('bNotify_new_admirer',False)
                request.user.save(update_fields=['email'])
                settings.save()                               
                return render(request,'settings_notifications.html',
                              { 'form': form,'updated':True})
    else:
        print "instantiating notifications form"
        form=NotificationSettingsForm(instance=request.user.notification_settings, initial={'email':request.user.email})
    return render(request,'settings_notifications.html',
                              { 'form': form})

# -- Credit Checker Page - acts as boarding gate before allowing premium feature access --
@login_required
def credit_checker(request,feature_id):
    # obtain feature data from feature_id and settings
    features_data=settings.FEATURES[feature_id]
    feature_cost = features_data['COST']
    feature_name = features_data['NAME']
                        
    # obtain total credits
    credit_available = request.user.site_credits
    credit_remaining = credit_available - feature_cost
    
    success_path = request.GET.get('success_path',"home")
    print "success_path: " + success_path
    cancel_url = request.GET.get('cancel_url',"home")
    print "cancel_url: " + cancel_url
    paypal_success_url = settings.PAYPAL_RETURN_URL + "/?success_path=" + success_path
    paypal_notify_url = settings.PAYPAL_NOTIFY_URL + request.user.username + "/"
    
    # perform conditional logic to determine which dialog to display
    
    if (credit_available < feature_cost):
        return render(request,'dialog_credit_insufficient.html',
                      {
                       'feature_cost':feature_cost,
                       'feature_name':feature_name,
                       'credit_available':credit_available,
                       'paypal_url': settings.PAYPAL_URL, 
                       'paypal_email': settings.PAYPAL_EMAIL, 
                       'paypal_success_url': paypal_success_url,
                       'paypal_cancel_url': cancel_url,
                       'paypal_notify_url':paypal_notify_url})
    else:
        return render(request,'dialog_credit_sufficient.html',
                      {'feature_cost':feature_cost,
                       'feature_name':feature_name,
                       'credit_available':credit_available,
                       'credit_remaining': credit_remaining,
                       'success_path':success_path})
@login_required    
@csrf_exempt # this is needed so that paypal success redirect from payment page works 
def paypal_purchase(request):

    method_dict=request.GET
    success_path = method_dict.get('success_path',"home")
    credit_amount = method_dict.get('credit_amount', 10)
    price=method_dict.get('amt',9)
    print "printing out pdt get variables:"
    for element in method_dict:
        print "element: " + element + " -> " + method_dict[element]
#    resource = get_object_or_404( models.Resource, pk=id )
#    user = get_object_or_404( User, pk=uid )
    if request.REQUEST.has_key('tx'):
        tx = request.REQUEST['tx']
        try:
            Purchase.objects.get( tx=tx )
            print "duplicate transaction found when processing PAYPAL PDT Handler"
            return HttpResponseRedirect(success_path)
        except Purchase.DoesNotExist:
            print "processing pdt transaction"
            result = paypal.Verify(tx)
            if result.success(): # valid
                Purchase.objects.create(purchaser=request.user, tx=tx, credit_total=int(credit_amount),price= price)
                print "just created a new purchase"
                return HttpResponseRedirect(success_path)
            else: # didn't validate
                return render(request, 'error.html', { 'error': "Failed to validate payment" } )
    else: # no tx
        return render(request, 'error.html', { 'error': "No transaction specified" } )

@require_POST
@csrf_exempt
def paypal_ipn_listener(request,username,credit_amount):
    print "  I P N    L I S T N E R    C A L L E D !!!!"
    print "username: " + username
    print "credit amount: " + str(credit_amount)
    method_dict=request.POST
    price=method_dict.get('payment_gross',9)
        
    if request.REQUEST.has_key('txn_id'):
        txn_id = request.REQUEST['txn_id']
        try:
            facebook_user = FacebookUser.objects.get(username=username)
            print "facebook user found with first name: " + facebook_user.first_name
            
        except FacebookUser.DoesNotExist:
            # evetually Log and error tell PAYPAL that something went wrong and step sending ipn messages
            pass
        try:
            Purchase.objects.get( tx=txn_id )
            print "existing purchase found. transaction id: " + txn_id
            pass
        except Purchase.DoesNotExist:
            print "verify paypal IPN"
            result = paypal.Verify_IPN(method_dict)
            print "paypal IPN verified"
            if result.success(): # valid
                Purchase.objects.create(purchaser=facebook_user, tx=txn_id, credit_total=int(credit_amount),price=price)   
                print "payment made with credit_amount: " + str(credit_amount) + " price: " + str(price)
            else:
                print "paypal IPN was a failure"
    return HttpResponse("OKAY")

# -- Credit Settings Page --
@login_required
def settings_credits(request):

    if 'amount' in request.POST:
        new_credits = int(request.POST['amount'])
        if new_credits==0:
            request.user.site_credits = 0
            request.user.save(update_fields=['site_credits'])
                          
    # obtain total credits
    credit_available = request.user.site_credits
    
    success_path = '/settings_credits'
    cancel_url = 'http://' + request.get_host() + success_path
    
    paypal_success_url = settings.PAYPAL_RETURN_URL + "/?success_path=" + success_path
    paypal_notify_url = settings.PAYPAL_NOTIFY_URL + request.user.username + "/"
    
    return render(request,'settings_credits.html',
                      {'credit_available':credit_available,
                       'paypal_url': settings.PAYPAL_URL, 
                       'paypal_email': settings.PAYPAL_EMAIL, 
                       'paypal_success_url': paypal_success_url,
                       'paypal_cancel_url': cancel_url,
                       'paypal_notify_url':paypal_notify_url})
    
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