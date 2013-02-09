from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from crush.models import CrushRelationship,PlatonicRelationship,LineupMember,FacebookUser
import datetime
import urllib,json
#from multiprocessing import Pool
from django.http import HttpResponseNotFound,HttpResponseForbidden
import time,random

# -- Admirer List Page --
@login_required
def admirers(request,show_lineup=None):

    me = request.user 
    progressing_admirer_relationships = CrushRelationship.objects.progressing_admirers(me)
    past_admirers_count = CrushRelationship.objects.past_admirers(me).count()
    
    # initialize the lineups of any new admirer relationships
        # filter out the new relationships whose lineup member 1 is empty
    
    #uninitialized_relationships = progressing_admirer_relationships.exclude(lineup_initialization_status=1) #get all relationships that don't already have a lineup (number of lineump members is zero)
    #if (uninitialized_relationships):
    #    print "hey, found an uninitialized relationship"
    #    pool=Pool(1) #must be 1 or things go bad!
    #    for relationship in uninitialized_relationships:
    #        pool.apply_async(LineupMembership.objects.initialize_lineup,[relationship]) #initialize lineup asynchronously
            #LineupMembership.objects.initialize_lineup(relationship)

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
    try:    
        relationship = CrushRelationship.objects.all_admirers(request.user).get(admirer_display_id=int_display_id)
    except CrushRelationship.DoesNotExist:
        ajax_response += '* ' + settings.LINEUP_STATUS_CHOICES[4] + '<button id="initialize_lineup_btn">Re-initialize</button>'
        return HttpResponse(ajax_response) # this is a catch all error return state
    if relationship.lineup_initialization_status == None or relationship.lineup_initialization_status > 3:
        relationship.lineup_initialization_status = 0
        relationship.save(update_fields=['lineup_initialization_status'])
        LineupMember.objects.initialize_lineup(relationship) 
    if relationship.lineup_initialization_status == 0:       
        # wait for a certain amount of time before returning a response
        counter = 0
        while True: # this loop handles condition where user is annoyingly refreshing the admirer page while the initialization is in progress
            print "trying admirer lineup initialization for " + relationship.target_person.last_name + ":" + display_id + " on try: " + str(counter) 
           
            if relationship.lineup_initialization_status > 0: # initialization was either a success or failed
                break
            elif counter==25: # if 30 seconds have passed then give up
                print "giving up on admirer:" + str(display_id)
                relationship.lineup_initialization_status = 5
                relationship.save(update_fields=['lineup_initialization_status'])
                break
            time.sleep(1) # wait a quarter second
            counter+=1

    if relationship.lineup_initialization_status > 3: # for data fetching errors show a button that allows user to restart the initialization 
        ajax_response += '* ' + settings.LINEUP_STATUS_CHOICES[relationship.lineup_initialization_status] + ' <button id="initialize_lineup_btn" display_id="' + display_id + '">Re-initialize</button>'
        return HttpResponse(ajax_response)
    if relationship.lineup_initialization_status > 1: # show error message
        ajax_response += '* ' + settings.LINEUP_STATUS_CHOICES[relationship.lineup_initialization_status]
        return HttpResponse(ajax_response)

    return render(request,'lineup_block.html', {'relationship':relationship})


# returns json:
    # 1st element: 'status': 0 or 1
# if status = 1, then no client side initialization needed, redirect to lineup page
# if status = 0, then proceed with client side initializatin using the next two element dictionaries
    # 2nd element (if status = 0) dictionary of mutual friend id : friend count
    # 3rd element (if status = 0) dictionary of admirer friend id : friend count

@login_required
def ajax_try_fof_initialization(request,display_id):

    try:
        relationship = CrushRelationship.objects.all_admirers(request.user).get(admirer_display_id=display_id)
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound()
    exclude_id_array=LineupMember.objects.get_exclude_id_array(relationship)
    exclude_id_string=LineupMember.objects.comma_delimit_list(exclude_id_array)
    post_dict = {};
    post_dict['access_token'] = request.user.access_token
    crush_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM+user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=' + request.user.username + ' AND NOT (uid2 IN (' + exclude_id_string + ')))"}'
    crush_app_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=' + request.user.username + ' AND NOT (uid2 IN (' + exclude_id_string + '))) AND is_app_user"}'
    mutual_friend_id_dict='{"method":"GET","name":"mutual-friends","relative_url":"' + request.user.username +'/mutualfriends/' + relationship.source_person.username + '"}'
    mutual_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM user WHERE uid IN ({result=mutual-friends:$.data.*.id}) AND NOT (uid IN (' + exclude_id_string + '))"}'
    mutual_app_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM user WHERE uid IN ({result=mutual-friends:$.data.*.id}) AND NOT (uid IN (' + exclude_id_string + ')) AND is_app_user"}'
    
    post_dict['batch'] = '[' + mutual_friend_id_dict + ',' + mutual_friend_dict + ',' + mutual_app_friend_dict + ',' + crush_friend_dict + ',' + crush_app_friend_dict  + ']'
    post_dict=urllib.urlencode(post_dict)    
    url='https://graph.facebook.com'
    
    num_fetch_tries=0 # try to grab data from facebook two times if necessary. sometimes it does not return data
    
    while (num_fetch_tries < 2):    
        fb_result = urllib.urlopen(url,post_dict)
        fb_result = json.load(fb_result)
    
        mutual_app_friend_array=[]
        crush_app_friend_array=[]
    
        if 'body' in fb_result[2] and 'data' in fb_result[2][u'body']:
            mutual_app_friend_array=json.loads(fb_result[2][u'body'])['data']
            random.shuffle(mutual_app_friend_array)
            num_fetch_tries=2
        if 'body' in fb_result[4] and 'data' in fb_result[4][u'body']:
            crush_app_friend_array=json.loads(fb_result[4][u'body'])['data']
            random.shuffle(crush_app_friend_array)
            num_fetch_tries=2
        num_fetch_tries+=1
        
    
    response_data={}
    response_data['success']=1
    if try_mf_initialization(mutual_app_friend_array,exclude_id_string,relationship)==False:
        if try_cf_initialization(crush_app_friend_array,exclude_id_string,relationship)==False:
            response_data['success']=0
            
            mutual_friend_array=[]
            crush_friend_array=[]
            if 'body' in fb_result[3] and 'data' in fb_result[3][u'body']:          
                crush_friend_array=json.loads(fb_result[3][u'body'])['data']
                random.shuffle(crush_friend_array)
            if 'body' in fb_result[1] and 'data' in fb_result[1][u'body']:
                mutual_friend_array=json.loads(fb_result[1][u'body'])['data']
                random.shuffle(mutual_friend_array)
            response_data['mutual_friend_array']=mutual_friend_array
            response_data['crush_friend_array']=crush_friend_array
            response_data['exclude_id_string']=exclude_id_string

    return HttpResponse(json.dumps(response_data),content_type="application/json")

# try to initialize lineup with 9 friends from a single mutual friend
# called by ajax_try_fof_initialization
def try_mf_initialization(mutual_app_friend_array,exclude_id_string,relationship):
    for mutual_friend in mutual_app_friend_array:
        if mutual_friend['friend_count'] <settings.MINIMUM_LINEUP_MEMBERS:
            continue
        # grab all friends of mutual app with admirer sex, friend sorted by friend count - via graph api
        fql_query = 'SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1=' + str(mutual_friend['uid']) + ' AND NOT (uid2 IN (' + exclude_id_string + ')))) AND sex = "' + relationship.source_person.get_fb_gender() + '" ORDER BY friend_count DESC LIMIT ' + str(settings.IDEAL_LINEUP_MEMBERS)
        fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,relationship.target_person.access_token))
        fql_query_results=json.load(fql_query_results)
        print fql_query_results
        fql_query_results = fql_query_results['data'] 
        # if less than minimum lineup members, go on to next mutual friend
        if len(fql_query_results) < settings.MINIMUM_LINEUP_MEMBERS:
            continue 
        acceptable_id_array=[]
        for result in fql_query_results:
            acceptable_id_array.append(result['uid'])
        # else add to lineup id array and setup in lineup
        LineupMember.objects.create_lineup(relationship,acceptable_id_array)
        return True
    # if for loop ended without returning, then return False cause no lineup was created
    return False

# try to initialize lineup with 9 friends from 9 separate crush friends
# called by ajax_try_fof_initialization
def try_cf_initialization(crush_app_friend_array,exclude_id_string,relationship):
    if len(crush_app_friend_array) < settings.MINIMUM_LINEUP_MEMBERS:
        return False
    acceptable_id_array=[]
    # iterate through all crush app friends
    for friend in crush_app_friend_array:
        # get each crush app friend's friends sorted by friend_count and filtered by gender & exclude id list - limit result to 1
        fql_query = 'SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1=' + str(friend['uid']) + ' AND NOT (uid2 IN (' + exclude_id_string + ')))) AND sex = "' + relationship.source_person.get_fb_gender() + '" ORDER BY friend_count DESC LIMIT 1'
        fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,relationship.target_person.access_token))
        fql_query_results=json.load(fql_query_results)
        fql_query_results = fql_query_results['data'] 
        # if result < 0 skip rest of loop
        if len(fql_query_results) == 0:
            continue
        # else grab the result and add to acceptable id_array
        acceptable_id_array.append(fql_query_results[0]['uid'])
        exclude_id_string = exclude_id_string + ',' + fql_query_results[0]['uid']
        # if acceptable id_array length == ideal lineup members then break out of loop entirely
        if len(acceptable_id_array) >= settings.IDEAL_LINEUP_MEMBERS:
            break
    # after loop, count the acceptable id_array_length, if greater than minimum lineup member setting, then call create_lineup
    if len(acceptable_id_array) >= settings.MINIMUM_LINEUP_MEMBERS:
        LineupMember.objects.create_lineup(relationship,acceptable_id_array)
        return True
    return False
    
# called when an client side initialization of friend-of-friend admirer starts
@login_required
def ajax_get_mutual_friends(request,display_id):
    print "HEY"
    try:
        relationship = CrushRelationship.objects.all_admirers(request.user).get(admirer_display_id=display_id)
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound()
    url='https://graph.facebook.com/' + request.user.username + '/mutualfriends/' + relationship.source_person.username + '/?access_token=%s' % request.user.access_token
    print url
    friend_profile = urllib.urlopen(url)
    friend_profile = json.load(friend_profile)
    friendlist=[]
    if len(friend_profile['data'])>0:
        for friend in friend_profile['data']:
            friendlist.append(friend['id'])
    return HttpResponse(json.dumps(friendlist),content_type="application/json")

# called when an client side initialization of friend-of-friend admirer fails
@login_required
def ajax_update_lineup_status(request,display_id,status):
    try:
            admirer_rel=CrushRelationship.objects.all_admirers(request.user).get(admirer_display_id=display_id)
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound(settings.LINEUP_STATUS_CHOICES[5])
    admirer_rel.lineup_initialization_status=int(status)
    admirer_rel.save(update_fields=['lineup_initialization_status'])
    return HttpResponse(settings.LINEUP_STATUS_CHOICES[int(status)])

# called when an client side initialization of friend-of-friend successfully completes
@login_required
def ajax_post_lineup(request,display_id):
    try:
        admirer_rel=CrushRelationship.objects.all_admirers(request.user).get(admirer_display_id=display_id)
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound(settings.LINEUP_STATUS_CHOICES[5])
    post_data = request.POST
    # if by chance there was an existing set of lineup members, clear them out first
    if admirer_rel.lineupmember_set.count>0:
        for member in admirer_rel.lineupmember_set.all():
            member.delete()
    # determine where admirer should go
    random_end = len(post_data) - 2 # -1 for csrf token -1 so we are not put at end of list
    admirer_position=random.randint(0, random_end) # normally len(data) should be 9
    lineup_position=0;
    for key in post_data:
        if key=="csrfmiddlewaretoken":
            continue
        if lineup_position==admirer_position:
            LineupMember.objects.create(relationship=admirer_rel,username=admirer_rel.source_person.username,position=lineup_position)
            lineup_position=lineup_position+1
            LineupMember.objects.create(relationship=admirer_rel,username=post_data[key],position=lineup_position)
        else:
            LineupMember.objects.create(relationship=admirer_rel,username=post_data[key],position=lineup_position)
        lineup_position=lineup_position+1
    # set initialization status
    admirer_rel.lineup_initialization_status=1
    admirer_rel.save(update_fields=['lineup_initialization_status'])
    return HttpResponse()
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
    elif lineup_member in me.just_friends_targets.all():
        ajax_response = "<div id=\"choice\">You already decided: Not Interested in " + lineup_member_user.first_name + " " + lineup_member_user.last_name + "</div>"
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
