'''
Created on Nov 1, 2012
# this file contains context processor functions to handle the notifications elements in the nav top bar
'''
from django.conf import settings
from datetime import datetime
from crush.models import CrushRelationship
from postman.models import Message
from django.db.models import Q

def context_processor(request):
    # moderation constants
    me = request.user
    if not me.is_anonymous():  
        progressing_admirer_relationships = CrushRelationship.objects.progressing_admirers(me)
        visible_responded_crushes = CrushRelationship.objects.visible_responded_crushes(me)
        progressing_crushes = CrushRelationship.objects.progressing_crushes(me)
        left_menu_crush_count = progressing_crushes.count() + visible_responded_crushes.count()
        new_messages_count=request.user.received_messages.filter(recipient_archived=False,recipient_deleted_at__isnull=True,read_at__isnull=True,moderation_status=settings.STATUS_ACCEPTED).count()
           
        return {
            'num_admirers_in_progress' : progressing_admirer_relationships.count(),
            'num_new_admirers': progressing_admirer_relationships.filter(target_status__lt = 3).count(), # progressing admirers who haven't started lineup (3 status)
            'num_new_responses' : visible_responded_crushes.count(),
            'num_new_messages':new_messages_count,
            'num_crushes_in_progress' : left_menu_crush_count,
            'num_platonic_friends' : me.just_friends_targets.count(),
            'facebook_app_id': settings.FACEBOOK_APP_ID,
            'ajax_error':settings.AJAX_ERROR,
            'minimum_samegender_friends':settings.MINIMUM_LINEUP_MEMBERS,
            'minimum_crushgender_friends':settings.MINIMUM_LINEUP_MEMBERS,
            }
    else: # whenever a user is logged in, just use an empty dictionary
        return {}
