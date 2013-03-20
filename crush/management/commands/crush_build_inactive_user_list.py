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

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  
        current_cache=cache.get('all_inactive_user_list',[])
        print "old cache has # elements: " + str(len(current_cache))
        all_inactive_user_list = FacebookUser.objects.filter(is_active=False).values_list('username',flat=True)#.only('target_person')

        cache.add('all_inactive_user_list',all_inactive_user_list)
        current_cache=cache.get('all_inactive_user_list')
        print "Updated cache's all_inactive_user_list with # elements: " + str(len(current_cache))