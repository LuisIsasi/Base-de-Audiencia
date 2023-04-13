(function($) {
    $(document).ready(function(){
        var clipboard;
        $('.core-list-zephyr-copy-btn').on("click", function(e) {
            e.preventDefault();
        });
        $('.core-list-zephyr-copy-btn').on("mouseleave", function(e) {
            $(this).removeClass('core-list-zephyr-copy-btn-success');
        });
        clipboard = new Clipboard('.core-list-zephyr-copy-btn');
        clipboard.on('success', function() {
            $('.core-list-zephyr-copy-btn').addClass('core-list-zephyr-copy-btn-success');
        });
    });
})(django.jQuery);
