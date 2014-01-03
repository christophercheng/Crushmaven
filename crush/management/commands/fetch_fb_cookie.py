'''
Created on Mar 19, 2013

This Scheduler Job Process calls update_fb_fetch_cookie whose main purpose is to find an updated xs cookie from the facebook account i.am.not.spam.i.swear@gmail.com.  This cookie is then set to cache where it can be used to fetch non-api facebook data.
 Recommend running once every 24 hours.

@author: Chris Work
'''



#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand
from crush.utils import update_fb_fetch_cookie

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  

        update_fb_fetch_cookie()
        