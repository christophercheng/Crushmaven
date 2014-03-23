from django.template.loader import render_to_string
#from crush.models.user_models import FacebookUser
from django.conf import settings
import requests
import os,time
import itertools
from django.core.mail import send_mail, send_mass_mail

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

CDN_URL = os.getenv('CDN_SUMO_URL')
STATIC_URL = 'http://' + str(CDN_URL) + '/static/'
    
def mygrouper(n, iterable):
    args = [iter(iterable)] * n
    return ([e for e in t if e != None] for t in itertools.izip_longest(*args))    
    
def send_site_mass_mail(mail_tuple):
    logger.debug("Sending Mass emails (" + str(len(mail_tuple)) + ")")
    
    if len(mail_tuple) < 20:
        for individual_tuple in mail_tuple:
            logger.debug(" - " + str(individual_tuple[3]))
    
    if settings.SEND_NOTIFICATIONS==False:
        return
    # don't send more than 100 at a time, 
    grouped_mail_tuple=mygrouper(100,mail_tuple)
    logger.debug("Mass Email Send: broke into groups of 100")
    num_groups_sent=0
    try:
        for group in grouped_mail_tuple:
            send_mass_mail(group)
            num_groups_sent+=1
            logger.debug("sent out group: " + str(num_groups_sent))
            time.sleep(3)
    except Exception as e:
        logger.error("Mass Email Failed after sending " + str(num_groups_sent) + " groups of 100 emails 3 seconds apart")
        raise e
    
def send_mailgun_email(from_string, email_address,subject,html_message,text_message='',send_time=None):
        logger.debug("sending mail from :" + from_string + " to: " + email_address + " with subject: " + subject)

        if settings.SEND_NOTIFICATIONS==False:
            return
        try:
            data_dict={"from": from_string,\
                          "to": email_address,"subject": subject, "html": html_message, "text": text_message}
#            data_dict={"from": from_string,\
#                           "to": email_address,"subject": subject, "html":html_message}
            if send_time != None:
                data_dict["o:deliverytime"]=str(send_time) 
            #logger.debug(str(data_dict))
            result= requests.post("https://api.mailgun.net/v2/crushmaven.com/messages",auth=("api", settings.MAILGUN_API_KEY),data=data_dict)
            logger.debug( "MailGun Response: " + str(result))
        
        except Exception as e:
            print "MAIL PROBLEM! " + str(type(e)) + " : " + str(e)

def send_mail_user_bought_credit(user, credit_total):
    if settings.SEND_NOTIFICATIONS==False:
        return
    if user.username not in ['100006341528806','1057460663','100004192844461','651900292','100003843122126','100007405598756']:
        message = user.get_name() + ' bought ' + str(credit_total) + ' credits!'
        send_mail(message,'YAY!', 'admin@crushmaven.com',['admin@crushmaven.com'])
        send_mail('',message, 'admin@crushmaven.com',['6465732737@vmobl.com'])
   

def send_mail_user_logged_in(user, header_string):
    if settings.SEND_NOTIFICATIONS==False:
        return
    if user.username not in ['100006341528806','1057460663','100004192844461','651900292','100003843122126','100007405598756']:
        message = 'http://www.facebook.com/' + str(user.username) + " " + header_string
        send_mail(user.get_name() + ' logged in!',message, 'admin@crushmaven.com',['admin@crushmaven.com'])
        send_mail('',user.get_name() + ' logged in! http://www.facebook.com/' + str(user.username), 'admin@crushmaven.com',['6465732737@vmobl.com'])
        
def send_mail_verify_email(user):
    email_address=user.email
    first_name=user.first_name
    username=user.username
    html=render_to_string('email_template_verify_email.html',{'first_name':first_name,'username':username,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_verify_email_text.html',{'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven <notifications@crushmaven.com>',email_address,'Please verify your email address',html,text)
            
def send_mail_crush_invite(friendship_type,full_name, short_name, first_name,email_address,recipient_fb_username=None):
    html=render_to_string('email_template_crush_invite.html',{'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name,'STATIC_URL':STATIC_URL,'recipient_fb_username':recipient_fb_username})
    text=render_to_string('email_template_crush_invite_text.html',{'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name,'STATIC_URL':STATIC_URL})

    if friendship_type == 0:
        send_mailgun_email('CrushMaven Notifications <notifications@crushmaven.com>',email_address,full_name + ', your friend on Facebook added you to their crush list',html,text)
    elif friendship_type == 1:
        send_mailgun_email('CrushMaven Notifications <notifications@crushmaven.com>',email_address,full_name + ', a friend-of-a-friend on Facebook added you to their crush list',html,text)
    else:
        send_mailgun_email('CrushMaven Notifications <notifications@crushmaven.com>',email_address,full_name + ', someone you may know added you to their crush list',html,text)
    
def send_facebook_mail_crush_invite(facebook_email_address,friendship_type,first_name):        # get the facebook username from the facebook uid
    logger.debug("sending facebook crush invite to email: " + facebook_email_address)

    if settings.SEND_NOTIFICATIONS==False:
        return
    message= first_name + ", a Facebook friend of yours added you as their crush."
    if friendship_type==1:
        message = first_name + ", a Facebook friend-of-a-friend added you as their crush."
    elif friendship_type == 2:
        message = first_name + ", one of our users - someone you may know - added you as their crush."
    message += "\r\n\r\nVisit https://apps.facebook.com/crushmaven to learn more.\r\n\r\nCrushMaven is the new matchmaking service that discovers anonymously if the person you're attracted to feels the same - or why they don't."
    send_mail('', message, 'notifications@crushmaven.com',[facebook_email_address])

def create_fb_crush_invite_tuple(relationship,facebook_email_address):
    crush_user= relationship.target_person
    crush_friendship_type=relationship.friendship_type
    crush_first_name = crush_user.first_name
    if crush_first_name == "":
        crush_first_name = facebook_email_address
        
    message= crush_first_name + ", a Facebook friend of yours added you as their crush."
    if crush_friendship_type==1:
        message = crush_first_name + ", a Facebook friend-of-a-friend added you as their crush."
    elif crush_friendship_type == 2:
        message = crush_first_name + ", one of our users - someone you may know - added you as their crush."
    message += "\r\n\r\nVisit https://apps.facebook.com/crushmaven to learn more.\r\n\r\nCrushMaven is the new matchmaking service that discovers anonymously if the person you're attracted to feels the same - or why they don't."
    data=['',message,'notifications_crushmaven.com',[facebook_email_address]]
    return data
        
def create_fb_mf_invite_tuple(facebook_email_address, mf_first_name, crush_full_name, fake_send=False):
    data_tuple=[]
    message= mf_first_name + ", your friend, " + crush_full_name + ", has a secret admirer (one of their friends).  Would you help us let them know?"

    message += "\r\n\r\nVisit https://apps.facebook.com/crushmaven to learn more.\r\n\r\nCrushMaven is the new matchmaking service that discovers anonymously if the person you're attracted to feels the same - or why they don't."
    
    return ['', message, 'notifications@crushmaven.com',[facebook_email_address]]
    
    
def send_facebook_mail_mf_invite(facebook_email_address, mf_first_name, crush_full_name, fake_send=False):        # get the facebook username from the facebook uid
    logger.debug("sending facebook invite referral mail to mutual friend: " + str(mf_first_name) + " " + str(facebook_email_address) + " on behalf of " + str(crush_full_name))
 
    if settings.SEND_NOTIFICATIONS==False or fake_send==True:
        return
    message= mf_first_name + ", your friend, " + crush_full_name + ", has a secret admirer (one of their friends).  Would you help us let them know?"

    message += "\r\n\r\nVisit https://apps.facebook.com/crushmaven to learn more.\r\n\r\nCrushMaven is the new matchmaking service that discovers anonymously if the person you're attracted to feels the same - or why they don't."
    send_mail('', message, 'notifications@crushmaven.com',[facebook_email_address])


def send_mail_mf_invite(full_name,short_name,first_name,crush_pronoun_subject,crush_pronoun_possessive, email_address,recipient_first_name = '',recipient_fb_username=''):
    html=render_to_string('email_template_mf_invite.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':crush_pronoun_subject,'pronoun_possessive':crush_pronoun_possessive,'STATIC_URL':STATIC_URL,'recipient_first_name':recipient_first_name,'recipient_fb_username':recipient_fb_username})
    text=render_to_string('email_template_mf_invite_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':crush_pronoun_subject,'pronoun_possessive':crush_pronoun_possessive,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven <notifications@crushmaven.com>',email_address,"Can you help up reach your friend, " + full_name + "?",html,text)

def send_mail_new_admirer(friendship_type,full_name, short_name, first_name,email_address):
    html=render_to_string('email_template_notify_new_admirer.html',{'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_new_admirer_text.html',{'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven <notifications@crushmaven.com>',email_address,short_name + ', you have a new admirer!',html,text)
    
def send_mail_new_attraction_response(full_name, short_name, first_name,pronoun_subject,pronoun_possessive,email_address,send_time=None):
    html=render_to_string('email_template_notify_new_attraction_response.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_new_attraction_response_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven <notifications@crushmaven.com>',email_address,short_name + ' responded to your crush!',html,text,send_time)

def send_mail_attraction_response_reminder(relationship):
    source_person=relationship.source_person
    source_person_email=source_person.email
    target_person=relationship.target_person
    full_name = target_person.first_name + " " + target_person.last_name
    short_name = target_person.first_name + " " + target_person.last_name[0]
    first_name = target_person.first_name
    pronoun_subject = target_person.get_gender_pronoun_subject()
    pronoun_possessive = target_person.get_gender_pronoun_possessive()    
    send_mail_new_attraction_response(full_name, short_name, first_name,pronoun_subject,pronoun_possessive,source_person_email)


    
def send_mail_changed_attraction_response(is_attracted,full_name, short_name, first_name,pronoun_subject,pronoun_possessive,email_address):
    html=render_to_string('email_template_notify_changed_attraction_response.html',{'is_attracted':is_attracted,'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_changed_attraction_response_text.html',{'is_attracted':is_attracted,'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven <notifications@crushmaven.com>',email_address,short_name + ' changed ' + pronoun_possessive + ' mind',html,text)
   
def send_mail_delivery_problem(full_name, short_name, first_name,invalid_email_address,email_address):
    html=render_to_string('email_template_notify_delivery_problem.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'invalid_email_address':invalid_email_address,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_delivery_problem_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'invalid_email_address':invalid_email_address,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven <notifications@crushmaven.com>',email_address,'Unsuccessful invite delivery to ' + invalid_email_address,html,text)

def send_mail_lineup_not_started(email_address):
    html=render_to_string('email_template_notify_lineup_not_started.html',{'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_lineup_not_started.html',{'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven <notifications@crushmaven.com>',email_address,'Your admirer is waiting for you to complete their lineup',html,text)
    

def send_mail_lineup_expiration_warning(email_address,expiration_date):
    html=render_to_string('email_template_notify_lineup_expiration_warning.html',{'expiration_date':expiration_date,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_lineup_expiration_warning_text.html',{'expiration_date':expiration_date,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven <notifications@crushmaven.com>',email_address,'Your admirer lineup is about to expire',html,text)
    
def send_mail_missed_invite_tip(relationship):
    try:
        email_address = relationship.source_person.email
        source_first_name = relationship.source_person.first_name
        recipient_fb_username=relationship.source_person.username
        html_template = "email_template_missed_invite_tip_other.html"
        source_person_email=relationship.source_person.email
        if 'hotmail' in source_person_email or 'live.com' in source_person_email:
            html_template = "email_template_missed_invite_tip_hotmail.html"
        elif 'yahoo' in source_person_email:
            html_template = "email_template_missed_invite_tip_yahoo.html"
        #html=render_to_string('email_template_missed_invite_question.html',{'first_name':first_name,'crush_list':crush_list,'more_crushes_count':more_crushes_count,'STATIC_URL':STATIC_URL})
        text=render_to_string('email_template_missed_invite_tip_text.html',{'source_first_name':source_first_name,'STATIC_URL':STATIC_URL})
        html=render_to_string(html_template,{'source_first_name':source_first_name,'STATIC_URL':STATIC_URL, 'recipient_fb_username':recipient_fb_username})
        send_mailgun_email('CrushMaven <notifications@crushmaven.com>',email_address,'You must email invite your crush to receive a response!',html,text)
    except Exception as e:
        logger.error("problem sending direct mail: admirer not invited crush reminder with exception: " + str(e) + " to relationship: " + str(relationship))
