'''
Created on Nov 1, 2012
# this file contains context processor functions to handle the notifications elements in the nav top bar
'''
from django.conf import settings
from datetime import datetime,timedelta
from crush.models import CrushRelationship
from postman.models import Message
from django.db.models import Q

def context_processor(request):
    # moderation constants
    me = request.user
    if not me.is_anonymous():  
        progressing_admirer_relationships = CrushRelationship.objects.progressing_admirers(me)
        progressing_admirers_count = progressing_admirer_relationships.count()
        past_admirer_relationships = CrushRelationship.objects.past_admirers(me)
        visible_responded_crushes = CrushRelationship.objects.visible_responded_crushes(me)
        #progressing_crushes = CrushRelationship.objects.progressing_crushes(me)
       # all_messages_count=request.user.received_messages.filter(recipient_archived=False,recipient_deleted_at__isnull=True,moderation_status=settings.STATUS_ACCEPTED).count()
        sent_thread_count=Message.objects.inbox(request.user).count()
        received_thread_count=Message.objects.sent(request.user).count()
        all_messages_count = sent_thread_count + received_thread_count
        new_messages_count=request.user.received_messages.filter(recipient_archived=False,recipient_deleted_at__isnull=True,read_at__isnull=True,moderation_status=settings.STATUS_ACCEPTED).count()

        friends_with_admirer_data=None # { user:{'num_admirers': num_admirers,'elapsed_time':elapsed_time}, ... }
        if  (me.processed_activated_friends_admirers):
            time_since_last_update = datetime.now() - me.processed_activated_friends_admirers 
            if time_since_last_update < timedelta(hours=settings.FRIENDS_WITH_ADMIRERS_SEARCH_DELAY):
                friends_with_admirer_data={}
                #calculate the data needed to populate the friends with admirer template
                for inactive_crush_friend in me.friends_with_admirers.all().order_by('first_name'):
                #print "creating html for: " + inactive_crush_friend.username
               
                    all_admirers = CrushRelationship.objects.all_admirers(inactive_crush_friend)
                    num_admirers = len(all_admirers)
                    if num_admirers==0:
                        continue # in this case, a user was added as a friend but then someone deleted them laster
        
                    elapsed_days = (datetime.now() - all_admirers[num_admirers-1].date_added).days
                    if elapsed_days==0:
                        elapsed_days = "today"
                    elif elapsed_days == 1:
                        elapsed_days = "yesterday"
                    elif elapsed_days > 60:
                        elapsed_days = str(elapsed_days/30) + " months ago"
                    elif elapsed_days > 30:
                        elapsed_days = "1 month ago"
                    else:
                        elapsed_days = str(elapsed_days) + " days ago"
                    admirer_data={}
                    admirer_data['num_admirers']=num_admirers
                    admirer_data['elapsed_time']=elapsed_days
                    friends_with_admirer_data[inactive_crush_friend]=admirer_data

        if  request.get_host() != 'www.crushmaven.com' or me.username in ['100006341528806','1057460663','100004192844461','651900292','100003843122126','100007405598756']:
            no_track=True
        else:
            no_track=False
        return {
            'num_total_crushes': CrushRelationship.objects.all_crushes(me).count(),
            'num_total_admirers': progressing_admirers_count + past_admirer_relationships.count(),
            'num_admirers_in_progress' : progressing_admirers_count,
            #'num_new_admirers': progressing_admirer_relationships.filter(target_status__lt = 3).count(), # progressing admirers who haven't started lineup (3 status)
            'num_new_responses' : visible_responded_crushes.count(),
            'num_all_messages':all_messages_count,
            'num_new_messages':new_messages_count,
            #'num_crushes_in_progress' : left_menu_crush_count,
            #'num_platonic_friends' : me.just_friends_targets.count(),
            'facebook_app_id': settings.FACEBOOK_APP_ID,
            'ajax_error':settings.AJAX_ERROR,
            'generic_error_message':settings.GENERIC_ERROR,
            'minimum_samegender_friends':settings.MINIMUM_LINEUP_MEMBERS,
            'minimum_crushgender_friends':settings.MINIMUM_LINEUP_MEMBERS,
            'friends_with_admirer_data':friends_with_admirer_data,
            'no_track':no_track
            }
    else: # whenever a user is not logged in , if there is ?no_track in url, then disable analytics tracking
        if request.get_host() != 'www.crushmaven.com' or 'no_track' in request.build_absolute_uri():
            no_track=True
        else:
            no_track=False
            
        return {'no_track':no_track}
