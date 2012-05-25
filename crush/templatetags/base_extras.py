from django import template
#from django.core.urlresolvers import reverse

register = template.Library()

@register.simple_tag
def navactive(request, url):
    # request.path is the current URL minus the host name
    # the following logic checks if the current page exists within the list of URLs passed in
        # if found ,active is returned, else empty string returned
    print url,request.path
    if url in request.path:
        print "matched!"
        return "active"
    return ""



