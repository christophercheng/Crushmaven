/*!
 * Facebook Friend Selector
 * Copyright (c) 2012 Coders' Grave - http://codersgrave.com
 * Version: 1.2
 * Requires:
 *   jQuery v1.6.2 or above
 *   Facebook Integration - http://developers.facebook.com/docs/reference/javascript/
 */
;(function(window, document, $, undefined) {
  'use strict';
  
  /*
   * any of the following attributes: max_selections, excludeIds,getStoredFriends,onSubmit will automatically overwrite existing properties set in the original dictionary parameter
   * one caveat, if a previous attribute was set, then future iterations of the dialog will always use this attribute value, unless it is changed
   * in other words, the attribute must be reset by setting it to "" and not just removing the attribute from the dom element
   */
  $.fn.fSelector = function ( options ) {
	this.unbind("click.fs");
    this.bind("click.fs", function(){
    	var attr_max_selections= $(this).attr('max_selections');
    	var attr_getStoredFriends = $(this).attr('getstoredfriends');
    	var attr_onSubmit = $(this).attr('onSubmit');
    	var attr_excludeIds = $(this).attr('excludeids');

    	if (attr_max_selections != undefined)// we are in friend setup mode most likely
    		options.max=parseInt(attr_max_selections);
    	if (attr_getStoredFriends != undefined)
    		options.getStoredFriends=attr_getStoredFriends;
    	if (attr_onSubmit!=undefined)
    		options.onSubmit=attr_onSubmit;
    	if (attr_excludeIds != undefined)
    		options.excludeIds=attr_excludeIds;
    	fsOptions = options;
      _start();
    });
    return this;

	  };

  var fsOptions = {},
  running = false, isShowSelectedActive = false,
  windowWidth = 0, windowHeight = 0, selected_friend_count = 1,
  search_text_base = '',
  
  num_connect_tries = 0, // for facebook connect to try mutliple times if errors
  
  content, wrap, overlay,

  _start = function() {

	  if ( FB === undefined ){
	      window.alert_modal('Facebook Connection Error', "Sorry, we are experiencing difficultly connecting to Facebook.  Please try again later.",$('#fs-dialog-box-wrap'));
	      return false;
	    }
	  
	  FB.getLoginStatus(function(response) {
	  	if (response.status === 'connected') {
	      _start2();
	  	} else if (response.status === 'not_authorized') {
	     	// not_authorized
		      window.alert_modal('Facebook Connection Error', "Sorry, we are currently experiencing diffuclty connecting to Facebook.  Please try again later.",$('#fs-dialog-box-wrap'));
	  		return false;
	  	} else {
	      // not_logged_in
	      login(_start2);
	  	}
		}); 
  },
  
  _start2 = function() {

    fsOptions = $.extend(true, {}, defaults, fsOptions);
    if ( fsOptions.max > 0 && fsOptions.max !== null ) {
      fsOptions.showSelectedCount = true;

      // if max. number selected hide select all button
      fsOptions.showButtonSelectAll = false;
    }

    _dialogBox();
    fsOptions.onStart();
  },

  _selectUsername = function() {
	  var limit_state = _limitText();
      
     if (limit_state === false) {
        return false;
      }


    var username=$("#nfs-input-text").val();// get the text from the nfs-input-text box
    if (username==fsOptions.lang.nonFriendSearchText | username=="")
    	return false;
	$("#fs-user-list").append('<div id="fs-loading"></div>');
    // see if user exists
	window.wait_modal_open("",$('#fs-dialog-box-wrap'));
    $.get("/ajax_find_fb_user/", {username:username},
    	  function(response){
    		window.wait_modal_close();
	        $('#fs-loading').remove();
    		if ('error_message' in response) {
    			window.alert_modal("Invalid Username",response.error_message,$("#fs-dialog-box-wrap") );
    			return false;
    		}
    		else {
 
    	    	// find the original user in hte old container
    	    	var selected_id = response.id + response.friend_type;
    			var duplicate_element = $('#fs-selected-user-list .fs-friends[value='+selected_id+']');

    	    	if ($(duplicate_element).length > 0){
    	    		window.alert_modal("Invalid Username","You already selected this person",$("#fs-dialog-box-wrap") );
    	    		return false;
    			}

    			_addValidUsername(response);
    	        selected_friend_count++;
    	        _enableContinueButton();
    			$('#nfs-input-text').val("");
    			window.addedNonFriend=true;
    		} 		
    }).fail(function(responseText,textStatus,XHR){
 		window.wait_modal_close();
    	fsOptions.onError("Sorry, we are unable to process your Facebook id.  Please re-check your entry and try again.");
    	$("#fs-loading").remove();
    });
},

  _addValidUsername  = function(userData){
        var item = $('<li class="checked selected" id="friend-type' + userData.friend_type + '"/>');
        var link = userData.name;

        var link =  '<a class="fs-anchor"  href="javascript://">' +
		        '<input class="fs-fullname" type="hidden" name="fullname[]" value="'+userData.name.toLowerCase().replace(/\s/gi, "+")+'" />' +
		        '<input class="fs-friends" type="checkbox" checked="checked" name="friend[]" value="' + userData.id+ userData.friend_type + '" />' +
		        '<img class="fs-thumb" src="https://graph.facebook.com/'+userData.id+'/picture" />' +
		        '<span class="fs-name">' + _charLimit(userData.name, 15) + '</span>' +
		      '</a>';
        item.append(link);
        $('#fs-selected-user-list ul').append(item);

	  },
    
  _close = function() {

    wrap.fadeOut(400, function(){
      content.empty();
      wrap.remove();
      _stopEvent();
      overlay.fadeOut(400, function(){
        overlay.remove();
      });
    });

    running = false;
    isShowSelectedActive = false;
    fsOptions.onClose();
  },
  
  _continue = function() {

	  /*
	        '<div id="fs-dialog-buttons">' +
	              '<a href="javascript:{}" id="fs-continue-button" class="fs-button"><span>Continue</span></a>' +
	              '<a href="javascript:{}" id="fs-cancel-button" class="fs-button"><span>'+fsOptions.lang.buttonCancel+'</span></a>' +
	          '</div>' +
	   */
	  
	  // change title to 'confirm your crush additions step 2 of 2'

      $('#fs-dialog-title span').html("Add Attractions - Confirmation");
      $('#nfs-tab').hide();
      $('#fs-tab').hide();
      $('#fs-continue-button').hide();
      $('#fs-submit-button').show();
      //$('#fs-terms').show();
      $('#fs-back-button').show();
      $('#fs-select-view').hide();
      $('#fs-confirm-view').show();
      _buildConfirmView();
	  
	  // and the big one, show all of the selected users broken out into friend type
	  
  },
  
  _back = function() {

	  /*
	        '<div id="fs-dialog-buttons">' +
	              '<a href="javascript:{}" id="fs-continue-button" class="fs-button"><span>Continue</span></a>' +
	              '<a href="javascript:{}" id="fs-cancel-button" class="fs-button"><span>'+fsOptions.lang.buttonCancel+'</span></a>' +
	          '</div>' +
	   */
	  
	  // change title to 'confirm your crush additions step 2 of 2'

      $('#fs-dialog-title span').html(fsOptions.lang.title);
      $('#nfs-tab').show();
      $('#fs-tab').show();
      $('#fs-continue-button').show();
      $('#fs-submit-button').hide();
      $('#fs-terms').hide();
      $('#fs-back-button').hide();
      $('#fs-select-view').show();
      $('#fs-confirm-view').hide();
      $('#fs-confirm-user-list').children().remove();
	  
	  // and the big one, show all of the selected users broken out into friend type
	  
  },

  _submit = function() {

	// ensure the terms & conditions checkbox is checked
	 
	if (!$('#fs-terms-checkbox').is(':checked')){
		window.alert_modal("Terms & Conditions Agreement","You cannot proceed without agreeing to the Terms & Conditions.",$("#fs-dialog-box-wrap") );
		return false;
  }
    //var selected_friends = [];
    var selected_friends_json={};
    $('li.checked a.fs-anchor').each(function(){
    	
    	var username=$(this).children('.fs-friends').val();
    	var fullname=$(this).children('.fs-fullname').val();
    	fullname=fullname.replace(/\+/g," ");
    	selected_friends_json[username]=fullname;
    	//selected_friends.push(parseInt(username,10));
    });
   
/*
    if ( fsOptions.facebookInvite === true ){

      var friends = '';

      for (var i = 0; i < selected_friends.length; i++) {
        friends += selected_friends[i] + ',';
      }

      friends = friends.substr(0, friends.length - 1);

      FB.ui({
        method: 'apprequests',
        message: fsOptions.lang.facebookInviteMessage,
        to: friends
      },function(response){

        if ( response !== null ){
          fsOptions.onSubmit(selected_friends);

          if ( fsOptions.closeOnSubmit === true ) {
            _close();
          }
        }

      });
    }
   */ 
    //else{
      if (typeof fsOptions.onSubmit == "string")
    	  eval(fsOptions.onSubmit + '(selected_friends_json)');
      else
    	  fsOptions.onSubmit(selected_friends_json);

      if ( fsOptions.closeOnSubmit === true ) {
        _close();
      }
    //}

  },

  _dialogBox = function() {

    if (running === true) {
      return;
    }

    running = true;

    $('body').append(
      overlay = $('<div id="fs-overlay"></div>'),
      wrap = $('<div id="fs-dialog-box-wrap"></div>')
    );

    
    var button_bar =  '<div id="fs-dialog-buttons">' +
		'<div id="fs-terms"><span id="fs-terms-checkbox-container"><input id="fs-terms-checkbox" type="checkbox" checked="checked"/></span><span id="fs-terms-checkbox-text">I agree to the <a href="/help_terms" target="_blank">terms & conditions</a></span></div>'  +
		 '<a href="javascript:{}" id="fs-cancel-button" class="site_dialog_button site_dialog_cancel_button"><span class="ui-button-text">'+ fsOptions.lang.buttonCancel +'</span></a>' +
			'<a id="fs-back-button" class=" site_dialog_button site_dialog_back_button" href="javascript://"><span>&#60; Back</span></a>' +
		 '<button href="javascript:{}" id="fs-continue-button" class="site_dialog_button site_dialog_go_button" disabled><span class="ui-button-text">' + fsOptions.lang.buttonContinue + '</span></button>' +
		 '<a href="javascript:{}" id="fs-submit-button" class="site_dialog_button site_dialog_go_button"><span>Add</span></a>' +
  	'</div>';
    
    var title_bar = '<h2 id="fs-dialog-title"><span>'+fsOptions.lang.title+'</span>';
    if (!fsOptions.setupSelect){
	    title_bar = title_bar + 
	    	'<a href="javascript:{}" id="fs-tab" >friends</a>' +
	    	'<a href="javascript:{}" id="nfs-tab" class="fs-inactive-tab">others</a>';
	  }
    //title_bar = title_bar + 
    //	'</h2><span class="close_dialog"></span>';
    wrap.append(
     title_bar,
     content = $('<div id="fs-dialog-box-content"></div>'),
     button_bar
    );

    var container = '<div id="fs-dialog" class="fs-color-'+fsOptions.color+'">' +
                      
                      '<div id="fs-select-view">' +
                      
	                      
	                      '<div id="fs-filter-box">' +
	                        '<div id="fs-input-wrap">' +
	                          '<input type="text" id="fs-input-text" title="'+fsOptions.lang.searchText+'" />' +
	                          '<a href="javascript:{}" id="fs-reset">Reset</a>' +
	                        '</div><span id="fs-search-results"></span>' +
	                      '</div>' +
	                      
	                      
	                      '<div id="nfs-input-box">' +
	                      	'<span>https://facebook.com/</span>' +
	                      	'<span id="nfs-input-wrap">' +
	                          	'<input type="text" id="nfs-input-text" title="'+fsOptions.lang.nonFriendSearchText+'" />' +
	                          	//'<a href="javascript:{}" id="fs-reset">Reset</a>' +
	                        '</span>' +
	                        '<a href="javascript:{}" id="fs-select-button" class="fs-button site_dialog_select_button" disabled><span>Select</span></a>' +	

	                        '<span id=\'nfs-help-link\'><a href="#" class="popup_link"> what is this?</a>' +
		                       '<div id="nfs-help" class="popup">' +
		                      		//'<span id="nfs-help-pointer"></span>' +
		                      		"<h3>What is a unique Facebook user id?</h3>" +
		                      		'<p>In your web browser, navigate to your attraction\'s Facebook page (on facebook.com).  Locate and examine the address bar at the top of the browser.  ' +
		                      		'The text that follows \'www.facebook.com/\' is your attraction\'s facebook user id. Copy and paste it up above.  <strong>Exclude the \'?\' or \'/\' characters and anything after them.</strong></p>' +
		                      		'<img src=\'/static/images/friend_selector_help.png\'>' +
		                      		'In the above example, the unique Facebook user id is \'JessicaAlba\'' +
		                      		'<span class="delete_button"></span>' +
		                      '</div></span>' +
	                        
	                        '</div>' +
	                      
	                      '<div id="fs-selected-user-list">' +
	                      	'<ul></ul>' +
	                      '</div>' +    
	                      
	                      '<div id="fs-user-list">' +
	                        '<ul></ul>' +
	                      '</div>' +
     

	                      
	                  '</div>' +// close off fs-select-view +
	                  
	                  '<div id="fs-confirm-view">' +
	                      	'<div id="fs-confirm-user-list">' +
	                    	'</div>' +
	                  '</div>' + // close off fs-confirm view
    
     
	                '</div>'; // close off fs-dialog

    //

    content.html(container);
    $('#nfs-input-box').hide();
    $('#fs-nonfriend-help').hide();
    $('#fs-terms').hide();
    $('#fs-back-button').hide();
    $('#fs-submit-button').hide();
    $('#fs-confirm-view').hide();
    $('#fs-user-list').append('<div id="fs-loading"></div>');
    _getFacebookFriends();
    _resize(true);
    _initEvent();
    //_selectAll();

    $(window).resize(function(){
      _resize(false);
    });

  },
  
  _getFacebookFriends  = function(){
	  	// BATCH request friends of gender preference and a second request of friends of same gender.  
	  		// second request is to ensure user has enough friends to make non-friend attraction additions
	  	// process the ids of excluded friends into a syntax that FQL understands (comma delimited list)    	  	
	    var fql_query = "";
	    var fql_samegender_query = "";
	    // initialize fql query and add any exclude ids if provided as an argument
	    if (fsOptions.excludeIds !==""){
	    	//alert (fsOptions.excludeIds);
	    	fql_query += "SELECT uid, name FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = " + fsOptions.facebookID + " AND NOT (uid2 IN (" + fsOptions.excludeIds + ")))";	
	    }
	    else {
	    	fql_query += "SELECT uid, name FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = " + fsOptions.facebookID + ")";
	    }
	    fql_samegender_query += "SELECT uid, name FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = " + fsOptions.facebookID + ")";
	    // add gender preference
	    if (fsOptions.malePref !== null){
		    var genderPref = "Female";
	    	if (fsOptions.malePref===true)
	    		genderPref="Male";
	    	fql_query += " AND sex='" + genderPref + "'";
	    }
	    if (fsOptions.maleGender !== null){
		    var gender = "Female";
	    	if (fsOptions.maleGender===true)
	    		gender="Male";
	    	fql_samegender_query += " AND sex='" + gender + "'";
	    }    
	    // add order info
	    fql_query += " ORDER BY name";
  
	  	var batch_query = {batch: [
	  	               	  	  {
	  	               	  		  'method':'get',
	  	               	  		  'relative_url':'fql?q='+fql_query
	  	               	  	  },
	  	               	  	  {
	  	               	  		  'method':'get',
	  	               	  		  'relative_url':'fql?q='+fql_samegender_query
	  	               	  	  }
	  	               	  	                           ]};// close off batch_query
		//FB.api('fql',{q:fql_query}, function(response) {
	  	FB.api('/',"POST",batch_query, function(response) {
	  		if ( response.error ) {
	  			//alert ("error: " + response.error); // temporary
	  			num_connect_tries+=1;
	  			if (num_connect_tries < 7) 	
	  				setTimeout(function () {
	  					_getFacebookFriends();
	  				}, 400); // if error connecting to facebook, wait .4 milliseconds before trying again
	  			else // too many tries - give up
	  			{
	  				num_connect_tries=0;
	  				window.alert_modal('Facebook Connection Error', "We're experiencing difficultly connecting to Facebook.  Please try again later.",$('#fs-dialog-box-wrap') );
	  				
	  		        location.href="/facebook/login";
	  		        //_close();
	  		        return false;
	  			}
	  		}
	  		else {
	  			if (JSON.parse(response[1].body).data.length < fsOptions.minimum_samegender_friends){
	  				window.alert_modal('Minimum Friend Requirement', "Sorry, you do not have the required number of Facebook friends to use this feature.",$('#fs-dialog-box-wrap') );
	  				_close();
	  				return;
	  			}
	  			_buildFacebookFriendGrid(response[0]);  	
	  	    	}
	  }); // close fb.api call 
  },
    
  _buildFacebookFriendGrid = function(response) {
      
	  var facebook_friends = JSON.parse(response.body).data;
      var item,person,link;
      // don't allow users with less than 4 friends of same sex to add any type of crush
      if (facebook_friends.length < fsOptions.minimum_crushgender_friends) {
    	  window.alert_modal('Minimum Friend Requirement', "Sorry, you do not have the required number of Facebook friends to use this feature.",$('#fs-dialog-box-wrap') );
    	  _close();
      }
      
      for (var j = 0; j < facebook_friends.length; j++) {

        if ($.inArray(parseInt(facebook_friends[j], 10), fsOptions.excludeIds) >= 0) 
          continue;

          item = $('<li/>');
          person = facebook_friends[j]
          link =  '<a class="fs-anchor" href="javascript://">' +
                        '<input class="fs-fullname" type="hidden" name="fullname[]" value="'+person.name.toLowerCase().replace(/\s/gi, "+")+'" />' +
                        '<input class="fs-friends" type="checkbox" name="friend[]" value="'+ person.uid+'0" />' +
                        '<img class="fs-thumb" src="https://graph.facebook.com/'+person.uid+'/picture" />' +
                        '<span class="fs-name">' + _charLimit(person.name, 15) + '</span>' +
                      '</a>';

          item.append(link);

          $('#fs-user-list ul').append(item);

      }
      // pre-select elements
      if (fsOptions.getStoredFriends.length){
    	  if (fsOptions.getStoredFriends!="") {
	    	  var preselected_friends = fsOptions.getStoredFriends.split(',');
	    	  for (var x = 0; x < preselected_friends.length;x++){
	    		  // find element with username
	    		  var username=preselected_friends[x] + '0';// there was a hack where type of friend was noted as an extra character at end
	    		  var target_element = $('#fs-user-list ul li a input.fs-friends[value="' + username + '"]');
	    		  _click(target_element.parents('li'));
	    	  }
    	  }//close off if (fsOptions.getStoredFriends!= "")
      }
      
      $('#fs-loading').remove();


  },
  

  _buildConfirmView = function() {
		
	  var friend1_elements = $('#fs-selected-user-list li').filter('#friend-type1');
	  var friend2_elements = $('#fs-selected-user-list li').filter('#friend-type2');
	  var friend0_elements = $('#fs-selected-user-list li').not('#friend-type2').not('#friend-type1');
	  
	  var container = $('#fs-confirm-user-list'); 
	// build friend list  
	  if (friend0_elements.length > 0) {
		  var new_html = '<h2>Selected Friends <span class="nf_selected_header_count">' + friend0_elements.length + '</span></h2><ul>';
	
		  $.each(friend0_elements, function(){
	    		var duplicate = $(this).clone();
	    		duplicate.find('input').remove();
	    		new_html += '<li>' + duplicate.html() + '</li>';
	    	});
		  new_html+='</ul>';
		  container.append(new_html);
	  }
	  
  	// build friend-of-friend list
	  if (friend1_elements.length > 0) {
		  var new_html = '<h2 id="fof_selected_header">Friends-of-Friends <span class="nf_selected_header_count">' + friend1_elements.length + '</span></h2><ul>';
			
		  $.each(friend1_elements, function(){
	    		var duplicate = $(this).clone();
	    		duplicate.find('input').remove();
	    		new_html += '<li>' + duplicate.html() + '</li>';;
	    	});
		  new_html+='</ul>';
		  container.append(new_html);
	  }
	  
  	
  	// build non-friend list
	  if (friend2_elements.length > 0) {
		  var new_html = '<h2  id="nf_selected_header">Non-Friend Users <span class="nf_selected_header_count">' + friend2_elements.length + '</span></h2><ul>';
			
		  $.each(friend2_elements, function(){
	    		var duplicate = $(this).clone();
	    		duplicate.find('input').remove();
	    		new_html += '<li>' + duplicate.html() + '</li>';
	    	});
		  new_html+='</ul>';
		  container.append(new_html);
	  }

  },

  _initEvent = function() {
  
    wrap.delegate('#fs-cancel-button', 'click.fs', function(){
      _close();
    });
    wrap.delegate('.close_dialog', 'click.fs', function(){
        _close();
      });
    
    wrap.delegate('#fs-submit-button', 'click.fs', function(){
      _submit();
    });
    
    wrap.delegate('#fs-continue-button', 'click.fs', function(){
    	if (fsOptions.setupSelect)
    		_submit();
    	else
    		_continue();
      });
    
    wrap.delegate('#fs-back-button', 'click.fs', function(){
        _back();
      });
    
    wrap.delegate('#fs-select-button', 'click.fs', function(){
        _selectUsername();
      });
    
    $('#fs-dialog-title').on("click","#nfs-tab", function(e){
        _showNfsInputBox($(this));
        $('#fs-tab').addClass('fs-inactive-tab');
        $('#nfs-tab').removeClass('fs-inactive-tab');
 	   if (!window.addedNonFriend)
 		   setTimeout(function(){_showNfsHelpPopup();},300); 
      });
    
    $('#fs-dialog-title').on("click","#fs-tab", function(e){
        _showFsInputBox($(this));
        $('#nfs-tab').addClass('fs-inactive-tab');
        $('#fs-tab').removeClass('fs-inactive-tab');
      });
    
    $('#fs-filter-box input').focus(function(){
      if ($(this).val() === $(this)[0].title){
        $(this).val('');
      }
    }).blur(function(){
      if ($(this).val() === ''){
        $(this).val($(this)[0].title);
      }
    }).blur();
    
    $('#nfs-help-link a').on('click',function(){

	   _showNfsHelpPopup();	   
    });
   $('#nfs-help .delete_button').click(function(e){
	   $('#nfs-help').animate({	left:0,top: 0},500);	
	   $('#nfs-help').hide('1000');
	   e.stopPropagation();
   });
   

   //$('#nfs-help').click(function(e){ 	
	   
//	   e.stopPropagation();
 //  });
    
    $('#nfs-input-box input').focus(function(){

        if ($(this).val() === $(this)[0].title){
          $(this).val('');
        }
      }).blur(function(){

        if ($(this).val() === ''){
          $(this).val($(this)[0].title);
        }
      }).blur();


    $('#fs-filter-box input').keyup(function(){
      _find($(this));
    });

    $('#nfs-input-text').keyup(function(event) {
    	if ($(this).val()!="")
    		$('#fs-select-button').removeAttr('disabled');
    	else
    		$('#fs-select-button').attr('disabled','true');
    	 if (event.keyCode == '13') {
    	    $('#fs-select-button').click();
    	    event.preventDefault();
    	  }
    });
    
    wrap.delegate('#fs-reset', 'click.fs', function() {
      $('#fs-input-text').val('');
      _find($('#fs-filter-box input'));
      $('#fs-input-text').blur();
    });


    wrap.delegate('#fs-user-list li', 'click.fs', function() {
      _click($(this));
    });

    wrap.delegate('#fs-selected-user-list li', 'click.fs', function() {
        _click($(this));
      });
  
    /*
    $('#fs-dialog').on("click","#fs-show-selected", function(e){
        _showSelected($(this));
      });
    */

    $(document).keyup(function(e) {
      if (e.which === 27 && fsOptions.enableEscapeButton === true) {
        _close();
      }
    });


    if ( fsOptions.closeOverlayClick === true ) {
      overlay.css({'cursor' : 'pointer'});
      overlay.bind('click.fs', _close);
    }

  },
  
  _showFsInputBox = function() {

	    $('#fs-filter-box').show();
	    $('#nfs-input-box').hide();
	    if ($('#fs-dialog').has('#fs-summary-box').length  ) 
	    	$('#fs-summary-box').show();
	    $('#fs-nonfriend-help').hide();
	    $('#fs-user-list ul').show();
	    
	  },
  _showNfsInputBox = function() {

	    $('#fs-filter-box').hide();
	    $('#nfs-input-box').show();
	    if ($('#fs-dialog').has('#fs-summary-box').length ){
	    	$('#fs-summary-box').hide();
	  }
	   
	    $('#fs-user-list ul').hide();
	    

	  },
	  
	  _showNfsHelpPopup = function(){
		  
		   if ($('#nfs-help').css('display')=='none'){
			   $('#nfs-help').css('left','-0px');
			   $('#nfs-help').css('top','0px');
			   $('#nfs-help').show('1000');
			   $('#nfs-help').animate({	left:-365,top: 50},500);		   
		   }
		   else{
			   $('#nfs-help').animate({	left:0,top: 0},500);	
			   $('#nfs-help').hide('1000');
		   }
	  },
// called when a click on li is done
  _click = function(th) {
    var btn = th;
    		
    if ( btn.hasClass('checked') ) {

    	// find the original user in hte old container
    	var selected_id = $(btn).find('.fs-friends').val();

    	var hidden_element = $('#fs-user-list .fs-friends[value='+selected_id+']');
    	// show the original user in the old container
		$(hidden_element).parents('li').removeClass('selected').show();

    	// compltely remove the copied user from the new container
    	btn.remove();

		selected_friend_count--;
		
		if (selected_friend_count - 1 !== $('#fs-user-list li').length) {
			$('#fs-select-all').text(fsOptions.lang.buttonSelectAll);
		}
    }
    else {

      var limit_state = _limitText();
      
      if (limit_state === false) {
        return false;
      }

      selected_friend_count++;
      
      // add a 'checked' copy to the new container
      var element_copy= btn.clone();
      element_copy.addClass('checked');
      element_copy.find('input.fs-friends').attr('checked', true);
      $('#fs-selected-user-list ul').append(element_copy);
      // hide the  user from the main container
      btn.addClass('selected');
      btn.hide();
	// clear out the filter text box
	$('#fs-reset').trigger('click');
	$('#fs-input-text').focus();
    }

    var selected_height = $('#fs-selected-user-list').height();
    var results_height=0;
    if ($('#fs-search-results').length)
    	results_height = $('#fs-search-results').height();
    $('#fs-user-list').css('height', (fsOptions.userListHeight - selected_height-results_height).toString() + 'px');

    _enableContinueButton();
    //_showFriendCount();
  },
  
  _enableContinueButton = function() {
	  if (selected_friend_count>1)
		  $('#fs-continue-button').removeAttr('disabled');
	  else
		  $('#fs-continue-button').attr('disabled','disabled');

	  },

  _stopEvent = function() {

    $('#fs-reset').undelegate("click.fs");
    $('#fs-user-list li').undelegate("click.fs");
    selected_friend_count = 1;
    $('#fs-select-all').undelegate("click.fs");

  },

  _charLimit = function(word, limit){

    var wlen = word.length;

    if ( wlen <= limit ) {
      return word;
    }

    return word.substr(0, limit) + '...';

  },

  _find = function(t) {

    var fs_dialog = $('#fs-dialog');

    search_text_base = $.trim(t.val());
    	
    var search_text = search_text_base.toLowerCase().replace(/\s/gi, '+');
    var container = $('#fs-user-list ul');
    var elements =[]
    if (search_text=="")
    	container.children().not(".selected").show();
    else{
    	var elements = $('#fs-user-list .fs-fullname[value*='+search_text+']');
    	container.children().hide();
    	$.each(elements, function(){
    		$(this).parents('li').not(".selected").show();
    	});
    }
    var result_text = '';
    if ( elements.length > 0 && search_text_base > '' ){
      result_text = fsOptions.lang.summaryBoxResult.replace("{0}", '"'+t.val()+'"');
      result_text = result_text.replace("{1}", elements.length);
    }
    else{
      result_text = fsOptions.lang.summaryBoxNoResult.replace("{0}", '"'+t.val()+'"');
    }

    if (search_text_base===''){
    	$('#fs-search-results').html('')
    	$('#fs-search-results').css('display','none');
    	$('#fs-filter-box').css('padding-bottom','10px');
    }
    else{
    	$('#fs-search-results').html(result_text);
    	$('#fs-search-results').css('display','block');
    	$('#fs-filter-box').css('padding-bottom','5px');
    }
    // set height of nfs-input-box to same height as fs filter box
    var filter_box_height = $('#fs-filter-box').css('height');
    $('#nfs-input-box').css('height',filter_box_height);
    // adjust height of fs-user-list
    var search_results_height=0;
    if (search_text_base!='')
    	search_results_height = $('#fs-search-results').height();

    var selected_box_height = $('#fs-selected-user-list').height();
    var new_height=(fsOptions.userListHeight - search_results_height-selected_box_height).toString() + 'px';
    $('#fs-user-list').css('height',new_height);
    
    /*
    if ( !fs_dialog.has('#fs-summary-box').length ) {
      $('#fs-filter-box').after('<div id="fs-summary-box"><span id="fs-result-text">'+result_text+'</span></div>');
      // shorten the height of fs-user-list
      var list_height = $('#fs-user-list').css('height').slice(0,-2);
      var summary_box_height = $('#fs-summary-box').css('height').slice(0,-2);
      var new_height=(list_height-summary_box_height).toString() + 'px';
      $('#fs-user-list').css('height',new_height);
    }
    else if ( !fs_dialog.has('#fs-result-text').length ) {
      $('#fs-summary-box').prepend('<span id="fs-result-text">'+result_text+'</span>');
    }
    else {
      $('#fs-result-text').text(result_text);
    }

    if ( search_text_base === '' ){

      if ( fs_dialog.has('#fs-summary-box').length ){
     //   if ( selected_friend_count === 1 ){
          var list_height = $('#fs-user-list').css('height').slice(0,-2);
          var summary_box_height = $('#fs-summary-box').css('height').slice(0,-2);
          var new_height=(parseInt(list_height) + parseInt(summary_box_height)).toString() + 'px';
          $('#fs-user-list').css('height',new_height);
          $('#fs-summary-box').remove();
     //   }
     //   else{
     //     $('#fs-result-text').remove();
     //   }

      }
    }
   */

  },

  _resize = function( is_started ) {

    windowWidth = $(window).width();
    windowHeight = $(window).height();

    var docHeight = $(document).height(),
        wrapWidth = wrap.width(),
        wrapHeight = wrap.height(),
        wrapLeft = (windowWidth / 2) - (wrapWidth / 2),
        wrapTop = (windowHeight / 2) - (wrapHeight / 2);

    if ( is_started === true ) {
      overlay
        .css({
          'background-color' : fsOptions.overlayColor,
          'opacity' : fsOptions.overlayOpacity,
          'height' : docHeight
        })
        .fadeIn('fast', function(){
          wrap.css({
            left: wrapLeft,
            top: wrapTop
          })
          .fadeIn();
        });
    }
    else{
      wrap
        .stop()
        .animate({
          left: wrapLeft,
          top: wrapTop
        }, 200);

      overlay.css({'height': docHeight});
    }
    // set height of user list to whatever was passed in
    $('#fs-user-list').css('height',fsOptions.userListHeight.toString() + 'px');
  },

  _shuffleData = function( array_data ) {
    for (var j, x, i = array_data.length; i; j = parseInt(Math.random() * i, 10), x = array_data[--i], array_data[i] = array_data[j], array_data[j] = x);
    return array_data;
  },

  _limitText = function() {
    if ( selected_friend_count > fsOptions.max && fsOptions.max !== null ) {
      var selected_limit_text = fsOptions.lang.selectedLimitResult.replace('{0}', fsOptions.max);
      $('.fs-limit').html('<span class="fs-limit fs-full">'+selected_limit_text+'</span>');
      return false;
    }
  },

  /*
  _showFriendCount = function() {
    if ( selected_friend_count > 1 && fsOptions.showSelectedCount === true ){
    
      var selected_count_text = fsOptions.lang.selectedCountResult.replace('{0}', (selected_friend_count-1));

      if ( !$('#fs-dialog').has('#fs-summary-box').length ) {
        $('#fs-filter-box').after('<div id="fs-summary-box"><span class="fs-limit fs-count">'+selected_count_text+'</span><a href="javascript:{}" id="fs-show-selected">'+fsOptions.lang.buttonShowSelected+'</a></div>');
      
      }
      else if ( !$('#fs-dialog').has('.fs-limit.fs-count').length ) {
        $('#fs-summary-box').append('<span class="fs-limit fs-count">'+selected_count_text+'</span>');
      }
      else{
        $('.fs-limit').text(selected_count_text);
      }
    }
    else{

     if ( search_text_base === '' ){
    	 var container = $('#fs-user-list ul');
    	   container.children().show();

    	 $('#fs-summary-box').remove();
      }
      else{
        $('.fs-limit').remove();
      }

    }
  },
*/
  /*
  _resetSelection = function() {
    $('#fs-user-list li').removeClass('checked');
    $('#fs-user-list input.fs-friends').attr('checked', false);
    
    selected_friend_count = 1;
  },
  */

  /*
  _selectAll = function() {
    if (fsOptions.showButtonSelectAll === true && fsOptions.max === null) {
      $('#fs-show-selected').before('<a href="javascript:{}" id="fs-select-all"><span>'+fsOptions.lang.buttonSelectAll+'</span></a> - ');
      
      wrap.delegate('#fs-select-all', 'click.fs', function() {
        if (selected_friend_count - 1 !== $('#fs-user-list li').length) {

          $('#fs-user-list li:hidden').show();
          _resetSelection();

          $('#fs-user-list li').each(function() {
            _click($(this));
          });
                
          $('#fs-select-all').text(fsOptions.lang.buttonDeselectAll);

          if (isShowSelectedActive === true) {
            isShowSelectedActive = false;
            $('#fs-show-selected').text(fsOptions.lang.buttonShowSelected);
          }
          
        }
        else {
          _resetSelection();
          
          //_showFriendCount();
          
          $('#fs-select-all').text(fsOptions.lang.buttonSelectAll);
        }
      });
      
    }
  },
*/
  /*
  _showSelected = function(t) {
    var container = $('#fs-user-list ul'),
        allElements = container.find('li'),
        selectedElements = container.find('li.checked');
    
    if (selectedElements.length !== 0 && selectedElements.length !== allElements.length || isShowSelectedActive === true) {
      if (isShowSelectedActive === true) {
        t.removeClass('active').text(fsOptions.lang.buttonShowSelected);   
        var text_box_value=$('#fs-input-text').val();
        if (text_box_value!==fsOptions.lang.searchText)
        	_find($('#fs-tab-view input'));
        else
        	container.children().show();
        isShowSelectedActive = false;
      }
      else {

        t.addClass('active').text(fsOptions.lang.buttonShowAll);    
        container.children().hide();
        $.each(selectedElements, function(){
          $(this).show();
        });  
        isShowSelectedActive = true;
      }
    }
     
  },
  */
  defaults = {
	accessToken: null, // used to get facebook graph api data
	facebookID:null,
    malePref: false, // pass in values: true (male), false (female), null (both)
    maleGender: true,
    minimum_samegender_friends:4,
    minimum_crushgender_friends:4,
    userListHeight:295,
    max: null,
    excludeIds: "",
    getStoredFriends: [],
    closeOverlayClick: true,
    enableEscapeButton: true,
    overlayOpacity: "0.3",
    overlayColor: '#000',
    closeOnSubmit: false,
    showSelectedCount: true,
    showButtonSelectAll: false,
    setupSelect:false,// setup mode - no confirmation tab view
    color: "default",
    lang: {
      title: "Friend Selector",
      buttonSubmit: "Send",
      buttonContinue: "Confirm",
      buttonCancel: "Cancel",
      buttonSelectAll: "Select All",
      buttonDeselectAll: "Deselect All",
      buttonShowSelected: "Show Selected",
      buttonShowAll: "Show All",
      summaryBoxResult: "{1} filtered results for {0}",
      summaryBoxNoResult: "No results for {0}",
      searchText: "Enter a friend's name",
      nonFriendSearchText: "Enter a unique facebook user id",
      fbConnectError: "You must be logged in to Facebook in order to use this feature.",
      ajaxError: "Sorry, there is a problem with our servers.  We are working to fix this problem a.s.a.p.",
      selectedCountResult: "You have choosen {0} people.",
      selectedLimitResult: "Limit is {0} people.",
      facebookInviteMessage: "Invite message"
    },
    maxFriendsCount: null,
    showRandom: false,
    facebookInvite: false,
    onStart: function(response){  return null; },
    onClose: function(response){ return null; },
    onSubmit: function(response){ return null; },
    onError: function(response){ return null; },
  };

})(window, document, jQuery);