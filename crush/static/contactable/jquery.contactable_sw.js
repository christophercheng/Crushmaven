/*
 * contactable 1.2.1 - jQuery Ajax contact form
 *
 * Copyright (c) 2009 Philip Beel (http://www.theodin.co.uk/)
 * Dual licensed under the MIT (http://www.opensource.org/licenses/mit-license.php) 
 * and GPL (http://www.opensource.org/licenses/gpl-license.php) licenses.
 *
 * Revision: $Id: jquery.contactable.js 2010-01-18 $
 *
 */
 
//extend the plugin
(function($){

	//define the new for the plugin ans how to call it	
	$.fn.contactable = function(options) {
		//set default options  
		var defaults = {
			message : 'Message',
			subject : 'A contactable message',
			submit : 'SEND',
			recievedMsg : 'Thank you for your message.',
			notRecievedMsg : 'Sorry, your message could not be sent.<BR><BR>Please try again.',
			disclaimer: "Have a suggestion or comment? <BR>&nbsp;&nbspLet us know!",
			hideOnSubmit: false

		};
		//call in the default otions
		var options = $.extend(defaults, options);
		//act upon the element that is passed into the design    
		return this.each(function() {
			//construct the form
			var this_id_prefix = '#'+this.id+' ';
			$(this).html('<div id="contactable_inner">Feedback</div><form id="contactForm"><div id="loading"></div><div id="callback"></div><div class="holder"><p class="disclaimer">'+options.disclaimer+'</p><textarea maxlength="500" id="message" required name="message" class="message" rows="10" cols="25" ></textarea><input type="submit" class="submit" value="'+options.submit+'"/></div></form>');
			//show / hide function
			$(this_id_prefix+'div#contactable_inner').click(function(){
				var fromMarginBottom = parseInt($(this_id_prefix+'#contactForm').css('marginBottom'));
				// fromMarginBottom is a hack to determine if the form is visible or not.  after jquery 1.8.3, the toggle() button was changed so this is the workaround
				if (fromMarginBottom < -100){
					$(this).animate({"marginBottom": "-=5px"}, "fast").animate({"marginBottom": "+=250px"}, "fast");
					$(this_id_prefix+'#contactForm').animate({"marginBottom": "-=0px"}, "fast").animate({"marginBottom": "+=320px"}, "fast"); 
				}
				else {
					$(this_id_prefix+'#contactForm').animate({"marginBottom": "-=320px"}, "fast");
					$(this).animate({"marginBottom": "-=250px"}, "fast").animate({"marginBottom": "+=5px"}, "fast"); 
				}
			}); // close off .click
				
			$(this_id_prefix+'#message').click(function(){
					var border=$(this_id_prefix+'#message').css("border-color");
					$(this_id_prefix+'#message').css("border-width","0px").css("border-color","white");
					//if (border=="rgb(255, 0, 0)")
					//	$(this_id_prefix+'#message').css("border-width","0px").css("border-color","white");
					// set text area background to white if it is not already
				});
			
			$(this_id_prefix+'input').click(function(){
				// if text area is empty, then simply change the background color of text area
				var message=$(this_id_prefix+'#message').val();

				if (message==''){	
					$(this_id_prefix+'#message').css("border-width","2px").css("border-color","red");
					return;
				}
				$(this_id_prefix+'.holder').hide();
				$(this_id_prefix+'#loading').show();
				// if text area is not empty, then do the following:
					// call ajax function to submit comment
						// show the loading form

				$.ajax({
					  type: 'POST',
					  url: '/ajax_submit_feedback/',
					  data: {message:$(this_id_prefix+'#message').val(),csrfmiddlewaretoken:options.csrf_token},
					  success: function(data){

						  $(this_id_prefix+'#loading').css({display:'none'}); 		
						  $(this_id_prefix+'#callback').show().append(options.recievedMsg);
						  
						  setTimeout(function(){
							  if ($(this_id_prefix+'#contactForm').css("margin-bottom")=='-50px')  
								  $(this_id_prefix+'#contactable_inner').trigger('click');	  
						  },1500);
						  setTimeout(function(){	  
							  $(this_id_prefix+'#message').val('');
							  $(this_id_prefix+'.holder').show();
							  $(this_id_prefix+'#callback').hide().html('');
							 
						  },2000);
					  }, 
					  error:function(){
						$(this_id_prefix+'#loading').css({display:'none'}); 
						$(this_id_prefix+'#callback').show().append(options.notRecievedMsg);
						setTimeout(function(){
							$(this_id_prefix+'.holder').show();
							$(this_id_prefix+'#callback').hide().html('');
						},3000);
                    }
				}); // close off $.ajax
				return false;
			}); // close off $(this_id_prefix+'input').click
		}); // close off return this.each(function() {
	}; // close off $.fn.contactable = function(options) {
 
})(jQuery);
	

