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
			recievedMsg : 'Thank you for your message',
			notRecievedMsg : 'Sorry but your message could not be sent, try again later',
			disclaimer: "Have a suggestion or comment? <BR>&nbsp;&nbspWe'd love to hear from you...",
			hideOnSubmit: false

		};

		//call in the default otions
		var options = $.extend(defaults, options);
		//act upon the element that is passed into the design    
		return this.each(function() {
			//construct the form
			var this_id_prefix = '#'+this.id+' ';
			$(this).html('<div id="contactable_inner"></div><form id="contactForm" method="" action=""><div id="loading"></div><div id="callback"></div><div class="holder"><p class="disclaimer">'+options.disclaimer+'</p><textarea maxlength="500" id="message" required name="message" class="message" rows="8" cols="25" ></textarea><input class="submit" type="submit" value="'+options.submit+'"/></div></form>');
			
			//show / hide function
			$(this_id_prefix+'div#contactable_inner').toggle(function() {
				$(this_id_prefix+'#overlay').css({display: 'block'});
				$(this).animate({"marginRight": "-=5px"}, "fast"); 
				$(this_id_prefix+'#contactForm').animate({"marginRight": "-=0px"}, "fast");
				$(this).animate({"marginRight": "+=380px"}, "slow"); 
				$(this_id_prefix+'#contactForm').animate({"marginRight": "+=380px"}, "slow"); 
			}, 
			function() {
				$(this_id_prefix+'#contactForm').animate({"marginRight": "-=380px"}, "slow");
				$(this).animate({"marginRight": "-=380px"}, "slow").animate({"marginRight": "+=5px"}, "fast"); 
				$(this_id_prefix+'#overlay').css({display: 'none'});
			});
			
			$(this_id_prefix+'#message').click(function(){
				var border=$(this_id_prefix+'#message').css("border-color");
				if (border=="rgb(255, 0, 0)")
					$(this_id_prefix+'#message').css("border-width","0px").css("border-color","white");
				// set text area background to white if it is not already
			});
			
			
			$(this_id_prefix+'input').click(function(){
				// if text area is empty, then simply change the background color of text area
				var message=$(this_id_prefix+'#message').val();

				if (message=='')
					$(this_id_prefix+'#message').css("border-width","2px").css("border-color","red");
					return;
				$(this_id_prefix+'.holder').hide();
				$(this_id_prefix+'#loading').show();
				// if text area is not empty, then do the following:
					// call ajax function to submit comment
						// show the loading form
				
					// once ajax function succeeds, then send thank you message, then auto close the dialog
				
					// if ajax function errors out, then show error message, then show the holder once more
				//$(this_id_prefix+'.holder').hide();
				//$(this_id_prefix+'#loading').show();
			});
			
		}); // close offreturn this.each(function() {
	}; // close off $.fn.contactable = function(options) {
 
})(jQuery);
			
/*			
			
			//validate the form 
			$(this_id_prefix+"#contactForm").validate({
				//set the rules for the fild names
				rules: {
					message: {
						required: true
					}
				},
				//set messages to appear inline
					messages: {
						name: "",
						email: "",
						message: ""
					},			

				submitHandler: function() {
					$(this_id_prefix+'.holder').hide();
					$(this_id_prefix+'#loading').show();
$.ajax({
  type: 'POST',
  url: options.url,
  data: {subject:options.subject, name:$(this_id_prefix+'#name').val(), email:$(this_id_prefix+'#email').val(), message:$(this_id_prefix+'#message').val()},
  success: function(data){
						$(this_id_prefix+'#loading').css({display:'none'}); 
						if( data == 'success') {
							$(this_id_prefix+'#callback').show().append(options.recievedMsg);
							if(options.hideOnSubmit == true) {
								//hide the tab after successful submition if requested
								$(this_id_prefix+'#contactForm').animate({dummy:1}, 2000).animate({"marginRight": "-=450px"}, "slow");
								$(this_id_prefix+'div#contactable_inner').animate({dummy:1}, 2000).animate({"marginRight": "-=447px"}, "slow").animate({"marginRight": "+=5px"}, "fast"); 
								$(this_id_prefix+'#overlay').css({display: 'none'});	
							}
						} else {
							$(this_id_prefix+'#callback').show().append(options.notRecievedMsg);
							setTimeout(function(){
								$(this_id_prefix+'.holder').show();
								$(this_id_prefix+'#callback').hide().html('');
							},2000);
						}
					},
  error:function(){
						$(this_id_prefix+'#loading').css({display:'none'}); 
						$(this_id_prefix+'#callback').show().append(options.notRecievedMsg);
                                        }
});		
				}//close off submit handler
			}); // close off $(this_id_prefix+"#contactForm").validate({

*/		
		

