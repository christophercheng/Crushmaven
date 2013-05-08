from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.conf import settings
from crush.models import CrushRelationship,PlatonicRelationship,FacebookUser,InviteEmail,SetupRelationship,SetupLineupMember
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

    
# -- Crush List Page --
@login_required
def setups_for_me(request):
    
    me = request.user
  
    progressing_setups = me.crush_setuprelationship_set_from_target.filter(date_lineup_finished=None).order_by('-updated_flag','date_added')
    setups_completed_count = me.crush_setuprelationship_set_from_target.exclude(date_lineup_finished=None).count()

    return render(request,'setups_for_me.html',
                              {
                               'setup_type': 0, # 0 is in progress, 1 is completed
                               'setup_relationships':progressing_setups,
                               'setups_in_progress_count': progressing_setups.count(),
                               'setups_completed_count':setups_completed_count,
                               })     

# -- Crushes Completed Page --
@login_required
def completed_setups_for_me(request):
    
    me = request.user
  
    completed_setups = me.crush_setuprelationship_set_from_target.exclude(date_lineup_finished=None).order_by('-updated_flag','date_added')
    setups_incomplete_count = me.crush_setuprelationship_set_from_target.filter(date_lineup_finished=None).count()

    return render(request,'setups_for_me.html',
                              {
                               'setup_type': 1, # 0 is in progress, 1 is completed
                               'setup_relationships':completed_setups,
                               'completed_setups_count': completed_setups.count(),
                               'setups_incomplete_count':setups_incomplete_count,
                               })       
    
@login_required
def setups_by_me(request):
    
    me = request.user
  
  # not right
    progressing_setups = me.crush_setuprelationship_set_from_source.filter(Q(date_setup_completed=None) | Q(updated_flag=True)).order_by('-updated_flag','date_added')
    setups_completed_count = me.crush_setuprelationship_set_from_source.exclude(Q(date_setup_completed=None) | Q(updated_flag=True)).count()

    return render(request,'setups_by_me.html',
                              {
                               'setup_type': 0, # 0 is in progress, 1 is completed
                               'setup_relationships':progressing_setups,
                               'setups_in_progress_count': progressing_setups.count(),
                               'setups_completed_count':setups_completed_count,
                               })     

# -- Crushes Completed Page --
@login_required
def completed_setups_by_me(request):
    
    me = request.user
  
  # not right
    completed_setups = me.crush_setuprelationship_set_from_source.exclude(Q(date_setup_completed=None) | Q(updated_flag=True)).order_by('-updated_flag','date_added')
    setups_incomplete_count = me.crush_setuprelationship_set_from_source.filter(Q(date_setup_completed=None) | Q(updated_flag=True)).count()

    return render(request,'setups_by_me.html',
                              {
                               'setup_type': 1, # 0 is in progress, 1 is completed
                               'setup_relationships':completed_setups,
                               'completed_setups_count': completed_setups.count(),
                               'setups_incomplete_count':setups_incomplete_count,
                               })     

@login_required
def setup_requests(request,reveal_crush_id=None):
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

# returns a comma separated string of usernames who cannot be recommended to the given setup target (existing recommendees)
@login_required    
def ajax_get_recommendee_exclude_ids(request, setup_target):
    # grab all setups of request.user where target_person = setup_target
    relevant_setups=request.user.crush_setuprelationship_set_from_source.filter(target_person__username=setup_target)
    previous_recommendee_id_csl=''
    # grab all setupLineupMembers of previous setups where 
        # the target is setup_target
        # the source is this request.user
        # the setupLineupMember is not relevant
    for setup in relevant_setups:
        existing_recommendee_objects = setup.setuplineupmember_set.all();
        for recommendee_object in existing_recommendee_objects:
            if previous_recommendee_id_csl != '':
                previous_recommendee_id_csl += ','
            previous_recommendee_id_csl += recommendee_object.username
    return previous_recommendee_id_csl

@login_required    
def setup_create_form(request):
    print "APP INVITE FORM!"
    # crush_name should be first name last name
    if request.method == 'POST': # if the form has been submitted...
        print "METHOD IS POST"
        setup_target_username = request.POST['target_username']
        setup_target_user = FacebookUser.objects.find_or_create_user(setup_target_username, fb_access_token=request.user.access_token, is_this_for_me=False,fb_profile=None)
        if setup_target_user == None:
            return
        recommendee_username_csl = request.POST['recommendee_username_csl']
        recommendee_username_array=recommendee_username_csl.split(',')
        if len(recommendee_username_array) == 0:
            return;
        setup = SetupRelationship.objects.create(target_person=setup_target_user,source_person=request.user,updated_flag=True,friendship_type=0)
        for (counter,recommendee) in enumerate(recommendee_username_array):
            SetupLineupMember.objects.create(relationship=setup, username = recommendee, position=counter)
        #perform find_or_create_user on target_username
        # create setupLIneupMember (with just username of each recommendee - no need to actually create user yet)
            # send out the emails here

        print "success and redirecting"                
        return redirect('/setups_by_me')
    else:
        # build list of exclude ids (anyone who is an undecided lineup member
        exclude_ids=''
        relevant_admirer_relationships = request.user.crush_crushrelationship_set_from_target.filter(date_lineup_finished=None)
        for relationship in relevant_admirer_relationships:
            # exclude lineup members in incompelte admirer relationships who weren't added as attraction (undecided or platonic)
            exclude_lineup_member_objects = relationship.lineupmember_set.exclude(decision=0)
            for lineup_member_object in exclude_lineup_member_objects:           
                if exclude_ids!='':
                    exclude_ids += ','
                exclude_ids += lineup_member_object.username
        return render(request, 'setup_create_form.html',{'exclude_ids':exclude_ids})
