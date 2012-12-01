'''
Created on Nov 1, 2012

@author: Chris Work
'''
# for my version of timesince
from datetime import datetime, timedelta
from django import template
from django.utils.timesince import timesince
from crush.models import LineupMember

register = template.Library()

# don't return any value if less than 2 minutes have not passed
@register.filter
def datetime_since(value): 
    #   now = datetime.now()
#   try:
#       difference = now - value
#   except:
#       return value
#    if difference <= timedelta(minutes=1):
#        return 'just now'
    return_value = '%(time)s' % {'time': timesince(value).split(', ')[0]}
    if '0 minutes' in return_value:
        return '1 minute'
    else:
        return return_value
    
# this is used to determine if crushes can be deleted - if they've been added > 7 days ago    
@register.filter
def days_since(value): 
    naive = value.replace(tzinfo=None)
    return (datetime.now() - naive).days
 


@register.filter
def date_since(value): 

    try:
        difference = datetime.now - value
    except:
        return 'exception'
    if difference < timedelta(hours=24):
        return 'hi'
    return '%(time)s' % {'time': timesince(value).split(', ')[0]}


# value is the admirer instance, arg is the lineup position (0-9)
# returns the username of the admirer lineup at that position
@register.filter
def admirer_lineup_username(value, arg): 
    print "looking for username at position " + arg
    try:
        member = value.lineupmember_set.get(position=(value.id + (.1 * int(arg))))
    except LineupMember.DoesNotExist:
        return "no_user"
    return member.username

"""
Usage:
{% if text|contains:"http://" %}
This is a link.
{% else %}
Not a link.
{% endif %}
"""
@register.filter()
def contains(value, arg):
    return arg in value

