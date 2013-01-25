'''
Created on Nov 1, 2012
# this file contains context processor functions to handle the notifications elements in the nav top bar
'''
from django.conf import settings
from datetime import datetime
from crush.models import CrushRelationship

def context_processor(request):
    me = request.user
    if not me.is_anonymous():  
        progressing_admirer_relationships = CrushRelationship.objects.progressing_admirers(me)
        known_responded_crushes = CrushRelationship.objects.known_responded_crushes(me)
        progressing_crushes = CrushRelationship.objects.progressing_crushes(me)
        left_menu_crush_count = progressing_crushes.count() + known_responded_crushes.count()
           
        return {
            'num_admirers_in_progress' : progressing_admirer_relationships.count(),
            'num_new_admirers': progressing_admirer_relationships.filter(target_status__lt = 3).count(), # progressing admirers who haven't started lineup (3 status)
            'num_new_responses' : known_responded_crushes.count(),
            'num_crushes_in_progress' : left_menu_crush_count,
            'num_platonic_friends' : me.just_friends_targets.count(),
            'facebook_app_id': settings.FACEBOOK_APP_ID
            }
    else: # whenever a user is logged in, just use an empty dictionary
        return {}
