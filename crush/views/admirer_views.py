from django.http import HttpResponse,HttpResponseNotAllowed,HttpResponseNotFound,HttpResponseForbidden
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from crush.models import CrushRelationship,PlatonicRelationship,LineupMember,FacebookUser
from crush.models.globals import g_init_dict
import datetime
from datetime import timedelta
import time,thread
from django.db.models import Q
from crush.utils import graph_api_fetch
from urllib2 import HTTPError
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# -- Admirer List Page --
@login_required
def admirers(request,show_lineup=None):
    global g_init_dict
    me = request.user 

    progressing_admirer_relationships = CrushRelationship.objects.progressing_admirers(me).order_by('friendship_type','is_lineup_paid','display_id')
    progressing_admirers_count = progressing_admirer_relationships.count()
    
    # initialize any uninitialized relationship lineups (status = None or greater than 1): (1 means initialized and 0 means initialization is in progress)
    uninitialized_relationships = progressing_admirer_relationships.filter(lineup_initialization_status=None)
    error_relationships = progressing_admirer_relationships.filter(Q(lineup_initialization_status=0) | Q(lineup_initialization_status__gt=1))
    start_relationships=[]
    if len(error_relationships) > 0:
        for relationship in error_relationships: 
            if relationship.lineup_initialization_status==0:
                if (datetime.datetime.now() - relationship.lineup_initialization_date_started) >= timedelta(minutes=settings.INITIALIZATION_RESTART_TIME_CRUSH_STATUS_0):
                    relationship.lineup_initialization_status=0 # reset intilization status
                    relationship.save(update_fields=['lineup_initialization_status'])
                    start_relationships.append(relationship)
                    continue
                #else: # need to tell user that relationship is in process of being initialized and they should wait
            elif relationship.lineup_initialization_status==2:
                if (datetime.datetime.now() - relationship.lineup_initialization_date_started) >= timedelta(hours=settings.INITIALIZATION_RESTART_TIME_CRUSH_STATUS_2):
                    relationship.lineup_initialization_status=0 # reset intilization status
                    relationship.save(update_fields=['lineup_initialization_status'])
                    start_relationships.append(relationship)
                    continue
            elif relationship.lineup_initialization_status == 3:
                if (datetime.datetime.now() - relationship.lineup_initialization_date_started) >= timedelta(minutes=settings.INITIALIZATION_RESTART_TIME_CRUSH_STATUS_3):
                    relationship.lineup_initialization_status=0 # reset intilization status
                    relationship.save(update_fields=['lineup_initialization_status'])
                    start_relationships.append(relationship)
                    continue
            else:
                if (datetime.datetime.now() - relationship.lineup_initialization_date_started) >= timedelta(minutes=settings.INITIALIZATION_RESTART_TIME_CRUSH_STATUS_4_5): 
                    relationship.lineup_initialization_status=0 # reset intilization status
                    relationship.save(update_fields=['lineup_initialization_status'])
                    start_relationships.append(relationship)
                    continue
 
    if len(uninitialized_relationships)>0 or len(start_relationships)>0:
        # reset initialize the global variable and set the number of relationships to initialize   
    
        for relationship in uninitialized_relationships:
            start_relationships.append(relationship)
        logger.debug("Initializing: " + str(len(start_relationships)) + " relationships")
 
        g_init_dict[me.username]={}    
        g_init_dict[me.username]['initialization_count'] = len(start_relationships) 


        if settings.INITIALIZATION_THREADING:
            thread.start_new_thread(LineupMember.objects.initialize_multiple_lineups,(start_relationships,))           
        else:
            LineupMember.objects.initialize_multiple_lineups(start_relationships)
    
    admirer_completed_relationships = CrushRelationship.objects.past_admirers(me).order_by('friendship_type','-display_id')
    past_admirers_count = admirer_completed_relationships.count()
     
    if progressing_admirers_count > 0 and past_admirers_count == 0:#  and not settings.DEBUG:
        show_help_popup=True
    else:
        show_help_popup=False
        
       
    return render(request,'admirers.html',
                              {'profile': me.get_profile, 
                               'admirer_relationships':progressing_admirer_relationships,
                               'past_admirer_relationships':admirer_completed_relationships,
                               'past_admirers_count': past_admirers_count,
                               'progressing_admirers_count':progressing_admirers_count,
                               'show_lineup': show_lineup,
                               'fof_fail_status':settings.LINEUP_STATUS_CHOICES[5],
                               'minimum_lineup_members':settings.MINIMUM_LINEUP_MEMBERS,
                               'ideal_lineup_members':settings.IDEAL_LINEUP_MEMBERS,  
                               'show_help_popup':show_help_popup,  
                               'lineup_block_timeout':settings.LINEUP_BLOCK_TIMEOUT                           
                               })    

    
    
@login_required
def ajax_display_lineup_block(request, display_id):
    global g_init_dict
    int_display_id=int(display_id)
    #logger.debug("ajax_initialize_lineup_block called with display id: " + str(int_display_id))
    ajax_response = ""
    try:    
        relationship = CrushRelationship.objects.all_admirers(request.user).get(display_id=int_display_id)
    except CrushRelationship.DoesNotExist:
        ajax_response += settings.LINEUP_STATUS_CHOICES[4]
        return HttpResponse('<div class="lineup_error">' + ajax_response + '</div>')
    
    crush_id = relationship.target_person.username
    rel_id_state=str(relationship.id) + '_initialization_state'
    # wait for a certain amount of time before returning a response
    counter = 0
    if relationship.lineup_initialization_status==0: # only loop if initialization status is 0 (in progress)
        logger.debug("staring while initialization loop")
        while True: # this loop handles condition where user is annoyingly refreshing the admirer page while the initialization is in progress     
            #print "rel_id: " + str(relationship.id) + " counter: " + str(counter) + " initialization status: " + str(relationship.lineup_initialization_status)
            if crush_id not in g_init_dict: #special case handling            
                #initialization hasn't started yet so wait another second before restarting loope
                #logger.debug("crush id not in g_init_dict while waiting in ajax_display_lineup_block with initialization status: " + str(relationship.lineup_initialization_status))
                #    relationship.save(update_fields=['lineup_initialization_status'])
                time.sleep(1) # wait a second
                counter+=1 
                continue
            if rel_id_state in g_init_dict[crush_id] and g_init_dict[crush_id][rel_id_state]==2: # initialization was either a success or failed
                #logger.debug("initialization was either a success or failure, breaking out of while loop")
                break
            elif counter>=settings.INITIALIZATION_TIMEOUT: # if 25 seconds have passed then give up
                logger.debug("giving up on server initialization of admirer relationship:" + str(relationship.id))
                relationship.lineup_initialization_status = 5
                relationship.save(update_fields=['lineup_initialization_status'])
                break
            #logger.debug("waiting for " + str(counter) + " seconds with initialization status:  " + str(relationship.lineup_initialization_status) + " and g_init_dict[crush_id][rel_id_state]: " + str(g_init_dict[crush_id][rel_id_state]))
            time.sleep(1) # wait a second
            counter+=1
        
        # refetch the relationship to get updated initialization status
        try:    
            relationship = CrushRelationship.objects.all_admirers(request.user).get(display_id=int_display_id)
        except CrushRelationship.DoesNotExist:
            ajax_response += settings.LINEUP_STATUS_CHOICES[4]
            logger.debug("could not refetch crush relationship object during initialization")
            return HttpResponse('<div class="lineup_error">' + ajax_response + '</div>')
    #logger.debug("finisehd with while initialization loop")
    if relationship.lineup_initialization_status > 1: # show error message
        ajax_response += settings.LINEUP_STATUS_CHOICES[relationship.lineup_initialization_status]
        logger.debug("lineup initialization status is greater than 1 in ajax_dispaly_lineup_block")
        return HttpResponse('<div class="lineup_error">' + ajax_response + '</div>')
    #logger.debug("going to lineup_block.html with lineup initialization status: " + str(relationship.lineup_initialization_status) + " and lineup member count: " + str(relationship.lineupmember_set.count()))
    return render(request,'lineup_block.html', {'relationship':relationship,
                                                'fail_status_5':settings.LINEUP_STATUS_CHOICES[5],
                                                'fail_status_2':settings.LINEUP_STATUS_CHOICES[2],
                                                'fail_status_3':settings.LINEUP_STATUS_CHOICES[3],})

# called if client-sided call to ajax_display_lineup_block timesout or fails for some odd reason.
@login_required
def ajax_initialization_failed(request, display_id):
    int_display_id=int(display_id)
    try:    
        relationship = CrushRelationship.objects.all_admirers(request.user).get(display_id=int_display_id)    
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound("")
    if relationship.lineup_initialization_status == None or relationship.lineup_initialization_status == 0:
        relationship.lineup_initialization_status = 5
        relationship.save(update_fields=['lineup_initialization_status'])
    return HttpResponse("")
    
    

# -- Single Lineup (Ajax Content) Page --
@login_required
def ajax_show_lineup_slider(request,admirer_id):
    me = request.user

    try:
        admirer_rel = CrushRelationship.objects.all_admirers(me).get(display_id=admirer_id)
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
    logger.debug("ajax get admirer: " + str(display_id) + " lineup position: " + lineup_position)
    ajax_response = ""
    me=request.user
    # obtain the admirer relationship
    try:
        admirer_rel=CrushRelationship.objects.all_admirers(me).get(display_id=display_id)
        # if lineup is not paid for, then don't show any content beyond slide 2
        if admirer_rel.is_lineup_paid == False and int(lineup_position) > 1:
        #     print "lineup_position just before forbidden error: " + lineup_position
            return HttpResponseForbidden("Error: You cannot access this content until the lineup is paid for.")
    except CrushRelationship.DoesNotExist:
        logger.warning( "Error: Could not find the admirer relationship.")
        return HttpResponseNotFound("Error: Could not find the admirer relationship.")

    lineup_member_set = admirer_rel.lineupmember_set 
    
    # obtain the actual user:
    lineup_member = lineup_member_set.get(position=lineup_position)
    # find or create a new user for the lineup member
    lineup_member_user=FacebookUser.objects.find_or_create_user(lineup_member.username, me.access_token, False, fb_profile=None)
    # if the lineup member user was not found for whatever reason, then we need to modify the lineup and strip out this member
    if lineup_member_user == None:
        logger.error (" facebook lineup user not found")
        ajax_response += '<div class="slide_container">'
        ajax_response +='<span class="lineup_name">user not available</span>'
        ajax_response +='<span class="lineup_mugshot view_facebook_widget"><img src="http://www.crushmaven.com/static/images/fb_unknown_user_pic.jpg"></span>'
        ajax_response +='<span class="lineup_facebook_link"><a href="http://www.facebook.com/' + str(lineup_member.username) + '" target="_blank"><span class="view_facebook_icon"></span>view profile</a></span>'
        ajax_response +='<span class="lineup_decision" username="' + str(lineup_member.username) + '" style="margin-top:5px">'
        ajax_response += "<span class=' choice crush existing_choice'>Sorry, this lineup member is no longer available...</span>"
        lineup_member.decision=1
        lineup_member.save(update_fields=['decision'])
        ajax_response += '</span></div>'
        return HttpResponse(ajax_response)
    
    if lineup_member.user==None: 
        lineup_member.user=lineup_member_user
        lineup_member.save(update_fields=['user'])
    
    # build the basic elements
    # 1) name, photo, position info 
    ajax_response += '<div class="slide_container">'
    ajax_response +='<a class="lineup_mugshot_link" href="https://www.facebook.com/' + lineup_member_user.username + '" target="_blank">' + '<span class="lineup_name">' + lineup_member_user.first_name + ' ' + lineup_member_user.last_name + '</span>'
    ajax_response +='<span class="lineup_mugshot"><img src="' + lineup_member_user.get_facebook_pic(125) + '"><span class="view_facebook_widget">view<span class="view_facebook_icon"></span></span> </a></span>'
    #ajax_response +='<span class="lineup_facebook_link"><a href="http://www.facebook.com/' + lineup_member_user.username + '" target="_blank"><span class="view_facebook_icon"></span>view profile</a></span>'

    # if the relationship is friend-of-friend, then show pictures of mutual friends:
    if admirer_rel.friendship_type==1:
        
        try:
            friend_profile=graph_api_fetch(request.user.access_token,request.user.username + '/mutualfriends/' + lineup_member.username)
            ajax_response +='<div id="mutual_friends"><span id="mutual_friends_prefix">mutual friends:</span>'
            for friend in friend_profile:
                ajax_response += '<a target="_blank" href="http://www.facebook.com/' + friend['id'] + '"><img src="http://graph.facebook.com/' + friend['id'] + '/picture?width=25&height=25" title="' + friend['name'] + '" style="height:25px;width:25px;"></a>'
            ajax_response += '</div>'
        except HTTPError as e:
            if e.code==400: # user's access token is invalid, so force user to log back in
                return HttpResponseNotAllowed('HTTPError')
            # no need to handle any other cases i.e. timeout since this isn't a vital function
        except:
            pass
    
    ajax_response +='<span class="lineup_decision" username="' + lineup_member_user.username + '" style="margin-top:5px">'
    
    # check to see if there is an existing crush relationship or platonic relationship:
    if lineup_member_user in me.crush_targets.all():
        ajax_response += '<span class="choice crush">Added as a Crush!</span>'
        lineup_member.decision = 0
        lineup_member.save(update_fields=['decision'])
    elif lineup_member_user in me.just_friends_targets.all():
        ajax_response += '<span class="choice platonic ">Not Interested</span>'
        ajax_response += '<a href="#" class="platonic_reconsider" add_type="crush" username="' + lineup_member_user.username + '" name="' + lineup_member_user.first_name + ' ' + lineup_member_user.last_name + '" member_gender= "' + lineup_member_user.gender + '" lineup_position="' + str(lineup_member.position) + '">change your mind?</a>'
        lineup_member.decision=1
        lineup_member.save(update_fields=['decision'])
    else:    
        if lineup_member.decision == None:
            ajax_response += '<a href="#" class="decision button lineup_decision_button" add_type="crush" username="' + lineup_member_user.username + '" name="' + lineup_member_user.first_name + ' ' + lineup_member_user.last_name + '" member_gender= "' + lineup_member_user.gender + '" lineup_position="' + lineup_position +  '">Add as Crush<span class="thumbs_up_icon">&nbsp;</span></a>' 
            ajax_response += '<a href="#" class="decision button lineup_decision_button" add_type="platonic" username="' + lineup_member_user.username + '" name="' + lineup_member_user.first_name + ' ' + lineup_member_user.last_name + '" member_gender= "' + lineup_member_user.gender + '" lineup_position="' + lineup_position + '">Not Interested</a>'        
       
        elif lineup_member.decision == 0:
            ajax_response += '<span class="crush choice" >Added as a Crush!</span>'
        else:
            ajax_response += '<span class="platonic choice">Not Interested</span>'   
    ajax_response += '</span>' # close off decision holder and decision tag
    ajax_response += '</div>' # close off slide_container
    #2) facebook button 
    #3) crush button 
    #4) platonic friend button  #
        
    return HttpResponse(ajax_response)

@login_required
def ajax_add_lineup_member(request,add_type,display_id,facebook_id,rating=3):
    logger.debug("adding member to a list")
    me=request.user
    # called from lineup.html to add a member to either the crush list or the platonic friend list
    try:
        target_user=FacebookUser.objects.get(username=facebook_id) # user is created when lineup slide loaded (if user wasn't already active)
        try:
            admirer_rel=CrushRelationship.objects.all_admirers(me).get(display_id=display_id)
        except CrushRelationship.DoesNotExist:
            return HttpResponse("Server Error: Could not add given lineup user")
        try:
            lineup_member=admirer_rel.lineupmember_set.get(username=target_user.username)
        except LineupMember.DoesNotExist:
            logger.error("could not find lineup member")
            return HttpResponse("Server Error: Could not add given lineup user")
       
        if lineup_member.decision!=None:
            # something is wrong, this person was already decided upon, so just return an error message
            # check to see if they haven't already been added as a crush
            if lineup_member.decision == 0:
                ajax_response = "<span id=\"choice\" class='crush choice existing_choice'>You already added " + target_user.first_name + " " + target_user.last_name + " as a crush.</span>"
                return HttpResponse(ajax_response)
            # else:
                # user changed their mind about platonic lineup member so exit out of here
                # break;
                #ajax_response = "<span id=\"choice\" class='platonic existing_choice'>You previously decided - Not Interested</span>"
           
        if add_type=='crush':
            # need to determine their friendship type

            if admirer_rel.friendship_type==0:
                new_relationship_friendship_type=0;
            elif admirer_rel.friendship_type== 2: # admirer has no mutual friends, and his friends will be lineup members so they will not be friends or have mutual friends with target person
                new_relationship_friendship_type=2;
            else: # admirer has mutual friends, so new relationship friendship type will likely be FOF (1) or no F (2).  there is a chance the lineup member is a friend, but not likely
                # test if there are mutual friends
                try:
                    friend_profile=graph_api_fetch(request.user.access_token,request.user.username + '/mutualfriends/' + facebook_id)
                    if len(friend_profile) > 0:
                        new_relationship_friendship_type=1
                    else:
                        new_relationship_friendship_type=2
                except:
                    # some error, so just assume not friends
                    new_relationship_friendship_type=2
            CrushRelationship.objects.create(source_person=request.user, target_person=target_user,friendship_type=new_relationship_friendship_type)
                        
            ajax_response = '<span class="choice crush new_crush" username="' + target_user.username + '" fullname="' + target_user.get_name() + '">Added as a crush</span>'
            lineup_member.decision=0
        else:
            PlatonicRelationship.objects.create(source_person=request.user, target_person=target_user,rating=rating)
            ajax_response = '<span class="choice platonic new_platonic">Not Interested</span>'
            ajax_response += '<a href="#" class="platonic_reconsider" add_type="crush" username="' + target_user.username + '" name="' + target_user.first_name + ' ' + target_user.last_name + '" member_gender= "' + target_user.gender + '" lineup_position="' + str(lineup_member.position) + '">change your mind?</a>'
            lineup_member.decision=1
        lineup_member.save(update_fields=['decision'])
        lineup_member_set = admirer_rel.lineupmember_set
        
        # handle processing when last lineup member decided upon
        if len(lineup_member_set.filter(decision=None)) == 0:
            admirer_rel.date_lineup_finished= datetime.datetime.now()
            admirer_rel.save(update_fields=['date_lineup_finished'])
        # make sure the crush relationship object's date_lineup_started field is set
        if (admirer_rel.date_lineup_started == None):
            admirer_rel.date_lineup_started = datetime.datetime.now()
            admirer_rel.target_status=3 # target status is now: started lineup
            admirer_rel.save(update_fields=['date_lineup_started','target_status'])
    except FacebookUser.DoesNotExist:
        logger.error( "failed to add lineup member: " + facebook_id )
        return HttpResponse("Server Error: Could not add given lineup user")  
    return HttpResponse(ajax_response)