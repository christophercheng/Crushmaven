'''
Created on Mar 19, 2013

This Scheduler Job Process sends exactly one email to any user who :
* has at least one uninvited crush
* does not have their notification settings for invite reminders turned off

@author: Chris Work
'''

#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand
from crush.utils_email import send_mail_invite_reminder

from crush.models import FacebookUser
from django.db.models import Q
from django.db.models import Min
from datetime import  datetime
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  
        if datetime.now().day != 1: 
            logger.debug("skipping the invite reminder cause it's not first of month")
            return
        relevant_user_set = FacebookUser.objects.filter( Q(Q(is_active=True),~Q(crush_targets=None)) ).annotate(min_crush_status=Min('crush_crushrelationship_set_from_source__target_status')).filter(min_crush_status=0)
        invite_sent_count=0
        for user in relevant_user_set:
            if user.email == '' or user.bNotify_crush_signup_reminder == False:
                continue
            crush_list=[]
            more_crushes_count=0
            # get all crush relationships for this user
            relevant_crush_list=user.crush_crushrelationship_set_from_source.filter(target_status__lt=1)[:5]
            for relevant_crush in relevant_crush_list:
                crush_list.append(relevant_crush.target_person.get_name())
            if len(relevant_crush_list)>4: # calculate number of other relationships
                more_crushes_count = user.crush_crushrelationship_set_from_source.filter(target_status__lt=1).count() - 5

            send_mail_invite_reminder(user.first_name, user.email, crush_list, more_crushes_count)
            invite_sent_count+=1
        logger.debug("Django Command: sent " + str(invite_sent_count) + " email invite reminders out!")
        return