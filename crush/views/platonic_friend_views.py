from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from crush.models import CrushRelationship,PlatonicRelationship,FacebookUser,LineupMembership

from multiprocessing import Pool
from django.http import HttpResponseNotFound

@login_required
def ajax_reconsider(request):

    me = request.user
    rel_id = request.POST['rel_id']
    
    try:
        rel=PlatonicRelationship.objects.all_friends(me).get(id=rel_id)
        rel_target_person=rel.target_person
        try:
            CrushRelationship.objects.all_crushes(me).get(target_person__username=rel_target_person.username)         
            # for some reason crush relationship already exists, but kill this platonic relationship anyway before leaving
            rel.delete()
            return HttpResponse("success") # crush relationship already exists for this person so don't do anything mo
        except CrushRelationship.DoesNotExist:
            # create a new crushrelationship
            new_crush=CrushRelationship.objects.create(target_person=rel_target_person,source_person=request.user,friendship_type=rel.friendship_type,updated_flag=True)
           
            if rel.friendship_type != 0: # for crushes with non-friends, the lineup must be initialized while the admirer is still logged in
                pool=Pool(1)
                pool.apply_async(LineupMembership.objects.initialize_lineup,[new_crush],) #initialize lineup asynchronously
                rel.delete()
    except PlatonicRelationship.DoesNotExist:
        return HttpResponseNotFound("can't find the original platonic relationship") #can't find original platonic relationships so don't do anything more
    
    return HttpResponse("success")
   
# -- Just Friends Page --
@login_required
def just_friends(request):
    me = request.user
    # only for testing purposes:
    if request.method == "POST":
        crushee_id=''
        userlist = []
        
        for key in request.POST:
            crushee_id=request.POST[key]
    
            if key.startswith('to'):    
                crushee_id=request.POST[key][:-1] #handle a hack where last character is the friend type

                friend_type= int(request.POST[key][-1])
                # find existing site user with this id or create a new user 
                # called function is in a custom UserProfile manager because it is also used during login/authentication
                print "trying to get a platonic friend user for id=" + crushee_id            
                selected_user=FacebookUser.objects.find_or_create_user(fb_id=crushee_id, fb_access_token=request.user.access_token, fb_profile=None, is_this_for_me=False)
                # now that the user is definitely on the system, add that user to the crush list        
                # only create a new relationship if an existing one between the current user and the selected user does not exist 
    
                if not(request.user.just_friends_targets.filter(username=selected_user.username).exists()):
                        PlatonicRelationship.objects.create(target_person=selected_user,source_person=request.user,
                                                               friendship_type=friend_type, updated_flag=True)
                        userlist.append(selected_user)
        return HttpResponseRedirect('/just_friends')

    # obtain the results of any crush additions or deletions
        # later I can move this into a separate view function
    
    if "delete" in request.GET:
        delete_username=request.GET["delete"]
            # find the relationship and delete it!
        try:
            PlatonicRelationship.objects.all_friends(me).get(target_person__username=delete_username).delete()
        except PlatonicRelationship.DoesNotExist:
            delete_username=''
        return HttpResponseRedirect('/just_friends')

    platonic_relationships = PlatonicRelationship.objects.all_friends(me).order_by('-updated_flag','target_person__last_name')
    
    return render(request,'just_friends.html',
                              {
                               'platonic_relationships':platonic_relationships,
                               })    