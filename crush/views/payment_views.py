from django.http import HttpResponse, HttpResponseForbidden,HttpResponseRedirect,HttpResponseNotFound
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from crush.models import CrushRelationship,FacebookUser, Purchase
from crush import paypal
from django.views.decorators.http import require_POST
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

#from django.contrib.auth.models import Use
# to allow app to run in facebook canvas without csrf error:
from django.views.decorators.csrf import csrf_exempt 

# unique_id is the admirer display id for feature 1 (purchase lineup), it is the crush username for feature 2
# -- Credit Checker Page - acts as boarding gate before allowing premium feature access --
@login_required
def credit_checker(request):
    # retrieve post data 
    post_data = request.POST
    feature_id = post_data['feature_id']
    success_path = post_data['success_path']
    cancel_url = post_data['cancel_url']
    if cancel_url[-1] == '/':     
        cancel_url = cancel_url[:-1];
    purchase_callback_name = post_data['purchase_callback_name']
    unique_id = post_data['unique_id']
    features_data=settings.FEATURES[feature_id]
    feature_cost = features_data['COST']
    feature_name = features_data['NAME']
    if request.user.is_underage:
        feature_cost = 0
        if feature_name.find('for') != -1:
            feature_name = feature_name.partition("for")
            if feature_name[1]!="":
                feature_name = feature_name[0] + " for free (for a limited time)"                    
    # obtain total credits
    credit_available = request.user.site_credits
    credit_remaining = credit_available - feature_cost
    
    paypal_success_url = settings.PAYPAL_RETURN_URL + "/?feature_id=" + str(feature_id) + "&unique_id=" + str(unique_id) + "&username=" + request.user.username + "&success_path=" + success_path + "&cancel_url=" + cancel_url
    paypal_notify_url = settings.PAYPAL_NOTIFY_URL + request.user.username + "/"
    
    # perform conditional logic to determine which dialog to display
    
    if (credit_available < feature_cost):
        return render(request,'dialog_credit_insufficient.html',
                      {
                       'feature_cost':feature_cost,
                       'unique_id':unique_id,
                       'feature_name':feature_name,
                       'credit_available':credit_available,
                       'paypal_url': settings.PAYPAL_URL, 
                       'paypal_email': settings.PAYPAL_EMAIL, 
                       'paypal_success_url': paypal_success_url,
                       'paypal_cancel_url': cancel_url,
                       'completed_survey':request.user.bCompletedSurvey,
                       'paypal_notify_url':paypal_notify_url})
    else:
        return render(request,'dialog_credit_sufficient.html',{
                       'feature_id':feature_id,
                       'purchase_callback_name':purchase_callback_name,
                       'feature_cost':feature_cost,
                       'feature_name':feature_name,
                       'credit_available':credit_available,
                       'credit_remaining': credit_remaining,
                       'unique_id':unique_id
                       })

# unique_id is the admirer display id for feature 1 (purchase lineup), it is the crush username for feature 2
@login_required
def ajax_deduct_credit(request, feature_id, unique_id):
    logger.debug( "attempting to deducting credit" )
    me=request.user

    if str(feature_id) == '1': # if feature is view lineup
        try:
            new_admirers=CrushRelationship.objects.all_admirers(me)
            relationship = new_admirers.get(display_id=unique_id)
        except CrushRelationship.DoesNotExist:
            return HttpResponseNotFound("Error: Could not find a matching crush relationship.")
        if relationship.handle_lineup_paid() == False:    
            return HttpResponseForbidden("You do not have enough credits to purchase this feature.")
        else:
            return HttpResponse("")
        
    elif str(feature_id)=='2':
        try:
            relationship=(CrushRelationship.objects.visible_responded_crushes(me)).get(target_person__username=unique_id)
        except CrushRelationship.DoesNotExist:
            return HttpResponseNotFound("Error: Could not find a matching crush relationship.")
        if relationship.handle_results_paid() == False:    
            return HttpResponseForbidden("You do not have enough credits to purchase this feature.")
        else:
            return HttpResponse("")

    elif str(feature_id)=='3':
        try:
            relationships=CrushRelationship.objects.completed_crushes(me)
            relationship = relationships.get(target_person__username=str(unique_id))
        except CrushRelationship.DoesNotExist:
            return HttpResponseNotFound("Error: Could not find a matching crush relationship.")
        if relationship.handle_rating_paid() == False:    
            return HttpResponseForbidden("You do not have enough credits to purchase this feature.")
        else:
            return HttpResponse("")
        
    elif str(feature_id)=='4':
        try:
            relationships=CrushRelationship.objects.all_crushes(me)
            relationship = relationships.get(target_person__username=str(unique_id))
        except CrushRelationship.DoesNotExist:
            return HttpResponseNotFound("Error: Could not find a matching completed crush relationship.")
        if relationship.handle_messaging_paid() == False:    
            return HttpResponseForbidden("You do not have enough credits to purchase this feature.")
        else:
            return HttpResponse("")

@login_required    
@csrf_exempt # this is needed so that paypal success redirect from payment page works 
def paypal_pdt_purchase(request):

    method_dict=request.GET
    success_path = method_dict.get('success_path',"home")
    credit_amount = method_dict.get('credit_amount', 10)
    price=method_dict.get('amt',9)
    feature_id=method_dict.get('feature_id','')
    unique_id=method_dict.get('unique_id','')
    username=method_dict.get('username','')
    #logger.debug("printing out pdt get variables:")
    #for element in method_dict:
    #    logger.debug("element: " + element + " -> " + method_dict[element] )

    if request.REQUEST.has_key('tx'):
        tx = request.REQUEST['tx']      
        try:
            Purchase.objects.get( tx=tx )
            logger.error ("duplicate transaction found when processing PAYPAL PDT Handler")
            if feature_id == u'1' and unique_id!='': # handling of lineup payment
                try:# handle special feature processing 
                    facebook_user = FacebookUser.objects.get(username=username)
                    #print "facebook user found with first name: " + facebook_user.first_name
                    admirer_rel = CrushRelationship.objects.all_admirers(facebook_user).get(display_id=unique_id)
                    admirer_rel.handle_lineup_paid()
                except CrushRelationship.DoesNotExist:
                    pass # do nothing, i guess :)            
                except FacebookUser.DoesNotExist:
                    pass
            if feature_id == u'2' and unique_id!='':
                try:# handle special feature processing 
                    facebook_user = FacebookUser.objects.get(username=username)
                    admirer_rel = CrushRelationship.objects.all_crushes(facebook_user).get(target_person__username=unique_id)
                    admirer_rel.handle_results_paid()
                except CrushRelationship.DoesNotExist:
                    pass # do nothing, i guess :)            
                except FacebookUser.DoesNotExist:
                    pass
            return HttpResponseRedirect(success_path)
        except Purchase.DoesNotExist:
            logger.debug( "processing pdt transaction" )
            result = paypal.Verify(tx)
            if result.success(): # valid
                Purchase.objects.create(purchaser=request.user, tx=tx, credit_total=int(credit_amount),price= price)
                logger.debug("just created a new purchase")
                # handle special feature processing
                if feature_id == 1 and unique_id != '': # handling of lineup payment
                    try:
                        facebook_user = FacebookUser.objects.get(username=username)
                        admirer_rel = CrushRelationship.objects.all_admirers(facebook_user).get(display_id=unique_id)
                        admirer_rel.handle_lineup_paid()
                    except CrushRelationship.DoesNotExist:
                        pass # do nothing, i guess :)
                    except FacebookUser.DoesNotExist:
                        pass
                if feature_id == u'2' and unique_id != '':
                    try:# handle special feature processing 
                        facebook_user = FacebookUser.objects.get(username=username)
                        admirer_rel = CrushRelationship.objects.all_crushes(facebook_user).get(target_person__username=unique_id)
                        admirer_rel.handle_results_paid()
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
    logger.debug("  I P N    L I S T N E R    C A L L E D !!!!")
    logger.debug( "username: " + username )
    logger.debug("credit amount: " + str(credit_amount))
    method_dict=request.POST
    price=method_dict.get('payment_gross',9)
        
    if request.REQUEST.has_key('txn_id'):
        txn_id = request.REQUEST['txn_id']
        try:
            facebook_user = FacebookUser.objects.get(username=username)
            logger.debug( "facebook user found with first name: " + facebook_user.first_name )
            
        except FacebookUser.DoesNotExist:
            # evetually Log and error tell PAYPAL that something went wrong and step sending ipn messages
            pass
        try:
            Purchase.objects.get( tx=txn_id )
            logger.debug( "existing purchase found. transaction id: " + txn_id )
            pass
        except Purchase.DoesNotExist:
            logger.debug( "verify paypal IPN" )
            result = paypal.Verify_IPN(method_dict)
            logger.debug( "paypal IPN verified" )
            if result.success(): # valid
                Purchase.objects.create(purchaser=facebook_user, tx=txn_id, credit_total=int(credit_amount),price=price)   
                logger.debug( "payment made with credit_amount: " + str(credit_amount) + " price: " + str(price) )
            else:
                logger.error ("paypal IPN was a failure")
    return HttpResponse("OKAY")
