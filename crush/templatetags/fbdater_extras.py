'''
Created on Nov 1, 2012

@author: Chris Work
'''
# for my version of timesince
from datetime import datetime, timedelta
from django import template
from django.utils.timesince import timesince
from django.conf import settings

register = template.Library()

@register.simple_tag
def navactive(request, url):
    # request.path is the current URL minus the host name
    # the following logic checks if the current page exists within the list of URLs passed in
        # if found ,active is returned, else empty string returned
    if url in request.path:
        return "active"
    return ""

@register.filter
def target_status_text(value):
    TARGET_STATUS_CHOICES = (
                           (0,'not signed up'),
                           (1,'not signed up'),
                           (2,'not started lineup'),
                           (3,'started lineup'),
                           (4,'responded'),
                           (5,'responded'),
                           )
    return TARGET_STATUS_CHOICES[int(value)][1]

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
    difference = ""
    try:
        print "datetime.now: " + str(datetime.now())
        print "value: " + str(value)
        difference = datetime.now() - value
    except:
        return 'exception'
    if difference < timedelta(hours=24):
        return 'hi'
    return '%(time)s' % {'time': timesince(value).split(', ')[0]}

@register.filter
def is_in_future(value): 
    if datetime.now() < value:
        return True
    else:
        return False

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

# used by lineup.html to iterate over a range of numbers
@register.filter
def get_range( value ):
  """
    Filter - returns a list containing range made from given value
    Usage (in template):

    <ul>{% for i in 3|get_range %}
      <li>{{ i }}. Do something</li>
    {% endfor %}</ul>

    Results with the HTML:
    <ul>
      <li>0. Do something</li>
      <li>1. Do something</li>
      <li>2. Do something</li>
    </ul>

    Instead of 3 one may use the variable set in the views
  """
  return range( value )

# called by setups_by_you.html to display number of responses for target and all recommendees
@register.filter
def lineup_statistics (relationship):
    lineup_count =  relationship.lineupmember_set.count();
    assessed_count = relationship.lineupmember_set.exclude(decision=None).count()
    return str(assessed_count) + ' out of ' + str(lineup_count)

# called by setups_by_you.html to display number of responses for target and all recommendees
@register.filter
def setup_target_responses_length (setup_relationship):
    return len(setup_relationship.setuplineupmember_set.exclude(decision=None))
    # called by setups_by_you.html to display number of responses for target and all recommendees
@register.filter
def setup_recommendees_responses_length (setup_relationship):
    return len(setup_relationship.setuplineupmember_set.exclude(lineup_member_attraction=None))