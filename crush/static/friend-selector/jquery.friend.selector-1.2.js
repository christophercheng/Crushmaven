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
	$("#nfs-user-list").append('<div id="fs-loading"></div>');
    var username=$("#nfs-input-text").val();// get the text from the nfs-input-text box
    // see if user exists
    $.get("/ajax_find_fb_user/", {username:username},
    	  function(response){
    		console.log(response);
    		if ('error_message' in response) {
    			alert(response.error_message);
    	        $('#fs-loading').remove();
    			return false;
    		}
    		else {
    			_addValidUsername(response);
    			$('#nfs-input-text').val("");
    	        $('#fs-loading').remove();
    		} 			
    });
},

  _addValidUsername  = function(userData){
        var item = $('<li/>');
        var link = userData.name;

        var link =  '<img class="fs-thumb" src="https://graph.facebook.com/'+ userData.id + '/picture" />' +
                     '<span class="fs-name">' + _charLimit(userData.name, 15) + '</span>'

        item.append(link);
        $('#nfs-user-list ul').append(item);
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

  _submit = function() {

    var selected_friends = [];
    $('input.fs-friends:checked').each(function(){
      var splitId = $(this).val().split('-');
      var id = splitId[1];
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

                      '<div id="fs-tab-container">' +
                      
	                    '<a href="javascript:{}" id="fs-tab" class="fs-button"><span>Friend</span></a>' +
	                    '<a href="javascript:{}" id="nfs-tab" class="fs-button"><span>Non-Friend</span></a>' +
           
                      	'<div id="fs-tab-view">' +
                      
		                      '<div id="fs-filter-box">' +
		                        '<div id="fs-input-wrap">' +
		                          '<input type="text" id="fs-input-text" title="'+fsOptions.lang.searchText+'" />' +
		                          '<a href="javascript:{}" id="fs-reset">Reset</a>' +
		                        '</div>' +
		                      '</div>' +
		                      
		                      '<div id="fs-user-list">' +
		                        '<ul></ul>' +
		                      '</div>' +
		                      
		                  '</div>' +  // close fs-tab-view
	
	                      '<div id="nfs-tab-view">' +
	                        
		                      '<div id="nfs-input-box">' +
		                      	'Enter Crush\'s Facebook Username:' + '<a href="#" id="nfs-help">what\'s this?</a>' +
		                        '<div id="anfs-input-wrap">' +
		                          '<span>https://facebook.com/</span>' +
		                          '<input type="text" id="nfs-input-text" title="'+fsOptions.lang.nonFriendSearchText+'" />' +
		                          '<a href="javascript:{}" id="fs-reset">Reset</a>' +
		                        '<a href="javascript:{}" id="fs-select-button" class="fs-button"><span>Select</span></a>' +
		                        '</div>' +
		                      '</div>' +
			                      
		                      '<div id="nfs-user-list">' +
		                        '<ul></ul>' +
		                      '</div>' + // close nfs-user-list
		                      
		                  '</div>' +  // close nfs-tab-view
		                  
	                  '</div>' + // close fs-tab-container
	                      
                    '<div id="fs-dialog-buttons">' +
                      '<a href="javascript:{}" id="fs-submit-button" class="fs-button"><span>'+fsOptions.lang.buttonSubmit+'</span></a>' +
                      '<a href="javascript:{}" id="fs-cancel-button" class="fs-button"><span>'+fsOptions.lang.buttonCancel+'</span></a>' +
                    '</div>' +
                '</div>';


    content.html(container);
    $('#fs-tab-view').children().hide();
    $('#fs-user-list').append('<div id="fs-loading"></div>');
    _getFacebookFriends();
    _resize(true);
    _initEvent();
    _selectAll();

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
	  			if (num_connect_tries < 5) 	
	  				setTimeout(function () {
	  					_getFacebookFriends();
	  				}, 400); // if error connecting to facebook, wait .4 milliseconds before trying again
	  			else // too many tries - give up
	  			{
	  		        alert(fsOptions.lang.fbConnectError);
	  		        _close();
	  		        return false;
	  			}
	  		}
	  		else {
	  			_buildFacebookFriendGrid(response);  	
	  	    	}
	  }); // close fb.api call 
  },
    
  _buildFacebookFriendGrid = function(response) {
	  console.log(response);//remove this later
	  
      var facebook_friends = response.data;
      var item,person,link;
      
      for (var j = 0; j < facebook_friends.length; j++) {

        if ($.inArray(parseInt(facebook_friends[j], 10), fsOptions.excludeIds) >= 0) 
          continue;

          item = $('<li/>');
          person = facebook_friends[j]
          link =  '<a class="fs-anchor" href="javascript://">' +
                        '<input class="fs-fullname" type="hidden" name="fullname[]" value="'+person.name.toLowerCase().replace(/\s/gi, "+")+'" />' +
                        '<input class="fs-friends" type="checkbox" name="friend[]" value="fs-'+person.uid+'" />' +
                        '<img class="fs-thumb" src="https://graph.facebook.com/'+person.uid+'/picture" />' +
                        '<span class="fs-name">' + _charLimit(person.name, 15) + '</span>' +
                      '</a>';

          item.append(link);

          $('#fs-user-list ul').append(item);

      }

      $('#fs-loading').remove();


  },

  _initEvent = function() {
  
    wrap.delegate('#fs-cancel-button', 'click.fs', function(){
      _close();
    });
    
    wrap.delegate('#fs-submit-button', 'click.fs', function(){
      _submit();
    });
    
    wrap.delegate('#fs-select-button', 'click.fs', function(){
        _selectUsername();
      });
    
    $('#fs-dialog').on("click","#nfs-tab", function(e){
        _showNfsTab($(this));
      });
    
    $('#fs-dialog').on("click","#fs-tab", function(e){
        _showFsTab($(this));
      });
    
    $('#fs-dialog input').focus(function(){
      if ($(this).val() === $(this)[0].title){
        $(this).val('');
      }
    }).blur(function(){
      if ($(this).val() === ''){
        $(this).val($(this)[0].title);
      }
    }).blur();


    $('#fs-tab-view input').keyup(function(){
      _find($(this));
    });


    wrap.delegate('#fs-reset', 'click.fs', function() {
      $('#fs-input-text').val('');
      _find($('#fs-tab-view input'));
      $('#fs-input-text').blur();
    });


    wrap.delegate('#fs-user-list li', 'click.fs', function() {
      _click($(this));
    });
    
    $('#fs-dialog').on("click","#fs-show-selected", function(e){
        _showSelected($(this));
      });
    

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
  
  _showFsTab = function() {

	    $('#fs-tab-view').children().show();
	    $('#nfs-tab-view').children().hide();

	  },
  _showNfsTab = function() {

	    $('#fs-tab-view').children().hide();
	    $('#nfs-tab-view').children().show();

	  },

  _click = function(th) {
    var btn = th;

    if ( btn.hasClass('checked') ) {

      btn.removeClass('checked');
      btn.find('input.fs-friends').attr('checked', false);

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

      btn.addClass('checked');
      btn.find('input.fs-friends').attr('checked', true);
    }

    _showFriendCount();
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
    	container.children().show();
    else{
    	var elements = $('#fs-user-list .fs-fullname[value*='+search_text+']');
    	container.children().hide();
    	$.each(elements, function(){
    		$(this).parents('li').show();
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

        if ( selected_friend_count === 1 ){
          $('#fs-summary-box').remove();
        }
        else{
          $('#fs-result-text').remove();
        }

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

  _resetSelection = function() {
    $('#fs-user-list li').removeClass('checked');
    $('#fs-user-list input.fs-friends').attr('checked', false);
    
    selected_friend_count = 1;
  },

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
          
          _showFriendCount();
          
          $('#fs-select-all').text(fsOptions.lang.buttonSelectAll);
        }
      });
      
    }
  },

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
      fbConnectError: "Sorry, there is a problem connecting to Facebook.  Please try again later.",
      selectedCountResult: "You have choosen {0} people.",
      selectedLimitResult: "Limit is {0} people.",
      facebookInviteMessage: "Invite message"
    },
    maxFriendsCount: null,
    showRandom: false,
    facebookInvite: false,
    onStart: function(response){ return null; },
    onClose: function(response){ return null; },
    onSubmit: function(response){ return null; }
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