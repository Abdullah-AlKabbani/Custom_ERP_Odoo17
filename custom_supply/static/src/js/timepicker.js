/** Time Picker 12h for Odoo 17 **/
odoo.define('custom_supply.timepicker_12h', [
    'web.field_registry',
    'web.AbstractField',
], function (fieldRegistry, AbstractField) {
    "use strict";

    var TimePicker12h = AbstractField.extend({

        start: function () {
            var self = this;

            // create input element
            this.$input = this.$el.find('input');

            // apply timepicker
            setTimeout(function () {
                self.$input.timepicker({
                    timeFormat: 'hh:mm TT',
                    interval: 15,
                    dynamic: false,
                    dropdown: true,
                    scrollbar: true
                });

            }, 100);

            // on change -> update field
            this.$input.on('change', function () {
                self._setValue($(this).val());
            });
        },
    });

    fieldRegistry.add('timepicker_12h', TimePicker12h);
});
