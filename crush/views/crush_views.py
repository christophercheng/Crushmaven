from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from crush.models import CrushRelationship,PlatonicRelationship,FacebookUser,InviteEmail,LineupMember
import json
import datetime
from crush.appinviteform import AppInviteForm
import time
from  django.http import HttpResponseNotFound,HttpResponseForbidden
from utils import graph_api_fetch
from urllib2 import URLError,HTTPError
import thread
from smtplib import SMTPException
# for initialization routine
from crush.models.globals import g_init_dict

# called by crush selector upson submit button press
@login_required
def ajax_add_crush_targets(request):
    global g_init_dict
    post_data = request.POST
    # this is just for testing, remove later
    counter=0
    for key in post_data:
        if key=="csrfmiddlewaretoken":
            continue
        counter+=1
        crushee_id=request.POST[key][:-1] #handle a hack where last character is the friend type   
        friend_type= int(request.POST[key][-1])
        # find existing site user with this id or create a new user 
        selected_user=FacebookUser.objects.find_or_create_user(fb_id=crushee_id, fb_access_token=request.user.access_token, fb_profile=None, is_this_for_me=False)
        # now that the user is definitely on the system, add that user to the crush list        
        # only create a new relationship if an existing one between the current user and the selected user does not exist 
        print "successfully got a new crush user with username: " + selected_user.facebook_username
        if not(request.user.crush_targets.filter(username=selected_user.username).exists()):
            relationship=CrushRelationship.objects.create(target_person=selected_user,source_person=request.user,
                                                       friendship_type=friend_type, updated_flag=True)
            # kick off the initialization process if the crush is a non-friend
            if friend_type==2:
                target_username=selected_user.username
                if not target_username in g_init_dict:
                    g_init_dict[target_username]={}
                if not 'initialization_count' in g_init_dict[target_username]:    
                    g_init_dict[target_username]['initialization_count'] = 1
                else:
                    g_init_dict[target_username]['initialization_count'] += 1
                relationship.lineup_initialization_status=0
                relationship.save(update_fields=['lineup_initialization_status'])
                thread.start_new_thread(LineupMember.objects.initialize_lineup,(relationship,))
    
    if counter > 0:
        return HttpResponse()
    else:
        return HttpResponseNotFound()
    
@login_required
def ajax_admin_delete_crush_target(request,crush_username):
    #if (not request.user.is_superuser) or (not request.user.is_staff):
        #if request.user.username=="1057460663" or request.user.username=="651900292" or request.user.username=="100004192844461":
        #    pass
        #else:
        #    return HttpResponseForbidden()        try:
        relationship = CrushRelationship.objects.all_crushes(request.user).get(target_person__username=crush_username)
        
        relationship.delete()
        return HttpResponse()
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound()

@login_required
def ajax_can_crush_target_be_platonic_friend(request,crush_username):
    try:
        crush_relationship = CrushRelationship.objects.all_crushes(request.user).get(target_person__username=crush_username)
        time_since_add = datetime.datetime.now() - crush_relationship.date_added
        if time_since_add.days < settings.MINIMUM_DELETION_DAYS_SINCE_ADD:
            return HttpResponseForbidden(settings.DELETION_ERROR[0])
        if crush_relationship.target_status == 3:
            return HttpResponseForbidden(settings.DELETION_ERROR[1])
        if crush_relationship.target_status > 3:
            if crush_relationship.date_target_responded > datetime.datetime.now():
                return HttpResponseForbidden(settings.DELETION_ERROR[1])
            elif crush_relationship.is_results_paid == False:
                return HttpResponseForbidden(settings.DELETION_ERROR[2])
        if crush_relationship.is_results_paid == True:
            time_since_target_responded = datetime.datetime.now() - crush_relationship.date_target_responded;
            if time_since_target_responded.days < settings.MINIMUM_DELETION_DAYS_SINCE_RESPONSE:
                return HttpResponseForbidden(settings.DELETION_ERROR[3])
        return HttpResponse() # everything passes
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound("Error: crush can no longer be found.") # same thing as a successful deletion i guess?

# user is no longer interested in crush and will move them to a platonic friend
# crush must pass all of the conditions before it can be removed
@login_required
def ajax_make_crush_target_platonic_friend(request,crush_username):   
    conditional_response = ajax_can_crush_target_be_platonic_friend(request,crush_username)
    if conditional_response.status_code != 200:
        return HttpResponseForbidden(conditional_response.content)
        # all checks have passed, go ahead and 'make' this relationship a platonic one
    try:
        crush_relationship = CrushRelationship.objects.all_crushes(request.user).get(target_person__username=crush_username)
        target_person = crush_relationship.target_person
        crush_relationship.delete()
        PlatonicRelationship.objects.create(source_person=request.user,target_person=target_person)
        return HttpResponse()
    except CrushRelationship.DoesNotExist:
        return HttpResponse() # same thing as a successful deletion i guess?
    
# -- Crush List Page --
@login_required
def attractions(request,reveal_crush_id=None):
    
    me = request.user
  
    crush_progressing_relationships = CrushRelationship.objects.progressing_crushes(me).order_by('-updated_flag','target_status','target_person__last_name')

    # if there is at least one friend attraction, then we need to check the user's facebook privacy setting.  if their app visibility is not set to "only me", then display warning dialog
    if (len(crush_progressing_relationships.filter(friendship_type=0))>0):
        check_fb_privacy=True
    else:
        check_fb_privacy=False
    
    if reveal_crush_id:
        try:
            reveal_crush_relationship = CrushRelationship.objects.completed_crushes(me).get(target_person__username=reveal_crush_id)
        except CrushRelationship.DoesNotExist:
            reveal_crush_id=None
            
    responded_relationships = CrushRelationship.objects.visible_responded_crushes(me)
    crushes_completed_count = CrushRelationship.objects.completed_crushes(me).count()

    return render(request,'crushes.html',
                              {
                               'crush_type': 0, # 0 is in progress, 1 is matched, 2 is not matched
                               'responded_relationships':responded_relationships,
                               'crush_relationships':crush_progressing_relationships,
                               'crushes_in_progress_count': crush_progressing_relationships.count(),
                               'crushes_completed_count':crushes_completed_count,
                               'lineup_status_choice_4':settings.LINEUP_STATUS_CHOICES[4],
                               'lineup_status_choice_5':settings.LINEUP_STATUS_CHOICES[5],
                               'check_fb_privacy_setting':check_fb_privacy,
                               'reveal_crush_id':reveal_crush_id,
                               })    
@login_required
def ajax_load_response_dialog_content(request,crush_id):
    # grab completed (paid) relationship from crush username
    try:
        relationship=CrushRelationship.objects.completed_crushes(request.user).get(target_person__username=crush_id)
        crush=relationship.target_person
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound("Error: Could not find a matching crush relationship.")
    ajax_response=''
    # show the results of a responded attraction & show either congratulatory or sympathetic messaging
        # show messaging on what to do next
        # provide link for any next step action items
    if relationship.target_status == 4:
        ajax_response += "Congratulations! " 
        ajax_response += crush.get_name() + " is mutually attracted to you.<BR><BR>"
        ajax_response +=  "<a href='#' id='send_fb_message' crush_id='" + crush_id + "'>Send " + crush.first_name + " a message</a>"
    else:
        ajax_response += "We're Sorry, " + crush.get_name() + " is not mutually attracted to you.<BR><BR>"
        ajax_response += "They did however rate your level of attractiveness:<BR><BR>"
        
        if relationship.is_platonic_rating_paid:
            rating = str(relationship.target_platonic_rating)
            ajax_response += rating + " out of 5<BR>(" + settings.PLATONIC_RATINGS[rating] + ") "
        else:
            ajax_response += "<div id='view_rating'><a href='#' unique_id='" + crush_id + "'>View Rating</a></div>"
    
    return HttpResponse(ajax_response)

@login_required
def ajax_get_platonic_rating(request,crush_id):

    try: 
        platonic_rating=None
        platonic_relationship = (request.user.platonic_relationship_set_from_target).get(source_person__username=crush_id)
        platonic_rating = platonic_relationship.rating
        crush_relationship=CrushRelationship.objects.completed_crushes(request.user).get(target_person__username=crush_id)
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound(settings.AJAX_ERROR)
    except Exception as e:
        print str(e)
        pass
    except PlatonicRelationship.DoesNotExist:
        return HttpResponseNotFound(settings.AJAX_ERROR)
    if crush_relationship.is_platonic_rating_paid:
        return HttpResponse(str(platonic_rating))
    else:
        return HttpResponseForbidden("Error: You have not paid to see your attraction rating.");

# -- Crushes Completed Page --
@login_required
def crushes_completed(request,reveal_crush_id=None):
    me = request.user
    crush_relationships = request.user.crush_relationship_set_from_source 
    if reveal_crush_id:
        try:
            reveal_crush_relationship = crush_relationships.get(target_person__username=reveal_crush_id)
            if reveal_crush_relationship.is_results_paid == False:
                reveal_crush_id = None #reset the value in this error case
        except CrushRelationship.DoesNotExist:
            reveal_crush_id = None
    responded_relationships = CrushRelationship.objects.visible_responded_crushes(me)
    crushes_completed_relationships = CrushRelationship.objects.completed_crushes(me).order_by('target_person__last_name')
    crushes_in_progress_count = CrushRelationship.objects.progressing_crushes(me).count()
    
    return render(request,'crushes.html',
                              {
                               'crush_type': 1, # 0 is in progress, 1 is matched, 2 is not matched
                               'responded_relationships':responded_relationships,
                               'crush_relationships':crushes_completed_relationships,
                               'crushes_in_progress_count': crushes_in_progress_count,
                               'crushes_completed_count' : crushes_completed_relationships.count,
                               'reveal_crush_id':reveal_crush_id,
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
                crush_relationship = CrushRelationship.objects.get(source_person=request.user,target_person__username=crush_username)
            except CrushRelationship.DoesNotExist:
                return render(request,"error.html",{ 'error': "App Invite Send encountered an unusual error.  Please try again later." })
            
            crush_email_success_array=[]
            crush_email_fail_array=[]
            friend_email_success_array=[]
            friend_email_fail_array=[]
            
            for email in crush_email_list:
                try:
                    InviteEmail.objects.process(new_email=email,new_relationship=crush_relationship,new_is_for_crush=True)
                    crush_email_success_array.append(email)
                except SMTPException:
                    crush_email_fail_array.append(email)
                    continue
            for email in friend_email_list:
                try:
                    InviteEmail.objects.process(new_email=email,new_relationship=crush_relationship,new_is_for_crush=False)
                    friend_email_success_array.append(email)
                except SMTPException:
                    friend_email_fail_array.append(email)
                    continue
            if request.is_ajax():
                print "success and returning rendered template"
                return render(request,'app_invite_success.html',{'crush_email_success_array':crush_email_success_array,
                                                                 'crush_email_fail_array':crush_email_fail_array,
                                                                 'friend_email_success_array':friend_email_success_array,
                                                                 'friend_email_fail_array':friend_email_fail_array,
                                                                 })
            else:
                print "success and redirecting"                
                return redirect('app_invite_success')
    else:
        # find mutual friends to pass to the app invite form
        fb_query_string = str(request.user.username + '/mutualfriends/' + crush_username)
        try:           
            friend_profile = graph_api_fetch(request.user.access_token,fb_query_string)
        except:
            raise 
        friendlist_string=''
        if friend_profile != None:
            for friend in friend_profile:
                friendlist_string+=friend['name'] + ', '
            friendlist_string=friendlist_string[:-2] # strip out last comma 
        print "friendlist_string: " + friendlist_string
        form=AppInviteForm(friendlist_string=friendlist_string)
        print "instantiated form instance"
    return render(request, 'app_invite_form.html',{'form':form,'crush_username':crush_username})

# called by the crush selector dialog
@login_required
def ajax_find_fb_user(request):

    response_data = dict()
    try:
        username=''
        username=request.REQUEST['username']
        me=request.user 
        access_token=me.access_token
        print "accessing user: " + username
        # call fb api to get user info and put it in the cleaned_data function
        crush_id=None
        fb_profile = graph_api_fetch('',username,expect_data=False)
        #raises KeyError if no id key/value pair exists in the fb_profile dictionary
        crush_id = fb_profile['id']
        if crush_id==me.username:
            response_data['error_message']='Invalid user: you cannot add yourself'
            return HttpResponse(json.dumps(response_data), mimetype="application/json")
        try:
            me.crush_targets.get(username=fb_profile['id'])
            response_data['error_message'] = 'You already added ' + fb_profile['name'] + ' as a crush.'
        except FacebookUser.DoesNotExist:
            
            try:
                fb_query_string= me.username + '/friends/' + crush_id
                friend_profile=graph_api_fetch(access_token,fb_query_string)
                if len(friend_profile)>0:
                    friend_type=0
                else:
                    fb_query_string= me.username + '/mutualfriends/' + crush_id
                    friend_profile=graph_api_fetch(access_token,fb_query_string)
    
                    if len(friend_profile)>0:
                        friend_type=1
                    else:
                        friend_type=2
                response_data['id']=fb_profile['id']
                response_data['name']=fb_profile['name']
                response_data['friend_type']=friend_type
            except:
                raise
    except HTTPError as e:
        print "Error: " + str(e.code)
        if e.code==404:
            print "BAD QUERY STRING"
            response_data['error_message'] = 'Invalid facebook username: ' + username
        elif e.code==400:
            print "BAD ACCESS TOKEN"
            raise
    except URLError as e: # most likley timeout
        print "Timeout"  + str(e.reason)
        if str(e.reason) == 'timed out': #timeout
            response_data['error_message'] = settings.AJAX_ERROR 

    return HttpResponse(json.dumps(response_data), mimetype="application/json")
 
@login_required
def ajax_initialize_nonfriend_lineup(request,target_username):
    ajax_response=''
    try:
        relationship = CrushRelationship.objects.all_crushes(request.user).get(target_person__username=target_username)
    except CrushRelationship.DoesNotExist:
        ajax_response += '* ' + settings.LINEUP_STATUS_CHOICES[4] + '<button id="initialize_lineup_btn">Re-initialize</button>'
        return HttpResponse(ajax_response) # this is a catch all error return state
    # if the non-friend is a reciprocal admirer (there is a date_target_responded), then there's no need to initialize the lineup, so just get out of here
    if relationship.date_target_responded != None:
        return HttpResponse()
    if relationship.lineup_initialization_status == None or relationship.lineup_initialization_status > 3:
        relationship.lineup_initialization_status = 0
        relationship.save(update_fields=['lineup_initialization_status'])

    if relationship.lineup_initialization_status == 0:
        # wait for a certain amount of time before returning a response
        counter = 0
        while True:
            #print "trying crush lineup initialization for " + relationship.target_person.last_name + " on try: " + str(counter) 

            if relationship.lineup_initialization_status > 0: # initialization was either a success or failed
                break
            elif counter==25: # if these number of seconds have passed then give up
                #print "giving up on crush: " + relationship.target_person.last_name
                relationship.lineup_initialization_status = 5
                relationship.save(update_fields=['lineup_initialization_status'])
                break
            time.sleep(1) # wait a quarter second
            counter+=1
    if relationship.lineup_initialization_status < 4 :
        return HttpResponse() # success or crush doesn't have enough friends
    else:
        ajax_response += '* ' + settings.LINEUP_STATUS_CHOICES[relationship.lineup_initialization_status] + '<button id="initialize_lineup_btn">Re-initialize</button>'
        return HttpResponse(ajax_response)
