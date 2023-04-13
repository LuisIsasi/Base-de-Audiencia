/* globals django */


var AUDB = AUDB || {};

AUDB.send_products_selection = function(slug, name)
{
    var opener, send_data;
    opener = sessionStorage.getItem("audb::products-opener");
    if (opener === null)
    {
        return;
    }
    opener = JSON.parse(opener);

    send_data = {
        name: "audb::products-data",
        product: {
            name: name,
            slug: slug
        }
    };

    window.opener.postMessage(send_data, opener.origin);
};

(function($) {
    var add_listeners = function()
    {
        $("#result_list").on(
            "click.audb-products",
            ".for-external-popup-core-products-name",
            event_send_products
        );

        $(window).on("message.audb-products", receive_message);
    };

    var event_send_products = function(e)
    {
        e.preventDefault();
        e.stopPropagation();
        AUDB.send_products_selection($(this).data("slug"), $(this).data("name"));
    };

    var get_from_message_event = function(e, prop)
    {
        var val = e[prop] || e.originalEvent[prop];
        return val;
    };

    var is_valid_message = function(e)
    {
        // I want to test source === window.opener as well, but I can't seem to
        // get it working
        var origin = get_from_message_event(e, "origin");
        return AUDB.valid_message_origins.test(origin);
    };

    var notify_ready = function()
    {
        // Because a user might be redirected to a login page, we must notify
        // window.opener when it is ready to start making requests.
        var message;
        if (window.opener)
        {
            message = {
                name: "audb::products-ready"
            };
            window.opener.postMessage(message, "*");
        }
    };

    var ready = function()
    {
        add_listeners();
        notify_ready();
    };

    var receive_message = function(e)
    {
        var message, opener_data, origin;
        if (!is_valid_message(e))
        {
            return;
        }
        origin = get_from_message_event(e, "origin");
        message = get_from_message_event(e, "data");

        if (message.name === "athena::requesting-product")
        {
            opener_data = {
                origin: origin
            };
            sessionStorage.setItem("audb::products-opener", JSON.stringify(opener_data));
        }
    };

    $(document).ready(ready);

})(django.jQuery);
