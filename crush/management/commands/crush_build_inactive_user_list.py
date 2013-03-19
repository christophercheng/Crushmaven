'''
Created on Mar 19, 2013

@author: Chris Work
'''

#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand

from crush.models.user_models import FacebookUser

class Command(NoArgsCommand):
    global all_inactive_user_list
    def handle_noargs(self, **options):
        global all_inactive_user_list
        
        all_inactive_user_list = FacebookUser.objects.filter(is_active=False).values_list('username',flat=True)#.only('target_person')