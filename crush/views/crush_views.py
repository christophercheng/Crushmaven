from django.http import HttpResponse,HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import simplejson
from crush.models import CrushRelationship, PlatonicRelationship, FacebookUser, InviteEmail,LineupMember,PastTwitterUsername,PastPhone
import json
import datetime
from crush.appinviteformv2 import AppInviteForm2
from crush.utils import graph_api_fetch

from urllib2 import URLError, HTTPError
import thread
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)
# for initialization routine
# import thread
# from crush.models.globals import g_init_dict

# called by crush selector upson submit button press
@login_required
def ajax_add_crush_targets(request):
    post_data = request.POST
    # ensure that user has not exceeded beta limits:
    if request.user.crush_crushrelationship_set_from_source.filter(target_status__lt = 4).count()>settings.MAXIMUM_CRUSHES:
        return HttpResponseForbidden("Sorry, during this initial beta period, you cannot have more than " + str(settings.MAXIMUM_CRUSHES) + " ongoing crushes at a time.")
    # this is just for testing, remove later
    counter = 0
    for key in post_data:
        if key == "csrfmiddlewaretoken":
            continue
        logger.debug( " ajax added crush key: " + key + " : " + request.POST[key])
        counter += 1
        crushee_id=key;
        friend_type=int(request.POST[key])
        # find existing site user with this id or create a new user 
        selected_user = FacebookUser.objects.find_or_create_user(fb_id=crushee_id, fb_access_token=request.user.access_token, fb_profile=None, is_this_for_me=False)
        if selected_user == None:
            return HttpResponseForbidden("Sorry, we are experiencing problems with our servers at this time.  We hope to have the problem fixed soon.")
        # now that the user is definitely on the system, add that user to the crush list        
        # only create a new relationship if an existing one between the current user and the selected user does not exist 
        if not(request.user.crush_targets.filter(username=selected_user.username).exists()):
            CrushRelationship.objects.create(target_person=selected_user, source_person=request.user,
                                                       friendship_type=friend_type, updated_flag=True)
            thread.start_new_thread(adjust_associated_lineup_members,(request.user,selected_user,True))
    if counter > 0:
        return HttpResponse('')
    else:
        return HttpResponseNotFound("Sorry, we were not able to add to your crushes.  Please try again.")

@login_required
def ajax_can_crush_target_be_platonic_friend(request, crush_username):
    try:
        crush_relationship = CrushRelationship.objects.all_crushes(request.user).get(target_person__username=crush_username)
        print crush_relationship
        time_since_add = datetime.datetime.now() - crush_relationship.date_added
        if time_since_add.days < settings.MINIMUM_DELETION_DAYS_SINCE_ADD:
            return HttpResponseForbidden(settings.DELETION_ERROR[0])
        if crush_relationship.target_status == 3:
            return HttpResponseForbidden(settings.DELETION_ERROR[1])
        if crush_relationship.target_status >3 and crush_relationship.is_results_paid==True:  
            time_since_response_view = datetime.datetime.now() - crush_relationship.date_results_paid
            if time_since_response_view.days < settings.MINIMUM_DELETION_DAYS_SINCE_RESPONSE_VIEW:
                return HttpResponseForbidden(settings.DELETION_ERROR[2])
        return HttpResponse('')  # everything passes
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound(settings.GENERIC_ERROR)  # same thing as a successful deletion i guess?

# user is no longer interested in crush and will move them to a platonic friend
# crush must pass all of the conditions before it can be removed
@login_required
def ajax_make_crush_target_platonic_friend(request, crush_username):   
    conditional_response = ajax_can_crush_target_be_platonic_friend(request, crush_username)
    if conditional_response.status_code != 200:
        return HttpResponseForbidden(conditional_response.content)
        # all checks have passed, go ahead and 'make' this relationship a platonic one
    try:
        crush_relationship = CrushRelationship.objects.all_crushes(request.user).get(target_person__username=crush_username)
        target_person = crush_relationship.target_person
        crush_relationship.delete()
        PlatonicRelationship.objects.create(source_person=request.user, target_person=target_person)
        # ===== fix any associated lineup members
        thread.start_new_thread(adjust_associated_lineup_members,(request.user,target_person,False))
        
        return HttpResponse()
       
    except CrushRelationship.DoesNotExist:
        return HttpResponse()  # same thing as a successful deletion i guess?

def adjust_associated_lineup_members(target_person,lineup_user,new_crush):
        modify_members = LineupMember.objects.filter(relationship__target_person=target_person,user=lineup_user)
        for member in modify_members:
            if new_crush==True:
                member.decision=0
            else:
                member.decision = 3
            member.save(update_fields=['decision'])
    
# -- Crush List Page --
@login_required
def your_crushes(request, reveal_crush_id=None):
    
    me = request.user
  
    crush_progressing_relationships = CrushRelationship.objects.progressing_crushes(me).order_by('-updated_flag','target_status','target_person__first_name')

    # if there is at least one friend attraction, then we need to check the user's facebook privacy setting.  if their app visibility is not set to "only me", then display warning dialog
    if (len(crush_progressing_relationships.filter(friendship_type=0)) > 0):
        check_fb_privacy = True
    else:
        check_fb_privacy = False
    invite_crush_id=reveal_crush_id 
    if reveal_crush_id:
        try:
            CrushRelationship.objects.completed_crushes(me).get(target_person__username=reveal_crush_id)
        except CrushRelationship.DoesNotExist:
            reveal_crush_id = None
            # other use of reveal_crush_id is to auto launch invite dialog
            try: 
                CrushRelationship.objects.progressing_crushes(me).get(target_person__username=invite_crush_id)
            except CrushRelationship.DoesNotExist:
                invite_crush_id=None
                pass
            
    responded_relationships = CrushRelationship.objects.visible_responded_crushes(me).order_by('target_person__first_name')

    completed_crushes_relationships = CrushRelationship.objects.completed_crushes(me).order_by('-updated_flag','target_person__first_name')

    # determine whether to show help popup
    if crush_progressing_relationships.count() == 0 and completed_crushes_relationships.count() == 0 and responded_relationships.count() == 0:
        show_help_popup=True
    else:
        show_help_popup=False
    if me.email == '':
        email_exists=False
    else:
        email_exists=True
    show_invite_help_popup=False
    #determine whether to show invite help popup
    number_noninvited_crushes = crush_progressing_relationships.filter(target_status__lt=4,date_invite_last_sent=None).count()
    if number_noninvited_crushes>0:
        show_invite_help_popup=True
    return render(request, 'crushes.html',
                              {
                               'responded_relationships':responded_relationships,
                               'crush_relationships':crush_progressing_relationships,
                               'completed_crush_relationships':completed_crushes_relationships,
                               'crushes_in_progress_count': crush_progressing_relationships.count(),
                               'completed_crushes_count':completed_crushes_relationships.count(),
                               'lineup_status_choice_4':settings.LINEUP_STATUS_CHOICES[4],
                               'lineup_status_choice_5':settings.LINEUP_STATUS_CHOICES[5],
                               'check_fb_privacy_setting':check_fb_privacy,
                               'reveal_crush_id':reveal_crush_id,
                               'invite_crush_id':invite_crush_id,
                               'show_help_popup':show_help_popup,
                               'email_exists':email_exists,
                               'show_invite_help_popup':show_invite_help_popup,
                               })    
@login_required
def ajax_load_response_dialog_content(request, crush_id):
    # grab completed (paid) relationship from crush username
    try:
        relationship = CrushRelationship.objects.completed_crushes(request.user).get(target_person__username=crush_id)
        crush = relationship.target_person
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound("Error: Could not find a matching crush relationship.")
    ajax_response = ''
    # show the results of a responded attraction & show either congratulatory or sympathetic messaging
        # show messaging on what to do next
        # provide link for any next step action items
    if relationship.target_status == 4:
        ajax_response += "<div class='dialog_subtitle'>Congratulations!</div>" 
        ajax_response += "<div id='response_container'>"
        ajax_response += "<span class='response_message'>" + crush.get_name() + " expressed a mutual interest you.</span>"
        ajax_response += '<span class="attractor_image"><img src="http://graph.facebook.com/' + crush_id + '/picture?width=60&height=60" /><span class="decision_icon" id="decision_icon_yes"></span></span>';
        # check for any previously hidden messages from the target_person
        if request.user.received_messages.filter(sender=relationship.target_person).count() == 0:           
            ajax_response += "<a href='#'  crush_id='" + crush_id + "' id='response_send_message'>Send " + crush.first_name + " a Message</a>"
        else:
            ajax_response += "<span class='response_message'>" + crush.first_name + " sent you a message as well:</span>"
            ajax_response += "<a href='#' id='response_send_message' crush_id='" + crush_id + "'>view message</a>"
        ajax_response += "</div>"
    else:
        ajax_response += "<script>$(\".response_view_rating .help_icon\").qtip({content:{text:$('#feedback_help_content').clone(),title:'What is this?'},show:{delay:0,},hide:{delay:500,fixed:true,},style:{classes: 'qtip-blue qtip-rounded qtip-shadow',tip:{corner:true}}});</script>"
        ajax_response += "<div class='dialog_subtitle' id='response_no_match'>No Mutual Interest</div>" 
        ajax_response += "<div id='response_container'>"
        ajax_response += "<span class='response_message'>We're sorry, " + crush.get_name() + " did not express a mutual interest in you." + "</span>"
        ajax_response += '<span class="attractor_image"><img src="http://graph.facebook.com/' + crush_id + '/picture?width=60&height=60" /><span class="decision_icon" id="decision_icon_no"></span></span>';
        ajax_response += "<span class='response_message'></span>"
        ajax_response += "<span class='response_view_rating'>"
        if relationship.is_platonic_rating_paid:
            ajax_response += '"' + relationship.objects.get_target_platonic_rating_display() + '"'
        else:
            ajax_response += "<a href='#' unique_id='" + crush_id + "'>view " + crush.get_gender_pronoun() + " reason</a>"
            ajax_response += "<span class='help_icon'>?</span>"
        ajax_response += "</span></div>"   
    return HttpResponse(ajax_response)

@login_required
def ajax_get_platonic_rating(request, crush_id):

    try: 
        platonic_rating = None
        platonic_relationship = (request.user.crush_platonicrelationship_set_from_target).get(source_person__username=crush_id)
        platonic_rating = platonic_relationship.rating
        crush_relationship = CrushRelationship.objects.completed_crushes(request.user).get(target_person__username=crush_id)
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound(settings.AJAX_ERROR)
    except Exception as e:
        logger.error("problem getting platonic rating : " + str(e) )
        pass
    except PlatonicRelationship.DoesNotExist:
        return HttpResponseNotFound(settings.AJAX_ERROR)
    if crush_relationship.is_platonic_rating_paid:          

        response = '<span class="response_view_score_description">"' + crush_relationship.get_target_platonic_rating_display() + '"</span>'
        return HttpResponse(response)
    else:
        return HttpResponseForbidden("Error: You have not paid to see your attraction rating."); 

# returns an array of crush username strings - used for fb inviting friends and excluding crushes from the list
@login_required
def ajax_get_noinvite_crush_array(request):

    crush_targets = request.user.crush_targets.all()
    return_data = {}
    crush_array=[]
    for target in crush_targets:
        crush_array.append(target.username)
    return_data['data']=crush_array
    return HttpResponse(simplejson.dumps(return_data),mimetype='application/json')


@login_required    
def app_invite_form_v2(request, crush_username):
    crush_fullname=request.POST['crush_fullname']
    current_crush_number=request.POST['current_crush_number']
    total_crushes_string=request.POST['total_crushes_string']
    delayed_invite=request.POST['delayed_invite']
    total_crushes_int=int(total_crushes_string)
    crush_pronoun="Her"
    if request.user.gender_pref==u'M':
        crush_pronoun="His"
    elif request.user.gender_pref==u'B':
        crush_pronoun="Their"
    crush_firstname=crush_fullname.split(' ',1)[0]
    source_person_email=request.user.email
    # crush_name should be first name last name
    try:
        crush_relationship = CrushRelationship.objects.get(source_person=request.user, target_person__username=crush_username)
    except CrushRelationship.DoesNotExist:
        return render(request, "error.html", { 'error': "App Invite Send encountered an unusual error.  Please try again later." })
    
    if 'posted_form' in request.POST:  # if the form has been submitted...
        update_field_list=[]
        mutual_friend_json=eval(request.POST['mutual_friend_json'])
        form = AppInviteForm2(request.POST,mutual_friend_json=mutual_friend_json,source_person_email=source_person_email,source_person_username=request.user.username)
        if form.is_valid():
            # send out the emails here
            crush_email_list = form.cleaned_data['crush_emails']['cleaned_email_list']
            generic_friend_email_list = form.cleaned_data['mf_generic_emails']['cleaned_email_list']
            friend_email_list = form.get_mutual_friend_email_array()    
            
            crush_email_success_array = []
            crush_email_fail_array = []
            friend_email_success_array = []
            friend_email_fail_array = []
            
            for email in crush_email_list:
                try:
                    if InviteEmail.objects.process(new_email=email, new_relationship=crush_relationship, new_is_for_crush=True):
                        crush_email_success_array.append(email)
                    else:
                        crush_email_fail_array.append(email)
                except:
                    crush_email_fail_array.append(email)
                    continue
            for email in generic_friend_email_list:
                try:
                    if InviteEmail.objects.process(new_email=email, new_relationship=crush_relationship, new_is_for_crush=False):
                        friend_email_success_array.append(email)
                    else:
                        friend_email_fail_array.append(email)
                except:
                    friend_email_fail_array.append(email)
                    continue
            for mf in friend_email_list:
                for email in mf['cleaned_email_list']: 
                    try:
                        if InviteEmail.objects.process(new_email=email, new_relationship=crush_relationship, new_is_for_crush=False,mf_recipient_first_name=mf['recipient_first_name'],mf_recipient_fb_username=mf['recipient_fb_username']):
                            friend_email_success_array.append(email)
                        else:
                            friend_email_fail_array.append(email)
                    except:
                        friend_email_fail_array.append(email)
                        continue
            new_twitter_username = form.cleaned_data['twitter_username']['cleaned_email_list']
            if new_twitter_username != '':
                target_person=crush_relationship.target_person
                target_person_existing_twitter=target_person.twitter_username
                if target_person.twitter_username == None:
                    # update current twitter username 
                    crush_relationship.target_person.twitter_username=new_twitter_username
                    crush_relationship.target_person.save(update_fields=['twitter_username']);
                    # then send out programattic invite
                elif target_person_existing_twitter!=new_twitter_username:
                    # check if there already ten twitter handles, if so then just ignore this one (Some bad user behavior going on)
                    past_twitters=target_person.pasttwitterusername_set.all()
                    if past_twitters.count() < 10:
                        # check if current twitter name has been stored in a past twitterusername instance
                        new_twitter_exists=False
                        for past_twitter in past_twitters:
                            if past_twitter.twitter_username == new_twitter_username:
                                new_twitter_exists=True;
                                break
                        if not new_twitter_exists:
                            # if it has not already been stored, then store it into past twitterUsername instance
                            PastTwitterUsername.objects.create(user=target_person,twitter_username=target_person_existing_twitter,date_twitter_invite_last_sent=target_person.date_twitter_invite_last_sent)
                            # update the current twitter username
                            crush_relationship.target_person.twitter_username=new_twitter_username
                            crush_relationship.target_person.save(update_fields=['twitter_username']);
                        # if new twitter username not previously stored, then send off programatic invite
                        # if previously stored, then don't send off programatic invite
            new_phone = form.cleaned_data['phone']['cleaned_email_list']
            if new_phone != '':
                target_person=crush_relationship.target_person
                target_person_existing_phone=target_person.phone
                if target_person.phone == None:
                    # update current twitter username 
                    crush_relationship.target_person.phone=new_phone
                    crush_relationship.target_person.save(update_fields=['phone']);
                    # then send out programattic invite
                elif target_person_existing_phone!=new_phone:
                    # check if there already ten twitter handles, if so then just ignore this one (Some bad user behavior going on)
                    past_phones=target_person.pastphone_set.all()
                    if past_phones.count() < 10:
                        # check if current twitter name has been stored in a past twitterusername instance
                        new_phone_exists=False
                        for past_phone in past_phones:
                            if past_phone.phone == new_phone:
                                new_phone_exists=True;
                                break
                        if not new_phone_exists:
                            # if it has not already been stored, then store it into past twitterUsername instance
                            PastPhone.objects.create(user=target_person,phone=target_person_existing_phone,date_phone_invite_last_sent=target_person.date_phone_invite_last_sent)
                            # update the current twitter username
                            crush_relationship.target_person.phone=new_phone
                            crush_relationship.target_person.save(update_fields=['phone']);
                        # if new twitter username not previously stored, then send off programatic invite
                        # if previously stored, then don't send off programatic invite           
                    
            # change status of crush relationship to invites sent (status 1) if at least one email successfully sent out
            if len(crush_email_success_array) > 0 or len(friend_email_success_array) > 0 or new_twitter_username!="" or new_phone!="":
                crush_relationship.target_status = 1;
                crush_relationship.date_invite_last_sent = datetime.datetime.now()
                crush_relationship.updated_flag = True
                update_field_list.append('target_status')
                update_field_list.append('date_invite_last_sent')
                update_field_list.append('updated_flag')
                crush_relationship.save(update_fields=update_field_list);        
            return HttpResponse("_GOOD") # special text tells app_invite_form_v2 js submission function that the function was a success
    else:
        current_crush_number = int(current_crush_number) + 1

        # determine if they haven't surpassed the total number of users to send out emails to:
        
        # find mutual friends to pass to the app invite form
        fb_query_string = str(request.user.username + '/mutualfriends/' + crush_username)
        try:           
            mutual_friend_json = graph_api_fetch(request.user.access_token, fb_query_string)
        except Exception as e:
            logger.debug("finding mutual friends failed with exception: " + str(e))
            raise  
        form = AppInviteForm2(mutual_friend_json=mutual_friend_json,source_person_email=source_person_email,source_person_username=request.user.username)
    mf_friend_count=len(mutual_friend_json)
    return render(request, 'app_invite_form_v2.html', {'form':form,'crush_username':crush_username, 'crush_fullname':crush_fullname, 'crush_firstname':crush_firstname, 'crush_pronoun':crush_pronoun,'mutual_friend_json':mutual_friend_json,'mf_friend_count':mf_friend_count,'delayed_invite':delayed_invite,'total_crushes_string':total_crushes_string,'total_crushes_int':total_crushes_int,'current_crush_number':str(current_crush_number)})


# called by the crush selector dialog
@login_required
def ajax_find_fb_user(request):

    response_data = dict()
    try:
        username = ''
        username = request.REQUEST['username']
        me = request.user 
        access_token = me.access_token
        logger.debug( "accessing user: " + username )
        # call fb api to get user info and put it in the cleaned_data function
        crush_id = None
        fb_profile = graph_api_fetch('', username, expect_data=False)
        # raises KeyError if no id key/value pair exists in the fb_profile dictionary
        crush_id = fb_profile['id']
        if crush_id == me.username:
            response_data['error_message'] = 'Invalid user: you cannot add yourself'
            return HttpResponse(json.dumps(response_data), mimetype="application/json")
        try:
            me.crush_targets.get(username=fb_profile['id'])
            response_data['error_message'] = 'You already added ' + fb_profile['name'] + ' as a crush.'
        except FacebookUser.DoesNotExist:
            
            try:
                fb_query_string = me.username + '/friends/' + crush_id
                friend_profile = graph_api_fetch(access_token, fb_query_string)
                if len(friend_profile) > 0:
                    friend_type = 0
                else:
                    fb_query_string = me.username + '/mutualfriends/' + crush_id
                    friend_profile = graph_api_fetch(access_token, fb_query_string)
    
                    if len(friend_profile) > 0:
                        friend_type = 1
                    else:
                        friend_type = 2
                response_data['id'] = fb_profile['id']
                response_data['name'] = fb_profile['name']
                response_data['friend_type'] = friend_type
            except:
                raise
    except HTTPError as e:
        print "Error: " + str(e.code)
        if e.code == 404:
            logger.debug ("BAD QUERY STRING")
            response_data['error_message'] = 'Invalid facebook username: ' + username
        elif e.code == 400:
            logger.warning ("BAD ACCESS TOKEN")
            raise
    except URLError as e:  # most likley timeout
        logger.warning( "ajax find user Timeout" + str(e.reason))
        if str(e.reason) == 'timed out':  # timeout
            response_data['error_message'] = settings.AJAX_ERROR 

    return HttpResponse(json.dumps(response_data), mimetype="application/json")

# called by new message write form to determine if attraction is messageeable
@login_required
def ajax_user_can_message(request, crush_id):
    # grab completed (paid) relationship from crush username
    try:
        relationship = CrushRelationship.objects.completed_crushes(request.user).get(target_person__username=crush_id)
        if relationship.date_messaging_expires is not None and datetime.date.today() <= relationship.date_messaging_expires:
            return HttpResponse("");
        else:
            return HttpResponseForbidden("");
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound("Error: Could not find a matching crush relationship.")
