/*global django document window */
/*eslint no-alert: 0*/


(function($) {

    "use strict";

    var $doc = $(document);


    var varsAutocompleteItems = function() {
        var ret = [];
        $.each(window.VARS_LOOKUP, function(i, v) {
            ret.push({label: v.key, official: v.type === "official"});
        });
        return ret;
    };

    // remove a key/value pair from the widget
    $doc.on("click", ".jsonwidget-kv-container .inline-deletelink",
        function() {
            var $parentContainer = $(this).closest(".jsonwidget-kv-container");
            $parentContainer.css("background-color", "#ffc");
            var promptText = $(this)
                .closest(".jsonwidget-outer-container")
                .find(".remove-confirm-prompt")
                .data("prompt-text");
            if (window.confirm(promptText)) {
                $parentContainer.fadeOut(500, function() { $parentContainer.remove(); });
            } else {
                $parentContainer.css("background-color", "");
            }
        }
    );


    // add a new key/value pair to the widget
    $doc.on("click", ".jsonwidget-outer-container .add-button",
        function() {
            var $addButton = $(this);
            var $container = $addButton.closest(".jsonwidget-outer-container");
            var $newRow = $container.find(".add-kv-template").clone();
            var lastPairID = $container
                .find(".add-kv-pair-container")
                .prev(".jsonwidget-kv-container")
                .find("input").first().data("pair-id");
            var newPairID = parseInt(lastPairID || "0", 10) + 1;
            var $keyInput;
            var $valInput;

            $newRow.removeClass("add-kv-template");
            $newRow.find("input").data("pair-id", newPairID.toString());

            $keyInput = $($newRow.find("input[type=text]")[0]);
            $valInput = $($newRow.find("input[type=text]")[1]);
            $keyInput.attr("name", $keyInput.data("name") + newPairID.toString() + "]");
            $valInput.attr("name", $valInput.data("name") + newPairID.toString() + "]");

            $keyInput.autocomplete({source: varsAutocompleteItems()});

            $container.find(".add-kv-pair-container").before($newRow);
            $keyInput.focus();

        }
    );


    $doc.ready(function(){
        $(".jsonwidget-key").autocomplete({source: varsAutocompleteItems()});
    });

})(django.jQuery);
