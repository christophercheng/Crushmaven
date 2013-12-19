'''
Created on Nov 1, 2012
# this file contains context processor functions to handle the notifications elements in the nav top bar
'''
from django.conf import settings
from datetime import datetime,timedelta
from crush.models import CrushRelationship
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
        all_messages_count=request.user.received_messages.filter(recipient_archived=False,recipient_deleted_at__isnull=True,moderation_status=settings.STATUS_ACCEPTED).count()

        new_messages_count=request.user.received_messages.filter(recipient_archived=False,recipient_deleted_at__isnull=True,read_at__isnull=True,moderation_status=settings.STATUS_ACCEPTED).count()
        
        ajax_reprocess_friends_with_admirers=True
        if  (me.processed_activated_friends_admirers):
            time_since_last_update = datetime.now() - me.processed_activated_friends_admirers 
            if time_since_last_update < timedelta(hours=settings.FRIENDS_WITH_ADMIRERS_SEARCH_DELAY):
                #print "don't re-process friends-with admirers - too soon: " + str(time_since_last_update)
                ajax_reprocess_friends_with_admirers=False

        inactive_friend_section_html = me.html_for_inactive_friend_section(ajax_reprocess_friends_with_admirers)
           
        return {
            'num_total_crushes': CrushRelationship.objects.all_crushes(me).count(),
            'num_total_admirers': progressing_admirers_count + past_admirer_relationships.count(),
            'num_admirers_in_progress' : progressing_admirers_count,
            #'num_new_admirers': progressing_admirer_relationships.filter(target_status__lt = 3).count(), # progressing admirers who haven't started lineup (3 status)
            'num_new_responses' : visible_responded_crushes.count(),
            'num_all_messages':all_messages_count,
            'num_new_messages':new_messages_count,
            #'num_crushes_in_progress' : left_menu_crush_count,
            'num_platonic_friends' : me.just_friends_targets.count(),
            'facebook_app_id': settings.FACEBOOK_APP_ID,
            'ajax_error':settings.AJAX_ERROR,
            'generic_error_message':settings.GENERIC_ERROR,
            'minimum_samegender_friends':settings.MINIMUM_LINEUP_MEMBERS,
            'minimum_crushgender_friends':settings.MINIMUM_LINEUP_MEMBERS,
            'inactive_friend_section_html':inactive_friend_section_html,
            }
    else: # whenever a user is logged in, just use an empty dictionary
        return {}
