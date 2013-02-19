from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from crush.models import CrushRelationship,PlatonicRelationship,LineupMember,FacebookUser
from crush.models.lineup_models import initialize_lineup
import datetime
from multiprocessing import Pool
from django.http import HttpResponseNotFound,HttpResponseForbidden
import time,random,thread
from django.db import transaction

g_initialization_timeout=None

# -- Admirer List Page --
@login_required
def admirers(request,show_lineup=None):
    global g_initialization_timeout
    g_initialization_timeout=25 # how much time should elapse before ajax initialization call fails
    me = request.user 
    progressing_admirer_relationships = CrushRelationship.objects.progressing_admirers(me)
    past_admirers_count = CrushRelationship.objects.past_admirers(me).count()
    
    # initialize any uninitialized relationship lineups
    uninitialized_relationships = progressing_admirer_relationships.exclude(lineup_initialization_status=1) 
    
    # reset the initialization status of any relationships that previously erred out:
    for error_relationship in uninitialized_relationships.filter(lineup_initialization_status__gt=1):
        error_relationship.lineup_initialization_status=0
        error_relationship.save(update_fields=['lineup_initialization_status'])
    
    uninitialized_friend_relationships = uninitialized_relationships.filter(friendship_type=0) 
    uninitialized_nonfriend_relationships = uninitialized_relationships.exclude(friendship_type=0) 
    
    # initialize friend relationships serially, albeit in a separate asynchronously fired process 
    if len(uninitialized_friend_relationships) > 0:
        friend_pool=Pool(1)
        g_initialization_timeout=25 + ((len(uninitialized_friend_relationships)-1)*5)# add time to timeout if multiple separated relationships
        for relationship in uninitialized_friend_relationships:
            #initialize_lineup(relationship)
            friend_pool.apply_async(initialize_lineup,[relationship])  
            
    # initialize non friend relationships asynchronously at once using threads
    for relationship in uninitialized_nonfriend_relationships:
        thread.start_new_thread(initialize_lineup,(relationship,)) 
        #initialize_lineup(relationship)

    return render(request,'admirers.html',
                              {'profile': me.get_profile, 
                               'admirer_type': 0, # 0 is in progress, 1 completed
                               'admirer_relationships':progressing_admirer_relationships,
                               'past_admirers_count': past_admirers_count,
                               'show_lineup': show_lineup,
                               'fof_fail_status':settings.LINEUP_STATUS_CHOICES[5],
                               'minimum_lineup_members':settings.MINIMUM_LINEUP_MEMBERS,
                               'ideal_lineup_members':settings.IDEAL_LINEUP_MEMBERS,                               
                               })    
    
@login_required
def ajax_display_lineup_block(request, display_id):
    int_display_id=int(display_id)
    print "ajax initialize lineup with display id: " + str(int_display_id)
    ajax_response = ""
  
    # wait for a certain amount of time before returning a response
    counter = 0
    while True: # this loop handles condition where user is annoyingly refreshing the admirer page while the initialization is in progress
        #print "trying admirer lineup initialization for " + relationship.target_person.last_name + ":" + display_id + " on try: " + str(counter)       
        try:    
            relationship = CrushRelationship.objects.all_admirers(request.user).get(admirer_display_id=int_display_id)
        except CrushRelationship.DoesNotExist:
            ajax_response += '* ' + settings.LINEUP_STATUS_CHOICES[4] + '<button id="initialize_lineup_btn">Re-initialize</button>'
            return HttpResponse(ajax_response)   
        print "rel_id: " + str(relationship.id) + " counter: " + str(counter) + " initialization status: " + str(relationship.lineup_initialization_status)
        if relationship.lineup_initialization_status > 0: # initialization was either a success or failed
            break
        elif counter==1: # if 30 seconds have passed then give up
            print "giving up on admirer:" + str(display_id)
            relationship.lineup_initialization_status = 5
            relationship.save(update_fields=['lineup_initialization_status'])
            break
        time.sleep(5) # wait a quarter second
        counter+=1

    if relationship.lineup_initialization_status > 3: # for data fetching errors show a button that allows user to restart the initialization 
        ajax_response += '* ' + settings.LINEUP_STATUS_CHOICES[relationship.lineup_initialization_status] + ' <button id="initialize_lineup_btn" display_id="' + display_id + '">Re-initialize</button>'
        return HttpResponse(ajax_response)
    if relationship.lineup_initialization_status > 1: # show error message
        ajax_response += '* ' + settings.LINEUP_STATUS_CHOICES[relationship.lineup_initialization_status]
        return HttpResponse(ajax_response)

    return render(request,'lineup_block.html', {'relationship':relationship,
                                                'fail_status_5':settings.LINEUP_STATUS_CHOICES[5],
                                                'fail_status_2':settings.LINEUP_STATUS_CHOICES[2],
                                                'fail_status_3':settings.LINEUP_STATUS_CHOICES[3],})

# -- Single Lineup (Ajax Content) Page --
@login_required
def ajax_show_lineup_slider(request,admirer_id):
    me = request.user
    try:
        admirer_rel = CrushRelationship.objects.all_admirers(me).get(admirer_display_id=admirer_id)
    except CrushRelationship.DoesNotExist:
        return HttpResponse("Error: Could not find an admirer relationship for the lineup.")

    member_set = admirer_rel.lineupmember_set.all()
    
    # need to cleanse the lineup members each time the lineup is run 
    # reason: while lineup is not complete, user may have added one of the lineup member as either a crush or a platonic frined
        
    return render(request,'lineup.html',
                              {
                               'admirer_rel':admirer_rel,
                               'member_set': member_set,
                               'number_completed_members': len(member_set.exclude(decision = None)),
                               'rating1': settings.PLATONIC_RATINGS[1],
                               'rating2': settings.PLATONIC_RATINGS[2],
                               'rating3': settings.PLATONIC_RATINGS[3],
                               'rating4': settings.PLATONIC_RATINGS[4],
                               'rating5': settings.PLATONIC_RATINGS[5],
                               })

# called by lineup lightbox slider to show an individual lineup member - and allow user to rate them
@login_required
#@csrf_exempt
def ajax_get_lineup_slide(request, display_id,lineup_position):
    print "ajax get admirer: " + str(display_id) + " lineup position: " + lineup_position
    print "please change!"
    ajax_response = ""
    me=request.user
    # obtain the admirer relationship
    try:
        admirer_rel=CrushRelationship.objects.all_admirers(me).get(admirer_display_id=display_id)
        # if lineup is not paid for, then don't show any content beyond slide 2
        if admirer_rel.is_lineup_paid == False and int(lineup_position) > 1:
        #     print "lineup_position just before forbidden error: " + lineup_position
            return HttpResponseForbidden("Error: You cannot access this content until the lineup is paid for.")
    except CrushRelationship.DoesNotExist:
        print "Error: Could not find the admirer relationship."
        return HttpResponseNotFound("Error: Could not find the admirer relationship.")
    # obtain the actual user:
    lineup_member = admirer_rel.lineupmember_set.get(position=lineup_position)
    # find or create a new user for the lineup member
    lineup_member_user=FacebookUser.objects.find_or_create_user(lineup_member.username, me.access_token, False, fb_profile=None)
    if lineup_member.user==None:
        lineup_member.user=lineup_member_user
        lineup_member.save(update_fields=['user'])
    lineup_count = len(admirer_rel.lineupmember_set.all())
    display_position=int(lineup_position) + 1;
    
    # build the basic elements
    # 1) name, photo, position info 
    ajax_response +='<div id="name">' + lineup_member_user.first_name + ' ' + lineup_member_user.last_name + '</div>'
    ajax_response +='<div id="mugshot" style="width:80px;height:80px"><img src="' + lineup_member_user.get_facebook_picture() + '" height="80" width="10"></div>'
    ajax_response +='<div id="position_info"><span>member ' + str(display_position)  + ' out of ' + str(lineup_count) + '<span></div>'
    ajax_response +='<div id="facebook_link"><a href="http://www.facebook.com/' + lineup_member_user.username + '" target="_blank">view facebook profile</a></div>'
    ajax_response +='<div id="decision" username="' + lineup_member_user.username + '">'
    
    # check to see if there is an existing crush relationship or platonic relationship:
    if lineup_member_user in me.crush_targets.all():
        ajax_response += "<div id=\"choice\">You already added " + lineup_member_user.first_name + " " + lineup_member_user.last_name + " as an attraction.</div>"
        lineup_member.decision = 0
        lineup_member.save(update_fields=['decision'])
    elif lineup_member in me.just_friends_targets.all():
        ajax_response = "<div id=\"choice\">You already decided: Not Interested in " + lineup_member_user.first_name + " " + lineup_member_user.last_name + "</div>"
        lineup_member.decision= 1
        lineup_member.save(update_fields=['decision'])
    else:    
        if lineup_member.decision == None:
            ajax_response += '<a href="#" class="attraction_add" add_type="crush" username="' + lineup_member_user.username + '" name="' + lineup_member_user.first_name + ' ' + lineup_member_user.last_name + '" lineup_position="' + lineup_position +  '">Add to Attractions</a>' 
            ajax_response += '<br><a href="#" class="platonic_add" add_type="platonic" username="' + lineup_member_user.username + '" name="' + lineup_member_user.first_name + ' ' + lineup_member_user.last_name + '" lineup_position="' + lineup_position + '">Not Interested</a>'        
       
        elif lineup_member.decision == 0:
            ajax_response += '<div class="crush" id="choice" >"You added' + lineup_member_user.first_name + ' ' + lineup_member_user.last_name + ' as an attraction!</div>'
        else:
            ajax_response += '<div class="platonic" id="choice">You are Not Interested in ' + lineup_member_user.first_name + ' ' + lineup_member_user.last_name + '</div>'   
    ajax_response += '</div>' # close off decision tag
    #2) facebook button 
    #3) crush button 
    #4) platonic friend button  #
    
    
    return HttpResponse(ajax_response)

@login_required
def ajax_add_lineup_member(request,add_type,admirer_display_id,facebook_id):
    print "adding member to a list"
    me=request.user
    # called from lineup.html to add a member to either the crush list or the platonic friend list
    try:
        target_user=FacebookUser.objects.get(username=facebook_id)
        try:
            admirer_rel=CrushRelationship.objects.all_admirers(me).get(admirer_display_id=admirer_display_id)
        except CrushRelationship.DoesNotExist:
            return HttpResponse("Server Error: Could not add given lineup user")
        try:
            lineup_member=admirer_rel.lineupmember_set.get(username=target_user.username)
        except LineupMember.DoesNotExist:
            print "could not find lineup member"
            return HttpResponse("Server Error: Could not add given lineup user")

        if lineup_member.decision!=None:
            # something is wrong, this person was already decided upon, so just return an error message
            # check to see if they haven't already been added as a crush
            if lineup_member.decision == 0:
                ajax_response = "<div id=\"choice\">You already added " + target_user.first_name + " " + target_user.last_name + " as a crush!</div>"
            else:
                ajax_response = "<div id=\"choice\">You already added " + target_user.first_name + " " + target_user.last_name + " as a platonic friend.</div>"
            return HttpResponse(ajax_response)
        if add_type=='crush':
            CrushRelationship.objects.create(source_person=request.user, target_person=target_user)
            ajax_response = '<div id="choice" class="crush">You added ' + target_user.first_name + ' ' + target_user.last_name + ' as a crush!</div>'
            lineup_member.decision=0
        else:
            PlatonicRelationship.objects.create(source_person=request.user, target_person=target_user)
            ajax_response = '<div id="choice" class="platonic">You added ' + target_user.first_name + ' ' + target_user.last_name + ' as a platonic friend.</div>'
            lineup_member.decision=1
        lineup_member.save(update_fields=['decision'])
        if len(admirer_rel.lineupmember_set.filter(decision=None)) == 0:
            admirer_rel.date_lineup_finished= datetime.datetime.now()
            admirer_rel.save(update_fields=['date_lineup_finished'])
    except FacebookUser.DoesNotExist:
        print "failed to add lineup member: " + facebook_id
        return HttpResponse("Server Error: Could not add given lineup user")  
    return HttpResponse(ajax_response)

@login_required
def ajax_update_num_platonic_friends(request):

    ajax_response = str(request.user.just_friends_targets.all().count())
    return HttpResponse(ajax_response)
@login_required
def ajax_update_num_crushes_in_progress(request):
    ajax_response = str(request.user.crush_targets.all().count())
    return HttpResponse(ajax_response)

# called when a crush response is paid for
@login_required
def ajax_update_num_new_responses(request):
    ajax_response = str(CrushRelationship.objects.known_responded_crushes(request.user).count())
    return HttpResponse(ajax_response)

# called when a lineup goes past the payment stage
@login_required
def ajax_update_num_new_admirers(request):
    ajax_response = str(CrushRelationship.objects.new_admirers(request.user).count())
    return HttpResponse(ajax_response)

# -- Past Admirers Page --
@login_required
def admirers_past(request):
    me = request.user 
   
    admirer_completed_relationships = CrushRelationship.objects.past_admirers(me).order_by('date_added')
    progressing_admirers_count = CrushRelationship.objects.progressing_admirers(me).count()
    
    return render(request,'admirers.html',
                              {
                               'admirer_type': 1, # 0 is in progress, 1 completed
                               'admirer_relationships':admirer_completed_relationships,
                               'progressing_admirers_count': progressing_admirers_count,
                               'fof_fail_status':settings.LINEUP_STATUS_CHOICES[2],
                               'minimum_lineup_members':settings.MINIMUM_LINEUP_MEMBERS,
                               'ideal_lineup_members':settings.IDEAL_LINEUP_MEMBERS,  
                               })    
