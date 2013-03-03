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

  var fsOptions = {},
  running = false, isShowSelectedActive = false,
  windowWidth = 0, windowHeight = 0, selected_friend_count = 1,
  search_text_base = '',
  
  num_connect_tries = 0, // for facebook connect to try mutliple times if errors
  
  content, wrap, overlay,
  fbDocUri = 'http://developers.facebook.com/docs/reference/javascript/',

  _start = function() {

    if ( FB === undefined ){
      alert('Facebook integration is not defined. View ' + fbDocUri);
      return false;
    }

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

	$("#fs-user-list").append('<div id="fs-loading"></div>');
	$("#fs-select-view #site-overlay").css('visibility','visible');
    var username=$("#nfs-input-text").val();// get the text from the nfs-input-text box
    // see if user exists
    $.get("/ajax_find_fb_user/", {username:username},
    	  function(response){
    		if ('error_message' in response) {
    			alert(response.error_message);
    			$("#fs-select-view #site-overlay").css('visibility','hidden');
    	        $('#fs-loading').remove();
    			return false;
    		}
    		else {
 
    	    	// find the original user in hte old container
    	    	var selected_id = response.id + response.friend_type;
    			var duplicate_element = $('#fs-selected-user-list .fs-friends[value='+selected_id+']');
    			console.log("duplicate?",duplicate_element);

    	    	if ($(duplicate_element).length > 0){
    	    		alert("You already selected this person");
    	    		$("#fs-select-view #site-overlay").css('visibility','hidden');
    	    		$('#fs-loading').remove();
    	    		return false;
    			}

    			_addValidUsername(response);
    	        selected_friend_count++;
    	        _enableContinueButton();
    			$('#nfs-input-text').val("");
    			$("#fs-select-view #site-overlay").css('visibility','hidden');
    	        $('#fs-loading').remove();
    		} 			
    }).fail(function(responseText,textStatus,XHR){
		if (responseText.responseText.indexOf("HTTPError") != -1)
			fsOptions.onHTTPError();
		else
			alert(fsOptions.ajaxError);
    	$("#fs-select-view #site-overlay").css('visibility','hidden');
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

      $('#fs-dialog-title').html("<span>Confirm your selections step 2 of 2</span>");
      $('#fs-continue-button').hide();
      $('#fs-submit-button').show();
      $('#fs-terms-checkbox').show();
      $('#fs-terms-checkbox').next().show();
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

      $('#fs-dialog-title').html("<span>" + fsOptions.lang.title + "</span>");
      $('#fs-continue-button').show();
      $('#fs-submit-button').hide();
      $('#fs-terms-checkbox').hide();
      $('#fs-terms-checkbox').next().hide();
      $('#fs-back-button').hide();
      $('#fs-select-view').show();
      $('#fs-confirm-view').hide();
      $('#fs-confirm-user-list').children().remove();
	  
	  // and the big one, show all of the selected users broken out into friend type
	  
  },

  _submit = function() {

	// ensure the terms & conditions checkbox is checked
	 
	if (!$('#fs-terms-checkbox').is(':checked')){
		alert("You can proceed without agreeing to the Terms & Conditions.");
		return false;
  }
    var selected_friends = [];
    $('input.fs-friends:checked').each(function(){
      var id = $(this).val();
      selected_friends.push(parseInt(id, 10));
    });

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
    else{
      fsOptions.onSubmit(selected_friends);

      if ( fsOptions.closeOnSubmit === true ) {
        _close();
      }
    }

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

    wrap.append('<div class="fs-dialog-box-bg" id="fs-dialog-box-bg-n"></div><div class="fs-dialog-box-bg" id="fs-dialog-box-bg-ne"></div><div class="fs-dialog-box-bg" id="fs-dialog-box-bg-e"></div><div class="fs-dialog-box-bg" id="fs-dialog-box-bg-se"></div><div class="fs-dialog-box-bg" id="fs-dialog-box-bg-s"></div><div class="fs-dialog-box-bg" id="fs-dialog-box-bg-sw"></div><div class="fs-dialog-box-bg" id="fs-dialog-box-bg-w"></div><div class="fs-dialog-box-bg" id="fs-dialog-box-bg-nw"></div>');
    wrap.append(
      content = $('<div id="fs-dialog-box-content"></div>')
    );

    var container = '<div id="fs-dialog" class="fs-color-'+fsOptions.color+'">' +
                      '<h2 id="fs-dialog-title"><span>'+fsOptions.lang.title+'</span></h2>' +
                      
                      
                      '<div id="fs-select-view"><div id="site-overlay"></div>' +
                      
	                      '<a href="javascript:{}" id="fs-tab" class="fs-button"><span>Friend</span></a>' +
		                  '<a href="javascript:{}" id="nfs-tab" class="fs-button"><span>Non-Friend</span></a>' +
	                      
	                      '<div id="fs-filter-box">' +
	                        '<div id="fs-input-wrap">' +
	                          '<input type="text" id="fs-input-text" title="'+fsOptions.lang.searchText+'" />' +
	                          '<a href="javascript:{}" id="fs-reset">Reset</a>' +
	                        '</div>' +
	                      '</div>' +
	                      
	                      
	                      '<div id="nfs-input-box">' +
	                      	'Enter Crush\'s Facebook Username:' +
	                        '<div id="anfs-input-wrap">' +
	                          '<span>https://facebook.com/</span>' +
	                          '<input type="text" id="nfs-input-text" title="'+fsOptions.lang.nonFriendSearchText+'" />' +
	                          '<a href="javascript:{}" id="fs-reset">Reset</a>' +
	                        '<a href="javascript:{}" id="fs-select-button" class="fs-button"><span>Select</span></a>' +
	                        '</div>' +
	                      '</div>' +
	                      
	                      '<div id="fs-selected-user-list">' +
	                      	'<ul></ul>' +
	                      '</div>' +    
	                      
	                      '<div id="fs-user-list">' +
	                        '<div id="fs-nonuser-help">' +
	                        '<h3>Where is the facebook user id?</h3>' +
	                        '1) Navigate to your crush\'s facebook page (on facebook.com)<br>' +
	                        '2) Locate the navigation / address bar at the top of your browser<br>' + 
	                        '3) Extract the text following \'www.facebook.com/\'.<br>' +

	                        'In the above example, the Facebook user id is \'JessicaAlba\' (highlighted in red).' +
	                      '</div>' +
	                        '<ul></ul>' +
	                      '</div>' +
     

	                      
	                  '</div>' +// close off fs-select-view +
	                  
	                  '<div id="fs-confirm-view">' +
	                      	'<div id="fs-confirm-user-list">' +
	                    	'</div>' +
	                  '</div>' + // close off fs-confirm view
		                      
	                  '<div id="fs-dialog-buttons">' +
	                  
	                  		'<input id="fs-terms-checkbox" type="checkbox" checked="checked"/><span>I agree to the <a href="/terms" target="_blank">terms & conditions</a></span>' +
	                  		'<a id="fs-back-button"  href="javascript://">Back</a>' +
	                  
	                      '<button href="javascript:{}" id="fs-continue-button" class="fs-button" disabled><span>Confirm</span></button>' +
	                      '<a href="javascript:{}" id="fs-submit-button" class="fs-button"><span>Select</span></a>' +
	                      '<a href="javascript:{}" id="fs-cancel-button" class="fs-button"><span>'+fsOptions.lang.buttonCancel+'</span></a>' +
	                  '</div>' +
     
	                '</div>'; // close off fs-dialog

    //

    content.html(container);
    $('#nfs-input-box').hide();
    $('#fs-nonuser-help').hide();
    $('#fs-terms-checkbox').hide();
    $('#fs-terms-checkbox').next().hide();
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
	  
	  	// process the ids of excluded friends into a syntax that FQL understands (comma delimited list)
	    
	    var fql_query = "";
	    // initialize fql query and add any exclude ids if provided as an argument
	    if (fsOptions.excludeIds !==""){
	    	//alert (fsOptions.excludeIds);
	    	fql_query += "SELECT uid, name FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = " + fsOptions.facebookID + " AND NOT (uid2 IN (" + fsOptions.excludeIds + ")))";	
	    }
	    else {
	    	fql_query += "SELECT uid, name FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = " + fsOptions.facebookID + ")";
	    }
	    // add gender preference
	    if (fsOptions.malePref !== null){
		    var genderPref = "Female";
	    	if (fsOptions.malePref===true)
	    		genderPref="Male";
	    	fql_query += " AND sex='" + genderPref + "'";
	    }	    
	    // add order info
	    fql_query += " ORDER BY name";
	 	    
	  //alert("fql_query_string: " + fql_query);
	  FB.api('fql',{q:fql_query}, function(response) {
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
	  				alert(fsOptions.lang.fbConnectError);
	  		        location.href="/facebook/login";
	  		        //_close();
	  		        return false;
	  			}
	  		}
	  		else {
	  			_buildFacebookFriendGrid(response);  	
	  	    	}
	  }); // close fb.api call 
  },
    
  _buildFacebookFriendGrid = function(response) {
	  
      var facebook_friends = response.data;
      var item,person,link;
      // don't allow users with less than 4 friends of same sex to add any type of crush
      if (facebook_friends.length < 0) {
    	  alert("Sorry, but you do not have the minimum number of Facebook friends required to use this feature.");
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

      $('#fs-loading').remove();


  },
  
  _buildConfirmView = function() {
		
	  var friend1_elements = $('#fs-selected-user-list li').filter('#friend-type1');
	  var friend2_elements = $('#fs-selected-user-list li').filter('#friend-type2');
	  var friend0_elements = $('#fs-selected-user-list li').not('#friend-type2').not('#friend-type1');
	  //alert("friend-count:" + $(friend0_elements).length + " friend_of_Friend_count:" + $(friend1_elements).length + " non_Friend_count:" + $(friend2_elements).length);
	  
	  var container = $('#fs-confirm-user-list'); 
	// build friend list  
	  if (friend0_elements.length > 0) {
		  var new_html = '<h2>Selected Friends (' + friend0_elements.length + ')</h2><ul>';
	
		  $.each(friend0_elements, function(){
	    		var duplicate = $(this).clone();
	    		duplicate.find('input').remove();
	    		new_html += duplicate.html();
	    	});
		  new_html+='</ul>';
		  container.append(new_html);
	  }
	  
  	// build friend-of-friend list
	  if (friend1_elements.length > 0) {
		  var new_html = '<h2>Selected Friends-of-Friends (' + friend1_elements.length + ')</h2><ul>';
			
		  $.each(friend1_elements, function(){
	    		var duplicate = $(this).clone();
	    		duplicate.find('input').remove();
	    		new_html += duplicate.html();
	    	});
		  new_html+='</ul>';
		  container.append(new_html);
	  }
	  
  	
  	// build non-friend list
	  if (friend2_elements.length > 0) {
		  var new_html = '<h2>Selected Non-Friend Users (' + friend2_elements.length + ')</h2><ul>';
			
		  $.each(friend2_elements, function(){
	    		var duplicate = $(this).clone();
	    		duplicate.find('input').remove();
	    		new_html += duplicate.html();
	    	});
		  new_html+='</ul>';
		  container.append(new_html);
	  }

  },

  _initEvent = function() {
  
    wrap.delegate('#fs-cancel-button', 'click.fs', function(){
      _close();
    });
    
    wrap.delegate('#fs-submit-button', 'click.fs', function(){
      _submit();
    });
    
    wrap.delegate('#fs-continue-button', 'click.fs', function(){
        _continue();
      });
    
    wrap.delegate('#fs-back-button', 'click.fs', function(){
        _back();
      });
    
    wrap.delegate('#fs-select-button', 'click.fs', function(){
        _selectUsername();
      });
    
    $('#fs-dialog').on("click","#nfs-tab", function(e){
        _showNfsInputBox($(this));
      });
    
    $('#fs-dialog').on("click","#fs-tab", function(e){
        _showFsInputBox($(this));
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

    $('#nfs-input-box').keypress(function(event) {
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
	    $('#fs-nonuser-help').hide();
	    $('#fs-user-list ul').show();
	    
	  },
  _showNfsInputBox = function() {

	    $('#fs-filter-box').hide();
	    $('#nfs-input-box').show();
	    if ($('#fs-dialog').has('#fs-summary-box').length ){
	    	$('#fs-summary-box').hide();
	  }
	   
	    $('#fs-user-list ul').hide();
	    $('#fs-nonuser-help').show();

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
    }
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


    if ( !fs_dialog.has('#fs-summary-box').length ) {
      $('#fs-filter-box').after('<div id="fs-summary-box"><span id="fs-result-text">'+result_text+'</span></div>');
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
          $('#fs-summary-box').remove();
     //   }
     //   else{
     //     $('#fs-result-text').remove();
     //   }

      }
    }

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
    color: "default",
    lang: {
      title: "Friend Selector",
      buttonSubmit: "Send",
      buttonCancel: "Cancel",
      buttonSelectAll: "Select All",
      buttonDeselectAll: "Deselect All",
      buttonShowSelected: "Show Selected",
      buttonShowAll: "Show All",
      summaryBoxResult: "{1} best results for {0}",
      summaryBoxNoResult: "No results for {0}",
      searchText: "Enter a friend's name",
      nonFriendSearchText: "username",
      fbConnectError: "You must be logged in to Facebook in order to use this feature.",
      ajaxError: "Sorry, there is a problem with our servers.  We are working to fix this problem a.s.a.p.",
      selectedCountResult: "You have choosen {0} people.",
      selectedLimitResult: "Limit is {0} people.",
      facebookInviteMessage: "Invite message"
    },
    maxFriendsCount: null,
    showRandom: false,
    facebookInvite: false,
    onStart: function(response){ return null; },
    onClose: function(response){ return null; },
    onSubmit: function(response){ return null; },
    onHTTPError: function(response){location.href='/facebook/login';},
  };


  $.fn.fSelector = function ( options ) {
    this.unbind("click.fs");
    this.bind("click.fs", function(){
      fsOptions = options;
      _start();
    });
    return this;

  };

})(window, document, jQuery);