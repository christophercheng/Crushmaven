'''
Created on Mar 19, 2013

This Scheduler Job Process sends exactly one email to any user who :
* has at least one uninvited crush
* does not have their notification settings for invite reminders turned off

@author: Chris Work
'''

#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand
from crush.utils import monthly_invite_reminder, notify_missed_crush_targets
from datetime import  datetime
import logging
logger = logging.getLogger(__name__)

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  
        if datetime.now().day == 1: 
            monthly_invite_reminder()
        notify_missed_crush_targets() #any crush targets who liked their admirer back, but their admirer never sees the result and thus triggers notification within a timeperiod
        return