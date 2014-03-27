'''
Created on Mar 19, 2013

This Scheduler Job Process calls update_fb_fetch_cookie whose main purpose is to find an updated xs cookie from the facebook account i.am.not.spam.i.swear@gmail.com.  This cookie is then set to cache where it can be used to fetch non-api facebook data.
 Recommend running once every 24 hours.

@author: Chris Work
'''



#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand

from crush.models.user_models import FacebookUser
import logging,os,time,datetime
from datetime import timedelta
from selenium import webdriver
# Get an instance of a logger
logger = logging.getLogger(__name__)
from django.db.models import Q

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  
        logger.debug ("Running Phone Invite Cadence")
        try:       
            driver = webdriver.PhantomJS()
        except Exception as e:
            logger.error( "not able to get phantom driver to send out phone invites.  exception: " + str(e))
            return
        driver.get('http://voice.google.com')
        username = "chris@crushmaven.com"
        password = "carmelwdc3141"
        time.sleep(5)
        driver.find_element_by_id("Email").send_keys(username)
        driver.find_element_by_id("Passwd").send_keys(password)
        driver.find_element_by_id("signIn").click()
        time.sleep(5)

        cutoff_date=datetime.datetime.now()-timedelta(days=14)
        phone_users = FacebookUser.objects.filter(~Q(phone=None),Q(date_phone_invite_last_sent=None) | Q(date_phone_invite_last_sent__lt=cutoff_date), Q(num_times_phone_invite_sent__lt=2) | Q(num_times_phone_invite_sent=None ))
        num_invites_sent = 0
        for phone_user in phone_users:
            # click on text button
            try:
                number=phone_user.phone
                message = "Hi, " + phone_user.first_name + ", your friend gave us your number to find out (anonymously) if you're mutually attracted to them.  Please visit www.crushmaven.com to learn more..."

                driver.find_element_by_css_selector('.actionButtonSection div:nth-child(2)').click()
                logger.debug("clicked on text button")

                # enter phone number
                driver.find_element_by_id('gc-quicksms-number').send_keys(number)
                logger.debug("sent number")
                # enter message
                driver.find_element_by_id('gc-quicksms-text2').send_keys(message)
                logger.debug("sent message")

                # click send button
                driver.find_element_by_id('gc-quicksms-send2').click()
                
                # update phone last updated button
                phone_user.date_phone_invite_last_sent=datetime.datetime.now()
                num_times_sent = phone_user.num_times_phone_invite_sent
                phone_user.num_times_phone_invite_sent = num_times_sent + 1
                phone_user.save(update_fields=['date_phone_invite_last_sent','num_times_phone_invite_sent'])
                num_invites_sent=num_invites_sent+1
                time.sleep(5)
            except Exception as e:
                logger.error("Could not send invite to phone: " + number + " because of exception: " + str(e))
                pass
            logger.debug("Completed Phone Invite Cadence: " + str(num_invites_sent) + " phone invites sent...")
   
        driver.close()
 