'''
Created on Nov 1, 2012

@author: Chris Work
'''
# for my version of timesince
from datetime import datetime, timedelta
from django import template
from django.utils.timesince import timesince

register = template.Library()

@register.filter
def datetime_since(value): 
    #   now = datetime.now()
#   try:
#       difference = now - value
#   except:
#       return value
#    if difference <= timedelta(minutes=1):
#        return 'just now'
    return '%(time)s' % {'time': timesince(value).split(', ')[0]}

@register.filter
def date_since(value): 

    try:
        difference = datetime.now - value
    except:
        return 'exception'
    if difference < timedelta(hours=24):
        return 'hi'
    return '%(time)s' % {'time': timesince(value).split(', ')[0]}