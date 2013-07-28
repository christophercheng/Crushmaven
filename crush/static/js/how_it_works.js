
/* --------- HANDLE HOW TO SECTION CLICKS ----------------- */
jQuery(document).ready(function($) {
$('.how_to_link').click(function(event){
        if ($(this).hasClass('how_to_link_active'))
                return;
        
        var active_slide=$('.active_how_to_slide');     
        var inactive_slide=$('.inactive_how_to_slide');
        var slide_container=$('.how_to_slide_container');

        // stop and fast forward any ongoing animations 
        active_slide.stop(true,false);
        inactive_slide.stop(true,false);
        slide_container.finish();
        
        var bForSingles = true;
        if ($(this).hasClass('for_singles')){
                active_slide=$('#how_to_slide_setup');
                inactive_slide=$('#how_to_slide_singles');
                var new_height='410';
        }
        else{
                active_slide=$('#how_to_slide_singles');
                inactive_slide=$('#how_to_slide_setup');
                var new_height='470';
                bForSingles=false;
        }
        
        var active_link=$('.how_to_link_active');
        var inactive_link=$(this);
        
        inactive_link.removeClass('how_to_link_inactive').addClass('how_to_link_active');
        active_link.removeClass('how_to_link_active').addClass('how_to_link_inactive');
        if (bForSingles)
        	setTimeout(function(){slide_container.animate({'min-height':new_height},{duration: 500,queue:false});},500);
        else
        	slide_container.animate({'min-height':new_height},{duration: 500,queue:false});
        
        active_slide.fadeOut({duration:500,queue:false,complete:function(){
                        inactive_slide.fadeIn(500,function(){
                                active_slide.removeClass('active_how_to_slide').addClass('inactive_how_to_slide');
                                inactive_slide.removeClass('inactive_how_to_slide').addClass('active_how_to_slide');
                                if (!bForSingles)
                                        window.set_setup_height();
                });
        }}); // close off active_slide.fadeToggle
});//close off .how_to_link_inactive click handler

/*  ensure all setup step boxes are same length */
window.set_setup_height = function() {
          if ($('#how_to_slide_setup').hasClass('active_how_to_slide')) {
                  var third_height = parseInt($('#setup_step_3 .setup_step_text').height()) + 210;
                  var fourth_height = parseInt($('#setup_step_4 .setup_step_text').height()) + 210;
                  var max_height = third_height;
                  if (fourth_height > third_height)
                        max_height = fourth_height;

                  $('.setup_step').animate({'min-height':max_height},250);
          }
};

var timeoutPointer;
$(window).resize(function(){
        clearTimeout(timeoutPointer);
        timeoutPointer = setTimeout(window.set_setup_height,100);
});
}); // close of jQuery(document).ready
