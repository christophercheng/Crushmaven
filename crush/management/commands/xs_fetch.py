'''
Created on Mar 19, 2013

This Scheduler Job Process should be run at least daily.  It grabs a fresh xs cookie so that the app can process FOF lineups.

@author: Chris Work
'''
#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand

import re
from crush.utils import fb_fetch,xs_fetch
from crush.utils_email import send_mailgun_email

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  
        xs=xs_fetch()
        print xs