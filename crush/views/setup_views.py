from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
#from django.conf import settings
from crush.models import CrushRelationship,FacebookUser,SetupRelationship,SetupLineupMember,SetupRequestRelationship
from  django.http import HttpResponseNotFound
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
def setup_requests_for_me(request):
    me = request.user
  
    requests_for_me = me.crush_setuprequestrelationship_set_from_target.filter().order_by('-updated_flag','date_added')
    requests_by_me_count = me.crush_setuprequestrelationship_set_from_source.count()

    return render(request,'setup_requests.html',
                              {
                               'request_type': 0, # 0 is in for me, 1 is by me
                               'request_relationships':requests_for_me,
                               'requests_by_me_count': requests_by_me_count,
                               })  

@login_required
def setup_requests_by_me(request):
    me = request.user
  
    requests_by_me = me.crush_setuprequestrelationship_set_from_source.filter().order_by('-updated_flag','date_added')
    requests_for_me_count = me.crush_setuprequestrelationship_set_from_target.count()

    return render(request,'setup_requests.html',
                              {
                               'request_type': 1, # 0 is in for me, 1 is by me                              
                               'request_relationships':requests_by_me,
                               'requests_for_me_count': requests_for_me_count,
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
def setup_create_form(request,target_person_username=""):
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
        #look for existing requests to create a setup for this target person, if it exists, then delete it
        try:
            outstanding_request = request.user.crush_setuprequestrelationship_set_from_target.get(source_person__username=setup_target_username)
            outstanding_request.delete()
        except SetupRequestRelationship.DoesNotExist:
            pass

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
        return render(request, 'setup_create_form.html',{'exclude_ids':exclude_ids,'target_person_username':target_person_username})
    
@login_required    
def ajax_create_setup_request(request,setup_request_target):
    
    # look for the target by username
        # if doesn't already exist then create the user
    setup_request_target_user = FacebookUser.objects.find_or_create_user(setup_request_target, fb_access_token=request.user.access_token, is_this_for_me=False,fb_profile=None)
    if setup_request_target_user == None:
        return HttpResponseNotFound("Was not able to create a user for the requested friend.")


    try:
        request.user.crush_setuprequestrelationship_set_from_source.get(target_person__username=setup_request_target)
    except SetupRequestRelationship.DoesNotExist:
        SetupRequestRelationship.objects.create(target_person=setup_request_target_user,source_person=request.user,updated_flag=True)
    return HttpResponse("")