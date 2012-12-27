'''
Created on Nov 1, 2012
# this file contains context processor functions to handle the notifications elements in the nav top bar
'''
from django.conf import settings

def context_processor(request):
    if not request.user.is_anonymous():
        return {'num_new_admirers':request.user.crush_relationship_set_from_target.filter(target_status__lt = 3).count(),
            'num_new_responses' : request.user.crush_relationship_set_from_source.filter(target_status__gt = 3).exclude(is_results_paid=True).count(),
            'num_crushes_in_progress' : request.user.crush_relationship_set_from_source.filter(is_results_paid=False).count(),
            'num_admirers_in_progress' : request.user.crush_relationship_set_from_target.filter(date_lineup_finished=None).count(),
            'num_platonic_friends' : request.user.just_friends_targets.count(),
            'facebook_app_id': settings.FACEBOOK_APP_ID
            }
    else: # whenever a user is logged in, just use an empty dictionary
        return {}
