'''
Created on Mar 19, 2013

This Scheduler Job Process sends exactly one email to any user who :
* has at least one uninvited crush
* does not have their notification settings for invite reminders turned off

@author: Chris Work
'''

#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand
from crush.utils import monthly_invite_reminder, notify_missed_crush_targets, lineup_expiration_warning, auto_complete_expired_lineups
from datetime import  datetime
import logging
logger = logging.getLogger(__name__)

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  
        logger.debug("Running Daily Maintenance")
        if datetime.now().day == 1: 
            logger.debug("Running Monthly Invite Maintenance")
            monthly_invite_reminder()
        logger.debug("Running Notifications for Crush Targets Who Weren't Previously Notified")
        notify_missed_crush_targets() #any crush targets who liked their admirer back, but their admirer never sees the result and thus triggers notification within a timeperiod
        logger.debug("Running Lineup Expiration Warning Notifications")
        lineup_expiration_warning() # send warning email to crush targets that their lineup is about to expire
        logger.debug("Running Expired Lineup Auto Completion Process")
        auto_complete_expired_lineups() # for any lineup that has expired, auto set undecided lineup members to platonic
        return