'''
Created on Nov 1, 2012
# this file contains context processor functions to handle the notifications elements in the nav top bar
'''


def context_processor(request):
    if not request.user.is_anonymous():
        return {'num_incomplete_admirers':request.user.crushrelationship_set.filter(target_status__lt = 5).count(),
            'num_new_responses' : request.user.get_profile().crushrelationship_set.exclude(target_feeling = 0).exclude(is_results_paid=True).count()
            }
    else: # whenever a user is logged in, just use an empty dictionary
        return {}
