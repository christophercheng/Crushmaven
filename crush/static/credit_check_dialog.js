
// required inputs:
	// feature_id
	// unique_id (admirer display id or crush username)
	// purchase_callback_name
	// success_path
	// cancel_url
	// ajax_error
// INITIALIZE CREDIT CHECK MODAL 
$(document).ready(function() // handling for the slider
{ 
	$("#credit_check_modal").dialog({modal: true,resizable:false, autoOpen: false});
});

function purchase_feature(data){
	load_url="/credit_checker/";
	dialog_div = $("#credit_check_modal");
	dialog_div.attr("feature_id",data.feature_id)
	dialog_div.html('<div id="site-loading"></div>');
	dialog_div.load(load_url,data,function(responseTxt,statusTxt,xhr){
			if (statusTxt!="success"){
				$(this).html(data.ajax_error);
		    $("#site-loading").remove();
		   }
	}); 
	dialog_div.dialog("open");
	dialog_div.dialog("moveToTop");
	return false;
};

function purchase_conversation(csrf_token,attraction_id,purchase_callback_name='') {
			data = {};
			data['csrfmiddlewaretoken']=csrf_token;
			data['success_path'] = '/messages/converse/' + attraction_id;	
			data['cancel_url'] =  '{{request.get_full_path}}';
			var unique_id = attraction_id;
			data['unique_id'] = unique_id;
			data['feature_id'] = '4';
			if (purchase_callback_name=='')
				data['purchase_callback_name'] = 'window.redirect_to_conversation(' + attraction_id + ')';
			else
				data['purchase_callback_name'] = purchase_callback_name;
			data['ajax_error']='{{ajax_error}}';
			purchase_feature(data);
	
}; 
	   
window.redirect_to_conversation=function(attraction_id){
  	location.href="/messages/converse/" + attraction_id;
};