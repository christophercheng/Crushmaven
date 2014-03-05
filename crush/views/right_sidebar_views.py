from django.http import HttpResponse,HttpResponseNotAllowed
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from urllib2 import HTTPError
from crush.models import CrushRelationship,FacebookUser
from datetime import datetime,timedelta
from django.core.cache import cache
from django.conf import settings
from django.db.models import Count
import random
# import the logging library
import logging


# Get an instance of a logger
logger = logging.getLogger(__name__)


# -- Friends with Admirers Section (Ajax Content) --
@login_required
def ajax_right_sidebar_content(request,remove_relation_type=None,remove_username=None):
    me = request.user
    
    if remove_username is not None:
        me.update_friends_with_admirers(remove_relation_type,remove_username)
    
    friends_with_admirer_data=get_friends_with_admirer_data(me)
    strangers_with_admirer_data=get_strangers_with_admirer_data(me)
    return render(request,"navigation_right.html",{'friends_with_admirer_data':friends_with_admirer_data,'strangers_with_admirer_data':strangers_with_admirer_data})


def get_friends_with_admirer_data(me):
    
    # update user's friends_with_admirer data if it hasn't been processed before or if it's been too long
    if  (me.processed_activated_friends_admirers):
            time_since_last_update = datetime.now() - me.processed_activated_friends_admirers 
            if time_since_last_update > timedelta(hours=settings.FRIENDS_WITH_ADMIRERS_SEARCH_DELAY):
                me.find_inactive_friends()
    else:
        me.find_inactive_friends()
    
    friends_with_admirers = me.friends_with_admirers.all().order_by('first_name')
    if friends_with_admirers.count() == 0:
        return None
    friends_with_admirer_data={}
    #calculate the data needed to populate the friends with admirer template
    for inactive_crush_friend in friends_with_admirers:
        all_admirers = CrushRelationship.objects.all_admirers(inactive_crush_friend)
        num_admirers = len(all_admirers)
        if num_admirers==0:
            continue # in this case, a user was added as a friend but then someone deleted them laster

        elapsed_days = (datetime.now() - all_admirers[num_admirers-1].date_added).days
        if elapsed_days==0:
            elapsed_days = "today"
        elif elapsed_days == 1:
            elapsed_days = "yesterday"
        elif elapsed_days > 60:
            elapsed_days = str(elapsed_days/30) + " months ago"
        elif elapsed_days > 30:
            elapsed_days = "1 month ago"
        else:
            elapsed_days = str(elapsed_days) + " days ago"
        admirer_data={}
        admirer_data['num_admirers']=num_admirers
        admirer_data['elapsed_time']=elapsed_days
        friends_with_admirer_data[inactive_crush_friend]=admirer_data
    return friends_with_admirer_data

def get_strangers_with_admirer_data(me):
    strangers_with_admirer_data={} # { user:{'num_admirers': num_admirers,'elapsed_time':elapsed_time}, ... } if process_right_sidebar==None: # friends-with-admirer section has been processed before and does not need to be processed
    all_invite_inactive_user_list = cache.get(settings.INVITE_INACTIVE_USER_CACHE_KEY)   
    if all_invite_inactive_user_list == None or len(all_invite_inactive_user_list) == 0:# for some reason there is not data in cache's inactive user list - most likely cause we're on development node
        return None # don't process this here
    if all_invite_inactive_user_list != None and len(all_invite_inactive_user_list) > 10:
        total_inactive_users=len(all_invite_inactive_user_list)
        # get 5 random index numbers to pull from list
        user_indices=[]
        count=0
        current_user_crush_targets = me.crush_targets.all()
        current_user_friends_with_admirers=me.friends_with_admirers.all()
        while (len(strangers_with_admirer_data) < 5 and count < 25):
            count=count+1
            temp_index = random.randint(0,total_inactive_users-1)
            if temp_index not in user_indices:
                user_indices.append(temp_index)
                try:
                    inactive_stranger = FacebookUser.objects.get(is_active=False,username=all_invite_inactive_user_list[temp_index])
                    # ensure that user with given username is not a crush of current user nor is a friend (with admirer)
                    if inactive_stranger not in current_user_crush_targets and inactive_stranger not in current_user_friends_with_admirers and me not in inactive_stranger.friends_that_invited_me.all():
                    
                        all_admirers = CrushRelationship.objects.all_admirers(inactive_stranger)
                        num_admirers = len(all_admirers)
                        if num_admirers==0:
                            continue # in this case, a user was added as a friend but then someone deleted them laster
                        elapsed_days = (datetime.now() - all_admirers[num_admirers-1].date_added).days
                        if elapsed_days==0:
                            elapsed_days = "today"
                        elif elapsed_days == 1:
                            elapsed_days = "yesterday"
                        elif elapsed_days > 60:
                            elapsed_days = str(elapsed_days/30) + " months ago"
                        elif elapsed_days > 30:
                            elapsed_days = "1 month ago"
                        else:
                            elapsed_days = str(elapsed_days) + " days ago"
                        admirer_data={}
                        admirer_data['num_admirers']=num_admirers
                        admirer_data['elapsed_time']=elapsed_days
                        strangers_with_admirer_data[inactive_stranger]=admirer_data
                except:
                    pass
    if len(strangers_with_admirer_data) > 0:
        return strangers_with_admirer_data
    else:
        return None

# -- Friends with Admirers Section (Ajax Content) --
@login_required
def ajax_friends_with_admirers_content(request,remove_username=None):

    me=request.user

    try:
        if remove_username is not None:
            me.update_friends_with_admirers(remove_username)
        else:
            me.find_inactive_friends()
    except HTTPError as e:
        if e.code==400:
            return HttpResponseNotAllowed(str(e))
    except Exception as e:
        print str(e)
        return HttpResponse('') # not key functionality, so don't do anything special
    me=request.user

    try:
        if remove_username is not None:
            me.update_friends_with_admirers(remove_username)
        else:
            me.find_inactive_friends()
    except HTTPError as e:
        if e.code==400:
            return HttpResponseNotAllowed(str(e))
    except Exception as e:
        print str(e)
        return HttpResponse('') # not key functionality, so don't do anything special
    

    friends_with_admirer_data={}
    #calculate the data needed to populate the friends with admirer template
    for inactive_crush_friend in me.friends_with_admirers.all().order_by('first_name'):
    #print "creating html for: " + inactive_crush_friend.username
   
        all_admirers = CrushRelationship.objects.all_admirers(inactive_crush_friend)
        num_admirers = len(all_admirers)
        if num_admirers==0:
            continue # in this case, a user was added as a friend but then someone deleted them laster

        elapsed_days = (datetime.now() - all_admirers[num_admirers-1].date_added).days
        if elapsed_days==0:
            elapsed_days = "today"
        elif elapsed_days == 1:
            elapsed_days = "yesterday"
        elif elapsed_days > 60:
            elapsed_days = str(elapsed_days/30) + " months ago"
        elif elapsed_days > 30:
            elapsed_days = "1 month ago"
        else:
            elapsed_days = str(elapsed_days) + " days ago"
        admirer_data={}
        admirer_data['num_admirers']=num_admirers
        admirer_data['elapsed_time']=elapsed_days
        friends_with_admirer_data[inactive_crush_friend]=admirer_data
        
    return render(request,"navigation_right_admired_friends.html",{'friends_with_admirer_data':friends_with_admirer_data})



