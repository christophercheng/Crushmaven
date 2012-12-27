from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.conf import settings
from crush.models import CrushRelationship,PlatonicRelationship,FacebookUser,LineupMember, Purchase, EmailRecipient
import urllib, json
import random 
import paypal
from django.views.decorators.http import require_POST
from datetime import datetime
from crush.appinviteform import AppInviteForm
from crush.notification_settings_form import NotificationSettingsForm
from django.db.models import F

from smtplib import SMTPException

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
            friend_email_list=form.cleaned_data['friend_emails']
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
                    crush_relationship.date_invite_last_sent=datetime.now()
                    crush_relationship.target_status = 1
                    crush_relationship.save(update_fields=['date_invite_last_sent','target_status'])
                    for email in crush_email_list:
                        EmailRecipient.objects.create(crush_relationship=crush_relationship,recipient_address=email,date_sent=datetime.now(),is_email_crush=True)
                        
                    for email in friend_email_list:
                        EmailRecipient.objects.create(crush_relationship=crush_relationship,recipient_address=email,date_sent=datetime.now(),is_email_crush=False)                    
                except CrushRelationship.DoesNotExist:
                    pass #the database won't store app invite history, but that's ok as long as the actual emails were successfully sent
            except SMTPException:
                return render(request,"error.html",{ 'error': "App Invite Send encountered an unusual error.  Plese try again later." })
            if request.is_ajax():
                print "sucess!!!!!"
                return render(request,'app_invite_success.html',{'crush_email_list':crush_email_list,
                                                                 'friend_email_list':friend_email_list})
            else:
                return redirect('app_invite_success')
    else:
        form=AppInviteForm()
    return render(request, 'app_invite_form.html',{'form':form,'crush_username':crush_username})

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
        
    relationship.number_unrated_lineup_members = relationship.lineupmember_set.count()
    print "number lineup members: " + str(relationship.lineupmember_set.count())
    relationship.save(update_fields=['number_unrated_lineup_members'])

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
                               'add_as_platonic_friends':True
                               })    

# -- Friends with Admirers Page --
@login_required
def friends_with_admirers(request):

    return render(request,'friends_with_admirers.html',
                              {}
                  )

# -- Single Lineup (Ajax Content) Page --
@login_required
def lineup(request,admirer_id):
    try:
        admirer_rel = request.user.crush_relationship_set_from_target.get(admirer_display_id=admirer_id)
    except CrushRelationship.DoesNotExist:
        return HttpResponse("Error: Could not find an admirer relationship for the lineup.")
    # detract credit if lineup not already paid for
    if (not admirer_rel.is_lineup_paid):
        if (request.user.site_credits >= settings.FEATURES['1']['COST']):
            request.user.site_credits -= int(settings.FEATURES['1']['COST'])
            request.user.save(update_fields=['site_credits']) 
            admirer_rel.is_lineup_paid=True
            admirer_rel.target_status=3
            admirer_rel.save(update_fields=['is_lineup_paid','target_status'])
        else:
            return HttpResponse("Error: not enough credits to see lineup")
    lineup_set = admirer_rel.lineupmember_set.all()
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
        admirer_rel.number_unrated_lineup_members=F('number_unrated_lineup_members') - 1
        if admirer_rel.number_unrated_lineup_members == 0:
                admirer_rel.date_lineup_finished= datetime.now()
        admirer_rel.save(update_fields=['date_lineup_finished', 'number_unrated_lineup_members'])
    except FacebookUser.DoesNotExist:
        print "failed to add lineup member: " + facebook_id
        return HttpResponse("Server Error: Could not add given lineup user")  
    return HttpResponse(ajax_response)
    

# -- Notification settings --
@login_required
def modal_delete_crush(request):
    return HttpResponse("Text only, please.", content_type="text/plain")
    

# -- Profile Settings Page --
@login_required
def settings_profile(request):

    return render(request,'settings_profile.html',
                              {})
    
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
                    
                return redirect('/settings_notifications/')
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
            existing = Purchase.objects.get( tx=tx )
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
            existing = Purchase.objects.get( tx=txn_id )
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