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
from crush.models.miscellaneous_models import InviteEmail
from django.db.models import Q
from crush.utils import graph_api_fetch
from crush.utils_email import send_mail_lineup_expiration_warning,send_mail_missed_invite_tip,send_mail_attraction_response_reminder,send_facebook_mail_mf_invite,send_mail_lineup_not_started,create_fb_mf_invite_tuple,create_fb_crush_invite_tuple,send_site_mass_mail
from crush.utils_fb_notifications import notify_person_on_facebook
from datetime import  datetime,timedelta

import logging
logger = logging.getLogger(__name__)

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  
        logger.debug("Running Daily Maintenance")

        auto_complete_expired_lineups()  # make sure this runs before daily email cadence program
        
        logger.debug("Running Daily Email Cadence Program")
        run_email_cadence_program()
        
        logger.debug("Running Expired Lineup Auto Completion Process")
        # for any lineup that has expired, auto set undecided lineup members to platonic

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
            try:
                PlatonicRelationship.objects.create(source_person=member.relationship.target_person, target_person=lineup_member_user,rating=1)
            except:
                pass

        relationship.date_lineup_finished=current_date
        relationship.lineup_auto_completed=True
        if relationship.target_status < 4:
            relationship.target_status=5 #set to platonic responded if not previously set to crush by user
        relationship.save(update_fields=['date_lineup_finished','lineup_auto_completed','target_status'])
    if relevant_relationships.count() == 0:
        logger.debug('no relationships to auto complete')
    return


# for every crush relationship have 4 new variables to track notifications:
    # 1: cadence_admirer_last_notified
    # 2: cadence_admirer_num_times_notified
    # 3: cadence_crush_last_notified
    # 4: cadence_crush_num_times_notified
# cadence_admirer variables get reset to None and 0 whenever:
    # a) crush responds and target status becomes crush_responded_platonic or crush_responded_crush (4 or 5)
# cadence_crush variables get reset to None and 0 whenever:
    # a) inactive crush signs up
    # b) active crush starts lineup

                

    
def run_email_cadence_program():
    try:
        
        logger.debug("EMAILING active admirers who haven't paid to see results of their responded crushes")
        active_crush_responded_cadence() #any crush targets who liked their admirer back, but their admirer never sees the result and thus triggers notification within a timeperiod
        
        logger.debug("emailing active crushes who haven't started their lineup")
        active_crush_nonstarted_lineup_cadence()  
    
        logger.debug("emailing active crushes who haven't completed their lineup")
        active_crush_incomplete_lineup_cadence()  
        
        logger.debug("EMAILING Admirers who did not invite their crush")
        admirer_not_invited_crush_cadence()
        
        logger.debug("emailing & FB messaging inactive crushes inviting them again")
        inactive_crush_invite_cadence()  
        
        logger.debug("FB messaging mutual friends of inactive crushes inviting them again")
        mf_of_inactive_crush_invite_cadence() 
        
    except Exception as e:
        logger.error("Daily Maintenance Failed with Exception: " + str(e))
    return True


# =========  Admirers who haven't invited their crush  =========
# email them whenever a new relationship has been created, and every 14 days after, for a maximum of 4 emails 
# (0,14,28,42)
# keep a variable called active admirer emails

def admirer_not_invited_crush_cadence():
    
    # gather all people who 1) have been notified less than 4 times and 2 ) haven't been notified within 14 days or not notified at all
    
    # create an empty list of source persons to notify
    notify_relationships=[]
    notify_persons=[] # temporary list of source persons
    # update any relationships' cadence variables
    update_relationships=[]
     
    # grab all crush relationships added in the last 24 hours that status is not_invited
    cutoff_date=datetime.now()-timedelta(days=14)
    
    relevant_relationships = CrushRelationship.objects.filter(Q(target_status=0),Q(cadence_admirer_num_sent__lt = 4) | Q(cadence_admirer_num_sent = None),Q(cadence_admirer_date_last_sent__lt = cutoff_date) | Q(cadence_admirer_date_last_sent = None))
    for relationship in relevant_relationships:
        source_person=relationship.source_person
        #source_person_email=source_person.email
        update_relationships.append(relationship)
        if source_person not in notify_persons:# and source_person_email != "":
            notify_persons.append(source_person)
            notify_relationships.append(relationship)
    for relationship in notify_relationships:
        try:
            if relationship.source_person.email!="":
                send_mail_missed_invite_tip(relationship)
            
            notify_person_username=relationship.source_person.username
            source_person_email=relationship.source_person.email
            email_type="other"
            if 'hotmail' in source_person_email or 'live.com' in source_person_email:
                email_type="hotmail"
            elif 'yahoo' in source_person_email:
                email_type="yahoo"
            destination_url="missed_invite_tip/" + notify_person_username + "/" + relationship.source_person.first_name + "/" + email_type + "/"
            message="You must email invite your crush - click here to get their email address from Facebook."
            notify_person_on_facebook(notify_person_username,destination_url,message)
        except Exception as e:
            logger.error("problem sending fb admirer not invited crush reminder with exception: " + str(e) + " to relationship: " + str(relationship))
        
    for relationship in update_relationships:
        num_sent = relationship.cadence_admirer_num_sent
        if num_sent==None:
            relationship.cadence_admirer_num_sent = 1
        else:
            relationship.cadence_admirer_num_sent = num_sent + 1
        relationship.cadence_admirer_date_last_sent = datetime.now()
        relationship.save(update_fields=['cadence_admirer_num_sent','cadence_admirer_date_last_sent'])
            
    logger.debug("Django Command: sent admirer cadence: " + str(len(notify_persons)) + " admirer missed invites!")
        

    return

# ======== Active Admirers who Haven't Paid to see their Crush Response yet ========


def active_crush_responded_cadence():  
    # grab all active admirers who have a crush relationship that has been responded (not results paid) and have been notified less than 4 times
        # don't grab crushes who liked their admirer back (they shouldn't be notified until either their original admirer pays for results, or the date_target_responded is in past)
    # gather all people who 1) have been notified less than 4 times and 2 ) haven't been notified within 14 days or not notified at all
    
    # create an empty list of source persons to notify
    notify_relationships=[]
    notify_persons=[] # temporary list of source persons
    # update any relationships' cadence variables
    update_relationships=[]
     
    # grab all crush relationships added in the last 24 hours that status is not_invited
    now = datetime.now()
    cutoff_date=now-timedelta(days=14)
    
    relevant_relationships = CrushRelationship.objects.filter(Q(target_status__gt=3),Q(is_results_paid=False),Q(date_target_responded__lt=now),Q(cadence_admirer_num_sent__lt = 4) | Q(cadence_admirer_num_sent = None),Q(cadence_admirer_date_last_sent__lt = cutoff_date) | Q(cadence_admirer_date_last_sent = None))
    for relationship in relevant_relationships:
        source_person=relationship.source_person
        #source_person_email=source_person.email
        update_relationships.append(relationship)
        if source_person not in notify_persons:# and source_person_email != "":
            notify_persons.append(source_person)
            notify_relationships.append(relationship)
    for relationship in notify_relationships:
        if relationship.source_person.email!="":
            send_mail_attraction_response_reminder(relationship)
        relationship.notify_source_person_on_facebook()
        
    for relationship in update_relationships:
        num_sent = relationship.cadence_admirer_num_sent
        if num_sent==None:
            relationship.cadence_admirer_num_sent = 1
        else:
            relationship.cadence_admirer_num_sent = num_sent + 1
        relationship.cadence_admirer_date_last_sent = datetime.now()
        relationship.save(update_fields=['cadence_admirer_num_sent','cadence_admirer_date_last_sent'])
            
    logger.debug("Django Command: sent admirer cadence: " + str(len(notify_persons)) + " crush responded!")   

    return

# =========  Inactive Crushes who haven't Signed up Yet =========
# send a facebook message invite to an inactive person immediately and every 14 days after (maximum 3 times)
    # if the inactive crush person also has at least one invite email associated with them, fire off an email as well
    # cadence_crush_num_sent should be set to 1 by transactional logic
# (0,14,28)
def inactive_crush_invite_cadence():
    # gather all ianctive crushes who 1) have been invited less than 3 times and 2) haven't been invited in last 14 days 
    # if there are any invite emails on file for them, email invite them too
    
    # if there are any phone numbers on file for them, text invite them too 
    notify_persons=[] # temporary list of source persons
    # update any relationships' cadence variables
     
    # grab all crush relationships added in the last 24 hours that status is not_invited
    now = datetime.now()
    update_relationships=[]
    cutoff_date=now-timedelta(days=14)
    mass_email_tuple=[]
    relevant_relationships = CrushRelationship.objects.filter(Q(target_status__lt=2),Q(cadence_crush_num_sent__lt = 3) | Q(cadence_crush_num_sent = None),Q(cadence_crush_date_last_sent__lt = cutoff_date) | Q(cadence_crush_date_last_sent = None))
    for relationship in relevant_relationships:
        target_person=relationship.target_person
        if target_person not in notify_persons:# and source_person_email != "":
            notify_persons.append(target_person)
            try:
                query_string=relationship.target_person.username + "?fields=username"
                data = graph_api_fetch('',query_string,False)
                fb_username=data['username'] 
                facebook_email_address=fb_username + "@facebook.com"
                mass_email_tuple.append(create_fb_crush_invite_tuple(relationship,facebook_email_address))
                logger.debug("adding inactive crush user to mass invite email list: " + str(target_person.get_name()))
                # update the cadence variables for this relationship
                update_relationships.append(relationship)

            except Exception as e:
                logger.error("Inactive FB invite Cadence Error: Couldn't get pretty username with exception: " + str(e) + " for relationship: " + str(relationship))
                pass
    
    # gather all invites_emails for crushes for relationships with inactive crush target and that haven't been sent out in more than 14 days and not sent more than 3 times
    remind_emails = InviteEmail.objects.filter(date_last_sent__lt=cutoff_date,is_for_crush=True,num_times_sent__lt=3,relationship__target_status__lt=2)
    
    for email in remind_emails:
        email.send()
    try:
            
        send_site_mass_mail(mass_email_tuple)
        for relationship in update_relationships:
            target_person = relationship.target_person
            all_target_relationships=CrushRelationship.objects.filter(target_person=target_person)
            for individual_target_relationship in all_target_relationships:
                num_sent = individual_target_relationship.cadence_crush_num_sent
                if num_sent==None:
                    individual_target_relationship.cadence_crush_num_sent = 1
                else:
                    individual_target_relationship.cadence_crush_num_sent = num_sent + 1
                individual_target_relationship.cadence_crush_date_last_sent = datetime.now()
                individual_target_relationship.save(update_fields=['cadence_crush_num_sent','cadence_crush_date_last_sent'])   
    except Exception as e:
        logger.error("Inactive FB invite Cadence Error: could not send out mass email for some reason : " + str(e))       

    logger.debug("Django Command: sent inactive crush cadence: " + str(len(mass_email_tuple)) + " crushes re-invited via facebook email!")   
    logger.debug("Django Command: sent inactive crush cadence: " + str(len(remind_emails)) + " crushes re-invited via invite email!")   
            
    return



def active_crush_invite_cadence():
    # this is not needed right now cause we're not at this point yet
    return True
# =========  Mutual Friends of Inactive Crushes who haven't Signed up Yet =========
# send facebook message to mutual friends of an inactive crush invite immediately and every 14 days after (maximum 2)
# (0, 14)

def mf_of_inactive_crush_invite_cadence():
    # grab all inactive crush relationships who have been invited less than 2 times and not within the last 14 days
    # grab all of their mutual friends ( with admirer)
    # send facebook message to all of them
    # grab all invite emails associated with mutual friends (who haven't been messaged more than twice, resend them a message
    
    # in the future check if the mutual friend is an app user, if so, send them a regular mf invite email
    # gather all ianctive crushes who 1) have been invited less than 3 times and 2) haven't been invited in last 14 days 
    # if there are any invite emails on file for them, email invite them too
    update_relationships=[]
    attempted_notifications=0
    # if there are any phone numbers on file for them, text invite them too 
    # update any relationships' cadence variables
    mass_email_tuple=[]
     
    # grab all crush relationships added in the last 24 hours that status is not_invited
    now = datetime.now()
    cutoff_date=now-timedelta(days=14)
    
    relevant_relationships = CrushRelationship.objects.filter(Q(target_status__lt=2),Q(cadence_mf_num_sent__lt = 2) | Q(cadence_mf_num_sent = None),Q(cadence_mf_date_last_sent__lt = cutoff_date) | Q(cadence_mf_date_last_sent = None))
    for relationship in relevant_relationships:
        source_person=relationship.source_person
        target_person=relationship.target_person
        
        # get list of all of the mutual friends
        fb_query_string = str(source_person.username + '/mutualfriends/' + target_person.username)
        at_least_one_mf_suceeded=False
        try:           
            mutual_friend_json = graph_api_fetch(source_person.access_token, fb_query_string)
            logger.debug("Succesfully got mutual friends for relationship: " + str(relationship))

            crush_full_name = target_person.get_name()
            for friend in mutual_friend_json:
                attempted_notifications+=1
                mf_username = friend['id']
                try:
                    friend_data=graph_api_fetch('',mf_username + "?fields=username",False)
                    facebook_email_address=friend_data['username'] + "@facebook.com"
                    mf_first_name = friend['name'].split(' ', 1)[0]              
                    if source_person.username not in ['100006341528806','1057460663','100004192844461','651900292','100003843122126','100007405598756']:    
                        mass_email_tuple.append(create_fb_mf_invite_tuple(facebook_email_address, mf_first_name, crush_full_name))
                    else:
                        logger.debug("sending facebook invite referral mail to mutual friend: " + str(mf_first_name) + " " + str(facebook_email_address) + " on behalf of " + str(crush_full_name))
                    at_least_one_mf_suceeded=True
                except Exception as e:
                    logger.error("Mutual Friend Cadence Error: Could not get pretty fb username for : " + str(friend))
                    pass
            
        except Exception as e:
            logger.error("Mutual Friend Cadence Error: Could not get mutual friends for relationship: " + str(relationship) + " with exception: " + str(e))
            pass
        if at_least_one_mf_suceeded:
            # update cadence variables
            update_relationships.append(relationship)

    
    # gather all invites_emails for mutual friends for relationships with inactive crush target and that haven't been sent out in more than 14 days and not sent more than 2 times
    remind_emails = InviteEmail.objects.filter(date_last_sent__lt=cutoff_date,is_for_crush=False,num_times_sent__lt=2,relationship__target_status__lt=2)
    
    for email in remind_emails:
        email.send()
    
    try:
        if len(mass_email_tuple) > 0:
            send_site_mass_mail(mass_email_tuple)    
            
        for relationship in update_relationships:
            num_sent = relationship.cadence_mf_num_sent
            if num_sent==None:
                relationship.cadence_mf_num_sent = 1
            else:
                relationship.cadence_mf_num_sent = num_sent + 1
            relationship.cadence_mf_date_last_sent = datetime.now()
            relationship.save(update_fields=['cadence_mf_num_sent','cadence_mf_date_last_sent'])      
    except Exception as e:
        logger.error("Mutual Friend Cadence Error: could not send out mass email for exception: " + str(e))     
            
    logger.debug("Django Command: sent MFs of inactive crush cadence: " + str(len(mass_email_tuple)) + " mutual friends messaged via facebook email out of " + str(attempted_notifications) + " attempted mf's")   
    logger.debug("Django Command: sent MFs of inactive crush cadence: " + str(len(remind_emails)) + " mutual friends messaged via direct email!")   
    return

# =========  Active Crushes who haven't completed the lineup yet =========

# send email and facebook message to active crush who hasn't started crush lineup immediately and every 14 days after (maximum 3)
def active_crush_nonstarted_lineup_cadence():
    # grab all active users who have been notified less than 3 times and who have not started a lineup
        # grab all relationships where the lineup has not been started
    # send both email and facebook notification
    notify_relationships=[]
    notify_persons=[] # temporary list of source persons
    # update any relationships' cadence variables
    update_relationships=[]
     
    # grab all crush relationships added in the last 24 hours that status is not_invited
    cutoff_date=datetime.now().date()-timedelta(days=14)
    
    relevant_relationships = CrushRelationship.objects.filter(Q(target_status=2),Q(cadence_crush_num_sent__lt = 2) | Q(cadence_crush_num_sent = None),Q(cadence_crush_date_last_sent__lt = cutoff_date) | Q(cadence_crush_date_last_sent = None))
    for relationship in relevant_relationships:
        target_person=relationship.target_person
        #source_person_email=source_person.email
        update_relationships.append(relationship)
        if target_person not in notify_persons:# and source_person_email != "":
            notify_persons.append(target_person)
            notify_relationships.append(relationship)
    for relationship in notify_relationships:
        email=target_person.email
        if email!="":
            send_mail_lineup_not_started(email)
        
        notify_person_username=target_person.username
        destination_url="lineup_not_started/"
        message="Your admirer, someone you know, is waiting for you to complete their lineup..."
        notify_person_on_facebook(notify_person_username,destination_url,message)
        
    for relationship in update_relationships:
        num_sent = relationship.cadence_crush_num_sent
        if num_sent==None:
            relationship.cadence_crush_num_sent = 1
        else:
            relationship.cadence_crush_num_sent = num_sent + 1
        relationship.cadence_crush_date_last_sent = datetime.now()
        relationship.save(update_fields=['cadence_crush_num_sent','cadence_crush_date_last_sent'])
            
    logger.debug("Django Command: sent crush cadence: " + str(len(notify_persons)) + " lineup not started reminders!")
        


# send email and facebook message to active crush who hasn't complete lineup a day before lineup expires
def active_crush_incomplete_lineup_cadence():
    current_date=datetime.now()
    day_from_now=current_date + timedelta(days=1)
    relevant_relationships=CrushRelationship.objects.filter(Q(date_lineup_finished=None,), Q(date_lineup_expires__lt=day_from_now),~Q(date_lineup_expires__lt=current_date))
    if relevant_relationships.count() == 0:
        logger.debug('no relationships to warn of lineup expiration')
    else: # get an access token to send facebook notifications
        for relationship in relevant_relationships:
            expiration_datetime=relationship.date_lineup_expires
            if relationship.target_person.bNotify_lineup_expiration_warning == False:
                continue
            email_address = relationship.target_person.email
            if email_address!='':
                send_mail_lineup_expiration_warning(email_address,expiration_datetime)
            notify_person_username = relationship.target_person.username
            destination_url = "lineup_expiration/" + str(relationship.target_person.username) + "/" + str(relationship.display_id) + "/"
            message="Your admirer's lineup is about to expire (on " + str(relationship.date_lineup_expires) + ") Afterward, undecided lineup members will default to 'Not Interested'"
            notify_person_on_facebook(notify_person_username,destination_url,message) 
            logger.debug("admirer lineup warning sent: " + str(relationship))

    return
