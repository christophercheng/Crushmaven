'''
Created on Nov 1, 2012
# this file contains context processor functions to handle the notifications elements in the nav top bar
'''
from django.conf import settings
from crush.models import CrushRelationship
from postman.models import Message

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
            'no_track':no_track
            }
    else: # whenever a user is not logged in , if there is ?no_track in url, then disable analytics tracking
        if request.get_host() != 'www.crushmaven.com' or 'no_track' in request.build_absolute_uri():
            no_track=True
        else:
            no_track=False
            
        return {'no_track':no_track}
