from django import template
#from django.core.urlresolvers import reverse

register = template.Library()

@register.simple_tag
def navactive(request, url):
    # request.path is the current URL minus the host name
    # the following logic checks if the current page exists within the list of URLs passed in
        # if found ,active is returned, else empty string returned
    if url in request.path:
        return "active"
    else:
        return "inactive"


"""
Usage:
left navigation menu counts
"""
@register.filter()
def left_menu_count_display(value):
    if value > 0:
        return str(value) + ' new'

    
    else:
        return ""
    
