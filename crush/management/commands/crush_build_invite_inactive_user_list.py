'''
Created on Mar 19, 2013

This Scheduler Job Process is not theoretically necessary.  The inactive user list is constantly being updated (items removed and added) by the find_or_create FacebookUser Manager function.  
However, if the cache ever gets out of whack for some odd reason, this command will help to rest the state of things.  Recommend running once every 24 hours.

@author: Chris Work
'''



#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand
from django.core.cache import cache
from crush.models.user_models import FacebookUser
from django.conf import settings
from crush.utils import user_can_be_messaged
from django.db.models import Count
# to allow app to run in facebook canvas without csrf error:
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  

        inactive_crushes = FacebookUser.objects.filter(is_active=False).annotate(num_admirers=Count('admirer_set')).filter(num_admirers__gt=0)
        if settings.SEND_NOTIFICATIONS==False:
            magic_cookie='147%3At-_nYdmJgC5hxw%3A2%3A1394001634%3A15839'
        else:
            magic_cookie=cache.get(settings.FB_FETCH_COOKIE,'')
        if magic_cookie=='':
            logger.error("Problem with magic cookie")
        all_invite_inactive_crush_list=[]
        logger.debug("reseting the invite inactive crush list")
        count=0
        for inactive_user in inactive_crushes:
            inactive_username=inactive_user.username
            if user_can_be_messaged(magic_cookie,inactive_username):
                all_invite_inactive_crush_list.append(inactive_username)
                logger.debug(str(count) + ": adding " + str(inactive_username) + " to invite cache")
            else:
                logger.debug(str(count) + ": excluding " + str(inactive_username) + " to invite cache")
        logger.debug("new invite inactive crush list has total members: " + str(len(all_invite_inactive_crush_list)))
    
        cache.set(settings.INVITE_INACTIVE_USER_CACHE_KEY,all_invite_inactive_crush_list)