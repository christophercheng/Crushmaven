from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from crush.models import CrushRelationship,FacebookUser, Purchase
from crush import paypal
from django.views.decorators.http import require_POST
from django.http import HttpResponseNotFound,HttpResponseForbidden
from django.db.models import F


#from django.contrib.auth.models import Use
# to allow app to run in facebook canvas without csrf error:
from django.views.decorators.csrf import csrf_exempt 

@login_required
def ajax_update_num_credits(request):
    ajax_response = str(request.user.site_credits)
    return HttpResponse(ajax_response)

@login_required
def ajax_deduct_credit(request, feature_id, relationship_display_id, current_user_is_target):
    print "deducting credit"
    # called from lineup.html to add a member to either the crush list or the platonic friend list
    me=request.user
    try:
        if current_user_is_target:
            relationship=request.user.crush_relationship_set_from_target.get(admirer_display_id=relationship_display_id)
        else:
            relationship=request.user.crush_relationship_set_from_source.get(admirer_display_id=relationship_display_id)
    except CrushRelationship.DoesNotExist:
        return HttpResponseNotFound("Error: Could not find a matching crush relationship.")

    features_data=settings.FEATURES[feature_id]
    feature_cost = features_data['COST']
    credit_available = me.site_credits
    credit_remaining = credit_available - int(feature_cost)
    if credit_remaining >= 0:
        me.site_credits = credit_remaining
    else:
        return HttpResponseForbidden("Error: You no longer have enough credit.")
    if str(feature_id) == '1': # if feature is view lineup
        relationship.is_lineup_paid = True
    # now save both the user and the relationship
    me.save(update_fields=['site_credits'])
    relationship.save(update_fields=['is_lineup_paid'])
    return HttpResponse()
   
# -- Credit Checker Page - acts as boarding gate before allowing premium feature access --
@login_required
def credit_checker(request,feature_id,relationship_display_id):
    # obtain feature data from feature_id and settings
    features_data=settings.FEATURES[feature_id]
    feature_cost = features_data['COST']
    feature_name = features_data['NAME']
                        
    # obtain total credits
    credit_available = request.user.site_credits
    credit_remaining = credit_available - feature_cost
    
    success_path = request.GET.get('success_path',"home")
    print "success_path: " + success_path
    cancel_url = request.GET.get('cancel_url',"home")
    print "cancel_url: " + cancel_url
    paypal_success_url = settings.PAYPAL_RETURN_URL + "/?feature_id=" + str(feature_id) + "&rel_display_id=" + str(relationship_display_id) + "&username=" + request.user.username + "&success_path=" + success_path + "&cancel_url=" + cancel_url
    paypal_notify_url = settings.PAYPAL_NOTIFY_URL + request.user.username + "/"
    
    # perform conditional logic to determine which dialog to display
    
    if (credit_available < feature_cost):
        return render(request,'dialog_credit_insufficient.html',
                      {
                       'feature_cost':feature_cost,
                       'feature_name':feature_name,
                       'credit_available':credit_available,
                       'paypal_url': settings.PAYPAL_URL, 
                       'paypal_email': settings.PAYPAL_EMAIL, 
                       'paypal_success_url': paypal_success_url,
                       'paypal_cancel_url': cancel_url,
                       'paypal_notify_url':paypal_notify_url})
    else:
        return render(request,'dialog_credit_sufficient.html',
                      {'feature_cost':feature_cost,
                       'feature_name':feature_name,
                       'credit_available':credit_available,
                       'credit_remaining': credit_remaining,
                       'success_path':success_path})
        
@login_required    
@csrf_exempt # this is needed so that paypal success redirect from payment page works 
def paypal_purchase(request):

    method_dict=request.GET
    success_path = method_dict.get('success_path',"home")
    credit_amount = method_dict.get('credit_amount', 10)
    price=method_dict.get('amt',9)
    feature_id=method_dict.get('feature_id','')
    rel_display_id=method_dict.get('rel_display_id','')
    username=method_dict.get('username','')
    print "printing out pdt get variables:"
    for element in method_dict:
        print "element: " + element + " -> " + method_dict[element] 
#    resource = get_object_or_404( models.Resource, pk=id )
#    user = get_object_or_404( User, pk=uid )
    if request.REQUEST.has_key('tx'):
        tx = request.REQUEST['tx']      
        try:
            Purchase.objects.get( tx=tx )
            print "duplicate transaction found when processing PAYPAL PDT Handler"
            if feature_id == u'1': # handling of lineup payment
                try:# handle special feature processing 
                    facebook_user = FacebookUser.objects.get(username=username)
                    #print "facebook user found with first name: " + facebook_user.first_name
                    admirer_rel = request.user.get_all_new_incomplete_admirer_relations().get(admirer_display_id=rel_display_id)
                    feature_cost=int(settings.FEATURES['1']['COST'])
                    facebook_user.site_credits=F('site_credits') - feature_cost
                    admirer_rel.is_lineup_paid=True;
                    admirer_rel.save(update_fields=['is_lineup_paid'])
                    facebook_user.save(update_fields=['site_credits'])
                except CrushRelationship.DoesNotExist:
                    pass # do nothing, i guess :)            
                except FacebookUser.DoesNotExist:
                    pass
            return HttpResponseRedirect(success_path)
        except Purchase.DoesNotExist:
            print "processing pdt transaction"
            result = paypal.Verify(tx)
            if result.success(): # valid
                Purchase.objects.create(purchaser=request.user, tx=tx, credit_total=int(credit_amount),price= price)
                print "just created a new purchase"
                # handle special feature processing
                if feature_id == 1 and rel_display_id != '': # handling of lineup payment
                    try:
                        facebook_user = FacebookUser.objects.get(username=username)
                        admirer_rel = request.user.get_all_new_incomplete_admirer_relations().get(admirer_display_id=rel_display_id)
                        feature_cost=settings.FEATURES['1']['COST']
                        facebook_user.site_credits=F('site_credits') - feature_cost
                        admirer_rel.is_lineup_paid=True;
                        admirer_rel.save(update_fields=['is_lineup_paid'])
                        facebook_user.save(udpate_fields=['site_credits'])
                    except CrushRelationship.DoesNotExist:
                        pass # do nothing, i guess :)
                    except FacebookUser.DoesNotExist:
                        pass
                return HttpResponseRedirect(success_path)
            else: # didn't validate
                return render(request, 'error.html', { 'error': "Failed to validate payment" } )
    else: # no tx
        return render(request, 'error.html', { 'error': "No transaction specified" } )

@require_POST
@csrf_exempt
def paypal_ipn_listener(request,username,credit_amount):
    print "  I P N    L I S T N E R    C A L L E D !!!!"
    print "username: " + username
    print "credit amount: " + str(credit_amount)
    method_dict=request.POST
    price=method_dict.get('payment_gross',9)
        
    if request.REQUEST.has_key('txn_id'):
        txn_id = request.REQUEST['txn_id']
        try:
            facebook_user = FacebookUser.objects.get(username=username)
            print "facebook user found with first name: " + facebook_user.first_name
            
        except FacebookUser.DoesNotExist:
            # evetually Log and error tell PAYPAL that something went wrong and step sending ipn messages
            pass
        try:
            Purchase.objects.get( tx=txn_id )
            print "existing purchase found. transaction id: " + txn_id
            pass
        except Purchase.DoesNotExist:
            print "verify paypal IPN"
            result = paypal.Verify_IPN(method_dict)
            print "paypal IPN verified"
            if result.success(): # valid
                Purchase.objects.create(purchaser=facebook_user, tx=txn_id, credit_total=int(credit_amount),price=price)   
                print "payment made with credit_amount: " + str(credit_amount) + " price: " + str(price)
            else:
                print "paypal IPN was a failure"
    return HttpResponse("OKAY")
