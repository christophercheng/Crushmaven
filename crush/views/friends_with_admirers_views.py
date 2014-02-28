from django.http import HttpResponse,HttpResponseNotAllowed
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from urllib2 import HTTPError
from crush.models import CrushRelationship
from datetime import datetime
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# -- Friends with Admirers Page --
@login_required
def friends_with_admirers(request):
    return render(request,'friends_with_admirers.html', {})

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
