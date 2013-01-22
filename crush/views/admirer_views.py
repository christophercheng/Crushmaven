from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from crush.models import CrushRelationship,PlatonicRelationship,FacebookUser,LineupMembership
from crush.utilities import  initialize_lineup
import datetime
from multiprocessing import Pool
from django.http import HttpResponseNotFound,HttpResponseForbidden
import time

# -- Admirer List Page --
@login_required
def admirers(request,show_lineup=None):

    me = request.user 

    # get list of responded (so we can filter them out the admirers )
    progressing_crush_list = me.crush_targets.filter(crush_relationship_set_from_target__target_status__gt = 3,crush_relationship_set_from_target__is_results_paid=False)   
    # if admirer is already a platonic friend of the crush, then don't create a new admirer block or a new lineup; 
    # build a list of incomplete admirer relationship by filtering them in the following order:
    #     filter through only those admirer relationships who have not finished their lineup (progressing relationships)
    #     filter out those progressing relationships who are also progressing crushes AND who have not yet instantiated a lineup
    #        if they are also a progressing crush, but a lineup has already been created, then don't filter them out
    admirer_relationships = me.crush_relationship_set_from_target
    progressing_admirer_relationships = admirer_relationships.filter(date_lineup_finished=None)
    progressing_admirer_relationships = progressing_admirer_relationships.all().exclude(source_person__in = progressing_crush_list, lineup_initialization_status = None)
    progressing_admirer_relationships = progressing_admirer_relationships.all().exclude(source_person__in = me.just_friends_targets.all()).order_by('target_status','date_added') # valid progressing relationships 

    past_admirers_count = admirer_relationships.exclude(date_lineup_finished=None).count()
    
    # initialize the lineups of any new admirer relationships
        # filter out the new relationships whose lineup member 1 is empty
    
    uninitialized_relationships = progressing_admirer_relationships.exclude(lineup_initialization_status=1) #get all relationships that don't already have a lineup (number of lineump members is zero)
    if (uninitialized_relationships):
        print "hey, found an uninitialized relationship"
        #pool=Pool(1) #must be 1 or things go bad!
        for relationship in uninitialized_relationships:
            #pool.apply_async(initialize_lineup,[relationship],) #initialize lineup asynchronously
            initialize_lineup(relationship)

    return render(request,'admirers.html',
                              {'profile': me.get_profile, 
                               'admirer_type': 0, # 0 is in progress, 1 completed
                               'admirer_relationships':progressing_admirer_relationships,
                               'past_admirers_count': past_admirers_count,
                               'show_lineup': show_lineup})    

@login_required
def ajax_display_lineup_block(request, display_id):
    int_display_id=int(display_id)
    print "ajax initialize lineup with display id: " + str(int_display_id)
    ajax_response = ""
    try:    
        counter = 0
        while True:
            print "trying admirer " + str(display_id) + " on try: " + str(counter) 
            admirer_rel=request.user.crush_relationship_set_from_target.get(admirer_display_id=int_display_id)
            if admirer_rel.lineup_initialization_status > 0: # initialization was either a success or failed
                if admirer_rel.lineup_initialization_status == 1:
                    break
                else:
                    return HttpResponse(settings.LINEUP_STATUS_CHOICES[admirer_rel.lineup_initialization_status])
            elif counter==25: # if 30 seconds have passed then give up
                print "giving up on admirer:" + str(display_id)
                return HttpResponse("Sorry, we are having difficulty enough data from Facebook to create your lineup.  Please try again later.")
                #return HttpResponseNotFound(str(display_id),content_type="text/plain")
            time.sleep(1) # wait a quarter second
            counter+=1

        for counter, membership in enumerate(admirer_rel.lineupmembership_set.all()):
            if counter < 2 or membership.decision!=None:
                ajax_response +=  '<img src="http://graph.facebook.com/' + membership.lineup_member.username + '/picture" height=40 width=40>'
            else:
                ajax_response += '<img src = "http://a3.twimg.com/profile_images/1649076583/facebook-profile-picture-no-pic-avatar_reasonably_small.jpg" height =40 width = 40>'

        ajax_response += '<BR>'
        
        if admirer_rel.is_lineup_paid:
            if admirer_rel.date_lineup_finished:
                ajax_response += 'Line-up completed ' + str(admirer_rel.date_lineup_finished)
                ajax_response += '<a href="#" class="view_lineup" display_id="' + display_id + '"><BR>View Completed Lineup</a>'
            else:
                ajax_response += '<a href="#" class="view_lineup" display_id="' + display_id + '">Finish Lineup</a>'
      
        else:
            ajax_response += '<a href="#" class="view_lineup" display_id="' + display_id + '">View Lineup</a>'
    
    except CrushRelationship.DoesNotExist:
        print "could not find admirer relationship"
        ajax_response="Sorry, there is a problem processing the lineup for this admirer.  We are working on fixing this issue."

    
    return HttpResponse(ajax_response)

# -- Single Lineup (Ajax Content) Page --
@login_required
def ajax_show_lineup_slider(request,admirer_id):
    me = request.user
    try:
        admirer_rel = me.crush_relationship_set_from_target.get(admirer_display_id=admirer_id)
    except CrushRelationship.DoesNotExist:
        return HttpResponse("Error: Could not find an admirer relationship for the lineup.")

    membership_set = admirer_rel.lineupmembership_set.all()
    
    # need to cleanse the lineup members each time the lineup is run 
    # reason: while lineup is not complete, user may have added one of the lineup member as either a crush or a platonic frined
        
    return render(request,'lineup.html',
                              {
                               'admirer_rel':admirer_rel,
                               'membership_set': membership_set,
                               'number_completed_members': len(membership_set.exclude(decision = None))})

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
        admirer_rel=me.crush_relationship_set_from_target.get(admirer_display_id=display_id)
        # if lineup is not paid for, then don't show any content beyond slide 2
        if admirer_rel.is_lineup_paid == False and int(lineup_position) > 1:
        #     print "lineup_position just before forbidden error: " + lineup_position
            return HttpResponseForbidden("Error: You cannot access this content until the lineup is paid for.")
    except CrushRelationship.DoesNotExist:
        print "Error: Could not find the admirer relationship."
        return HttpResponseNotFound("Error: Could not find the admirer relationship.")
    # obtain the actual user:
    try:   # obtain the user
        lineup_membership = admirer_rel.lineupmembership_set.get(position=lineup_position)
    except FacebookUser.DoesNotExist: 
        print ("Error: Could not find the lineup member data.")
        return HttpResponseNotFound("Error: Could not find the lineup member data.")
    lineup_count = len(admirer_rel.lineup_members.all())
    display_position=int(lineup_position) + 1;
    
    # build the basic elements
    # 1) name, photo, position info 
    ajax_response +='<div id="name">' + lineup_membership.lineup_member.first_name + ' ' + lineup_membership.lineup_member.last_name + '</div>'
    ajax_response +='<div id="mugshot" style="width:80px;height:80px"><img src="' + lineup_membership.lineup_member.get_facebook_picture() + '" height="80" width="10"></div>'
    ajax_response +='<div id="position_info"><span>member ' + str(display_position)  + ' out of ' + str(lineup_count) + '<span></div>'
    ajax_response +='<div id="facebook_link"><a href="http://www.facebook.com/' + lineup_membership.lineup_member.username + '" target="_blank">view facebook profile</a></div>'
    ajax_response +='<div id="decision" username="' + lineup_membership.lineup_member.username + '">'
    
    lineup_user=lineup_membership.lineup_member
    # check to see if there is an existing crush relationship or platonic relationship:
    if lineup_user in me.crush_targets.all():
        ajax_response += "<div id=\"choice\">You already added " + lineup_user.first_name + " " + lineup_user.last_name + " as a crush.</div>"
    elif lineup_user in me.just_friends_targets.all():
        ajax_response = "<div id=\"choice\">You already added " + lineup_user.first_name + " " + lineup_user.last_name + " as a platonic friend.</div>"
    else:    
        if lineup_membership.decision == None:
            ajax_response += '<a href="#" class="member_add" add_type="crush" username="' + lineup_membership.lineup_member.username + '" name="' + lineup_membership.lineup_member.first_name + ' ' + lineup_membership.lineup_member.last_name + '" lineup_position="' + lineup_position +  '">Add as crush</a>' 
            ajax_response += '<br><a href="#" class="member_add" add_type="platonic" username="' + lineup_membership.lineup_member.username + '" name="' + lineup_membership.lineup_member.first_name + ' ' + lineup_membership.lineup_member.last_name + '" lineup_position="' + lineup_position + '">Add as platonic friend</a>'        
       
        elif lineup_membership.decision == 0:
            ajax_response += '<div class="crush" id="choice" >"You added' + lineup_membership.lineup_member.first_name + ' ' + lineup_membership.lineup_member.last_name + ' as a crush!</div>'
        else:
            ajax_response += '<div class="platonic" id="choice">You added' + lineup_membership.lineup_member.first_name + ' ' + lineup_membership.lineup_member.last_name + ' as just-a-friend.</div>'   
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
            admirer_rel=request.user.crush_relationship_set_from_target.get(admirer_display_id=admirer_display_id)
        except CrushRelationship.DoesNotExist:
            return HttpResponse("Server Error: Could not add given lineup user")
        try:
            membership=admirer_rel.lineupmembership_set.get(lineup_member=target_user)
        except LineupMembership.DoesNotExist:
            print "could not find lineup member"
            return HttpResponse("Server Error: Could not add given lineup user")

        if membership.decision!=None:
            # something is wrong, this person was already decided upon, so just return an error message
            # check to see if they haven't already been added as a crush
            if membership.decision == 0:
                ajax_response = "<div id=\"choice\">You already added " + target_user.first_name + " " + target_user.last_name + " as a crush!</div>"
            else:
                ajax_response = "<div id=\"choice\">You already added " + target_user.first_name + " " + target_user.last_name + " as a platonic friend.</div>"
            return HttpResponse(ajax_response)
        if add_type=='crush':
            CrushRelationship.objects.create(source_person=request.user, target_person=target_user)
            ajax_response = '<div id="choice" class="crush">You added ' + target_user.first_name + ' ' + target_user.last_name + ' as a crush!</div>'
            membership.decision=0
        else:
            PlatonicRelationship.objects.create(source_person=request.user, target_person=target_user)
            ajax_response = '<div id="choice" class="platonic">You added ' + target_user.first_name + ' ' + target_user.last_name + ' as a platonic friend.</div>'
            membership.decision=1
        membership.save(update_fields=['decision'])
        if len(admirer_rel.lineupmembership_set.filter(decision=None)) == 0:
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
