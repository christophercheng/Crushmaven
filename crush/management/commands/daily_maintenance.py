'''
Created on Mar 19, 2013

This Scheduler Job Process sends exactly one email to any user who :
* has at least one uninvited crush
* does not have their notification settings for invite reminders turned off

@author: Chris Work
'''

#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand
from crush.models.user_models import FacebookUser
from crush.models.relationship_models import CrushRelationship,PlatonicRelationship
from django.db.models import Q
from django.db.models import Min
from crush.utils_email import send_mail_invite_reminder,send_mail_lineup_expiration_warning
from datetime import  datetime,timedelta
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
    
    
   
def monthly_invite_reminder():
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

# crush targets who like their admirer need to be notified eventually if their admirer doesn't view their response (which manually triggers notification)
def notify_missed_crush_targets():
    # go through and grab any crush relationships where the target_status is responded_crush and date_target_responded is in past AND the date_source_last_notified is empty
    current_date=datetime.now()
    relevant_relationships=CrushRelationship.objects.filter(target_status=4,date_target_responded__lt = current_date,date_source_last_notified=None,is_results_paid=False)
    for relationship in relevant_relationships:
        relationship.notify_source_person()
    # for each grabbed relationship 
        # call notify source person
        # update date_source_last_notified
    return

def lineup_expiration_warning():
    current_date=datetime.now() + timedelta(days=1)
    relevant_relationships=CrushRelationship.objects.filter(lineup_initialization_status=1,date_lineup_finished=None, date_lineup_expires__lt=current_date)
    for relationship in relevant_relationships:
        email_address = relationship.target_person.email
        if email_address!='':
            send_mail_lineup_expiration_warning(email_address,relationship.date_lineup_expires)
            logger.debug("admirer lineup warning sent: " + str(relationship))
    if relevant_relationships.count() == 0:
        logger.debug('no relationships to warn of lineup expiration')
    return
  
def auto_complete_expired_lineups():
    current_date=datetime.now()
    relevant_relationships=CrushRelationship.objects.filter(lineup_initialization_status=1,date_lineup_finished=None, date_lineup_expires__lt=current_date)
    for relationship in relevant_relationships:
        logger.debug("Auto complete this relationship: " + str(relationship))
        relevant_lineup_members= relationship.lineupmember_set.filter(decision=None)
        for member in relevant_lineup_members:
            updated_fields=[]
            lineup_member_user = member.user
            if lineup_member_user==None:
                lineup_member_user=FacebookUser.objects.find_or_create_user(member.username, member.relationship.target_person.access_token, False, fb_profile=None)
                # if the lineup member user was not found for whatever reason, then we need to modify the lineup and strip out this member
                if lineup_member_user == None:
                    continue
                member.user=lineup_member_user
                updated_fields.append('user')
            member.decision=1
            updated_fields.append('decision')
            member.save(update_fields=updated_fields)
            PlatonicRelationship.objects.create(source_person=member.relationship.target_person, target_person=lineup_member_user,rating=1)

        relationship.date_lineup_finished=current_date
        relationship.lineup_auto_completed=True
        relationship.save(update_fields=['date_lineup_finished','lineup_auto_completed'])
    if relevant_relationships.count() == 0:
        logger.debug('no relationships to auto complete')
    return
