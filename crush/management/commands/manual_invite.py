'''
Created on Mar 19, 2013

This Scheduler Job Process manually fires off email invites to any stored invitation emails that haven't yet been sent.
this is used when the administartor manually enters an email invite.  email invites that don't have a date_invite_last_sent field  (set to None) are the ones that are relevant.

@author: Chris Work
'''

#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand
from crush.models.miscellaneous_models import InviteEmail
from datetime import  datetime
import logging
logger = logging.getLogger(__name__)

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  
        logger.debug("Running Manual Invites")
        relevant_invites = InviteEmail.objects.filter(date_last_sent=None)
        for invite in relevant_invites:
            invite.send()
            invite.relationship.date_invite_last_sent = datetime.now()
            invite.relationship.save(update_fields=['date_invite_last_sent'])
        return
    