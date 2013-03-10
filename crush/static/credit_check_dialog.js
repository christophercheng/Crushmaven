
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

