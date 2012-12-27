'''
Created on Nov 1, 2012
# this file contains context processor functions to handle the notifications elements in the nav top bar
'''
from django.conf import settings

def context_processor(request):
    me = request.user
    if not me.is_anonymous():  
        # get list of responded crushes (so we can filter them out the admirers )
        progressing_crush_list = me.crush_targets.filter(crush_relationship_set_from_target__target_status__gt = 3,crush_relationship_set_from_target__is_results_paid=False)     
        # build a list of incomplete admirer relationship by filtering them in the following order:
        #     filter through only those admirer relationships who have not finished their lineup (progressing relationships)
        #     filter out those progressing relationships who are also progressing crushes AND who have not yet instantiated a lineup
        #        e.g. if they are also a progressing crush, but a lineup has already been created, then don't filter them out
        admirer_relationships = me.crush_relationship_set_from_target
        progressing_admirer_relationships = admirer_relationships.filter(date_lineup_finished=None).exclude(source_person__in = progressing_crush_list,is_lineup_initialized=False) # valid progressing relationships  
    
        return {
            'num_admirers_in_progress' : progressing_admirer_relationships.count(),
            'num_new_admirers': progressing_admirer_relationships.filter(target_status__lt = 3).count(),
            'num_new_responses' : progressing_crush_list.count(),
            'num_crushes_in_progress' : me.crush_targets.filter(crush_relationship_set_from_target__target_status__lt=4).count(),
            'num_platonic_friends' : me.just_friends_targets.count(),
            'facebook_app_id': settings.FACEBOOK_APP_ID
            }
    else: # whenever a user is logged in, just use an empty dictionary
        return {}
