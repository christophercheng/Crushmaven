from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from crush.models import CrushRelationship,PlatonicRelationship,FacebookUser,InviteEmail,Recommendation,RecommendationLineupMember
import json
import datetime
from crush.appinviteform import AppInviteForm
import time
from  django.http import HttpResponseNotFound,HttpResponseForbidden
from utils import graph_api_fetch
from urllib2 import URLError,HTTPError
# for initialization routine
#import thread
#from crush.models.globals import g_init_dict

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
def friend_setups(request,reveal_crush_id=None):
    
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

# -- Crushes Completed Page --
@login_required
def friend_setups_completed(request,reveal_crush_id=None):
    me = request.user
    crush_relationships = request.user.crush_crushrelationship_set_from_source 
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
def my_setups(request,reveal_crush_id=None):
    
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

# -- Crushes Completed Page --
@login_required
def my_setups_completed(request,reveal_crush_id=None):
    me = request.user
    crush_relationships = request.user.crush_crushrelationship_set_from_source 
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
def recommendation_create_form(request):
    print "APP INVITE FORM!"
    # crush_name should be first name last name
    if request.method == 'POST': # if the form has been submitted...
        print "METHOD IS POST"
        recommendation_target_username = request.POST['target_username']
        recommendation_target_user = FacebookUser.objects.find_or_create_user(recommendation_target_username, fb_access_token=request.user.access_token, is_this_for_me=False,fb_profile=None)
        if recommendation_target_user == None:
            return
        if recommendation_target_user.is_active==True:
            target_status=1
        else:
            target_status=0
        recommendee_username_csl = request.POST['recommendee_username_csl']
        recommendee_username_array=recommendee_username_csl.split(',')
        if len(recommendee_username_array) == 0:
            return;
        recommendation = Recommendation.objects.create(target_person=recommendation_target_user,source_person=request.user,updated_flag=True,friendship_type=0,target_status=target_status)
        for (counter,recommendee) in enumerate(recommendee_username_array):
            RecommendationLineupMember.objects.create(recommendation=recommendation, username = recommendee, position=counter)
        #perform find_or_create_user on target_username
        # create RecommendationLIneupMember (with just username of each recommendee - no need to actually create user yet)
            # send out the emails here

        print "success and redirecting"                
        return redirect('/my_setups')
    else:
        return render(request, 'recommendation_create_form.html')
