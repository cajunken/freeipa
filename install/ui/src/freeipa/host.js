/*  Authors:
 *    Pavel Zuna <pzuna@redhat.com>
 *    Endi S. Dewata <edewata@redhat.com>
 *
 * Copyright (C) 2010 Red Hat
 * see file 'COPYING' for use and warranty information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

define(['./ipa',
        './jquery',
        './phases',
        './reg',
        './text',
        './details',
        './search',
        './association',
        './entity',
        './certificate'],
    function(IPA, $, phases, reg, text) {

var exp = IPA.host = {};

var make_spec = function() {
return {
    name: 'host',
    policies: [
        IPA.search_facet_update_policy,
        IPA.details_facet_update_policy,
        {
            $factory: IPA.cert.cert_update_policy,
            source_facet: 'details',
            dest_entity: 'cert',
            dest_facet: 'details'
        },
        {
            $factory: IPA.cert.cert_update_policy,
            source_facet: 'details',
            dest_entity: 'cert',
            dest_facet: 'search'
        }
    ],
    facets: [
        {
            $type: 'search',
            columns: [
                'fqdn',
                'description',
                {
                    name: 'has_keytab',
                    label: '@i18n:objects.host.enrolled',
                    formatter: 'boolean'
                }
            ],
            actions: [
                'select',
                {
                    $type: 'automember_rebuild',
                    name: 'automember_rebuild',
                    label: '@i18n:actions.automember_rebuild'
                }
            ],
            header_actions: ['select_action', 'automember_rebuild']
        },
        {
            $type: 'details',
            $factory: IPA.host.details_facet,
            sections: [
                {
                    name: 'details',
                    fields: [
                        {
                            $type: 'host_dnsrecord_entity_link',
                            name: 'fqdn',
                            other_entity: 'dnsrecord'
                        },
                        'krbprincipalname',
                        {
                            $type: 'textarea',
                            name: 'description'
                        },
                        'userclass',
                        'l',
                        'nshostlocation',
                        'nshardwareplatform',
                        'nsosversion',
                        {
                            $type: 'sshkeys',
                            name: 'ipasshpubkey',
                            label: '@i18n:objects.sshkeystore.keys'
                        },
                        {
                            $type: 'multivalued',
                            name: 'macaddress',
                            flags: ['w_if_no_aci']
                        },
                        {
                            name: 'ipakrbokasdelegate',
                            $type: 'checkbox',
                            acl_param: 'krbticketflags',
                            flags: ['w_if_no_aci']
                        }
                    ]
                },
                {
                    name: 'enrollment',
                    action_panel: {
                        $factory: IPA.action_panel,
                        name: 'enrollment_actions',
                        actions: ['unprovision', 'set_otp', 'reset_otp']
                    },
                    fields: [
                        {
                            $factory: IPA.host_keytab_widget,
                            name: 'has_keytab',
                            label: '@i18n:objects.host.keytab'
                        },
                        {
                            $type: 'host_password',
                            name: 'has_password',
                            label: '@i18n:objects.host.password'
                        }
                    ]
                },
                {
                    name: 'certificate',
                    action_panel: {
                        $factory: IPA.action_panel,
                        name: 'cert_actions',
                        actions: [
                            'request_cert', 'view_cert', 'get_cert',
                            'revoke_cert', 'restore_cert'
                        ]
                    },
                    fields: [
                        {
                            $type: 'certificate_status',
                            name: 'certificate_status',
                            label: '@i18n:objects.host.status'
                        }
                    ]
                }
            ],
            actions: [
                'select',
                {
                    $type: 'automember_rebuild',
                    name: 'automember_rebuild',
                    label: '@i18n:actions.automember_rebuild'
                },
                'host_unprovision',
                {
                    $type: 'set_otp',
                    name: 'set_otp',
                    label: '@i18n:objects.host.password_set_title',
                    status: 'missing',
                    hide_cond: ['has_password']
                },
                {
                    $type: 'set_otp',
                    name: 'reset_otp',
                    label: '@i18n:objects.host.password_reset_title',
                    status: 'present',
                    show_cond: ['has_password']
                },
                'cert_view',
                'cert_get',
                'cert_request',
                'cert_revoke',
                'cert_restore'
            ],
            header_actions: ['select_action', 'automember_rebuild'],
            state: {
                evaluators: [
                    IPA.host.has_password_evaluator,
                    IPA.host.has_keytab_evaluator,
                    IPA.host.userpassword_acl_evaluator,
                    IPA.host.krbprincipalkey_acl_evaluator,
                    IPA.cert.certificate_evaluator
                ]
            },
            policies: [
                IPA.host.enrollment_policy,
                IPA.host.certificate_policy
            ]
        },
        {
            $type: 'association',
            name: 'managedby_host',
            add_method: 'add_managedby',
            remove_method: 'remove_managedby'
        },
        {
            $type: 'association',
            name: 'memberof_hostgroup',
            associator: IPA.serial_associator
        },
        {
            $type: 'association',
            name: 'memberof_netgroup',
            associator: IPA.serial_associator
        },
        {
            $type: 'association',
            name: 'memberof_role',
            associator: IPA.serial_associator
        },
        {
            $type: 'association',
            name: 'memberof_hbacrule',
            associator: IPA.serial_associator,
            add_method: 'add_host',
            remove_method: 'remove_host'
        },
        {
            $type: 'association',
            name: 'memberof_sudorule',
            associator: IPA.serial_associator,
            add_method: 'add_host',
            remove_method: 'remove_host'
        }
    ],
    standard_association_facets: true,
    adder_dialog: {
        $factory: IPA.host_adder_dialog,
        height: 300,
        sections: [
            {
                $factory: IPA.composite_widget,
                name: 'fqdn',
                fields: [
                    {
                        $type: 'host_fqdn',
                        name: 'fqdn',
                        required: true
                    }
                ]
            },
            {
                name: 'other',
                fields: [
                    'userclass',
                    {
                        name: 'ip_address',
                        validators: [ 'ip_address' ],
                        metadata: '@mc-opt:host_add:ip_address'
                    },
                    {
                        $type: 'force_host_add_checkbox',
                        name: 'force',
                        metadata: '@mc-opt:host_add:force'
                    }
                ]
            }
        ]
    },
    deleter_dialog: {
        $factory: IPA.host_deleter_dialog
    }
};};

IPA.host.details_facet = function(spec, no_init) {

    var that = IPA.details_facet(spec, true);
    that.certificate_loaded = IPA.observer();
    that.certificate_updated = IPA.observer();

    that.get_refresh_command_name = function() {
        return that.entity.name+'_show_'+that.get_pkey();
    };

    if (!no_init) that.init_details_facet();

    return that;
};

IPA.host_fqdn_widget = function(spec) {

    spec = spec || {};

    spec.widgets = [
        {
            $type: 'text',
            name: 'hostname',
            label: '@i18n:objects.service.host',
            required: true
        },
        {
            $type: 'dnszone_select',
            name: 'dnszone',
            label: '@mo:dnszone.label_singular',
            editable: true,
            empty_option: false,
            required: true,
            searchable: true
        }
    ];

    var that = IPA.composite_widget(spec);

    that.create = function(container) {
        that.container = container;

        var hostname = that.widgets.get_widget('hostname');
        var dnszone = that.widgets.get_widget('dnszone');

        var table = $('<table/>', {
            'class': 'fqdn'
        }).appendTo(that.container);

        var tr = $('<tr/>').appendTo(table);

        var th = $('<th/>', {
            'class': 'hostname',
            title: hostname.label,
            text: hostname.label
        }).appendTo(tr);

        $('<span/>', {
            'class': 'required-indicator',
            text: IPA.required_indicator
        }).appendTo(th);

        th = $('<th/>', {
            'class': 'dnszone',
            title: dnszone.label,
            text: dnszone.label
        }).appendTo(tr);

        $('<span/>', {
            'class': 'required-indicator',
            text: IPA.required_indicator
        }).appendTo(th);

        tr = $('<tr/>').appendTo(table);

        var td = $('<td/>', {
            'class': 'hostname'
        }).appendTo(tr);

        var widget_cont = $('<div/>', {
            name: hostname.name
        }).appendTo(td);
        hostname.create(widget_cont);

        td = $('<td/>', {
            'class': 'dnszone'
        }).appendTo(tr);

        widget_cont = $('<div/>', {
            name: dnszone.name
        }).appendTo(td);
        dnszone.create(widget_cont);

        var hostname_input = $('input', hostname.container);
        var dnszone_input = $('input', dnszone.container);

        hostname_input.keyup(function(e) {
            var value = hostname_input.val();
            var i = value.indexOf('.');
            if (i >= 0) {
                var hostname = value.substr(0, i);
                var dnszone = value.substr(i+1);
                hostname_input.val(hostname);
                if (dnszone) {
                    dnszone_input.val(dnszone);
                    dnszone_input.focus();
                }
                IPA.select_range(dnszone_input, 0, dnszone_input.val().length);
            }
        });
    };

    return that;
};

IPA.host_fqdn_field = function(spec) {

    spec = spec || {};

    var that = IPA.field(spec);

    that.validate_required = function() {

        var hostname = that.hostname_widget.save();
        var dnszone = that.dns_zone_widget.save();

        var valid = true;

        if(!hostname.length || hostname[0] === '') {
            that.hostname_widget.show_error(text.get('@i18n:widget.validation.required'));
            that.valid = valid = false;
        }

        if(!dnszone.length || dnszone[0] === '') {
            that.dns_zone_widget.show_error(text.get('@i18n:widget.validation.required'));
            that.valid = valid = false;
        }

        return valid;
    };

    that.hide_error = function() {
        that.hostname_widget.hide_error();
        that.dns_zone_widget.hide_error();
    };

    that.save = function(record) {

        if(!record) record = {};

        var hostname = that.hostname_widget.save()[0];
        var dnszone = that.dns_zone_widget.save()[0];

        record.fqdn = hostname && dnszone ? [ hostname+'.'+dnszone ] : [];

        return record.fqdn;
    };

    that.reset = function() {

        that.hostname_widget.update([]);
        that.dns_zone_widget.update([]);
    };

    that.widgets_created = function() {

        that.widget = that.container.widgets.get_widget(that.widget_name);
        that.hostname_widget = that.widget.widgets.get_widget('hostname');
        that.dns_zone_widget = that.widget.widgets.get_widget('dnszone');
    };

    return that;
};

IPA.host_adder_dialog = function(spec) {

    spec = spec || {};
    spec.retry = spec.retry !== undefined ? spec.retry : false;

    if (!IPA.dns_enabled) {

        //When server is installed without DNS support, a use of host_fqdn_widget
        //is bad because there are no DNS zones. IP address field is useless as
        //well. Special section and IP address field should be removed and normal
        //fqdn textbox has to be added.
        spec.sections.shift();
        spec.sections[0].fields.shift();
        spec.sections[0].fields.unshift('fqdn');
        delete spec.height;
    }

    var that = IPA.entity_adder_dialog(spec);

    that.create = function() {
        that.entity_adder_dialog_create();
        that.container.addClass('host-adder-dialog');
    };

    that.on_error = IPA.create_4304_error_handler(that);

    return that;
};

IPA.host_deleter_dialog = function(spec) {

    spec = spec || {};

    var that = IPA.search_deleter_dialog(spec);

    that.create = function() {

        that.deleter_dialog_create();

        var metadata = IPA.get_command_option('host_del', 'updatedns');

        that.updatedns = $('<input/>', {
            type: 'checkbox',
            name: 'updatedns',
            title: metadata.doc
        }).appendTo(that.container);

        that.container.append(' ');

        that.container.append(metadata.doc);
    };

    that.create_command = function() {
        var batch = that.search_deleter_dialog_create_command();
        var updatedns = that.updatedns.is(':checked');

        for (var i=0; i<batch.commands.length; i++) {
            var command = batch.commands[i];
            command.set_option('updatedns', updatedns);
        }

        return batch;
    };

    return that;
};

IPA.dnszone_select_widget = function(spec) {

    spec = spec || {};
    spec.other_entity = 'dnszone';
    spec.other_field = 'idnsname';

    var that = IPA.entity_select_widget(spec);

    that.create_search_command = function(filter) {
        return IPA.command({
            entity: that.other_entity.name,
            method: 'find',
            args: [filter],
            options: {
                forward_only: true
            }
        });
    };

    return that;
};

IPA.host_dnsrecord_entity_link_field = function(spec){
    var that = IPA.link_field(spec);

    that.other_pkeys = function(){
        var pkey = that.facet.get_pkey();
        var first_dot = pkey.search(/\./);
        var pkeys = [];
        pkeys[1] = pkey.substring(0,first_dot);
        pkeys[0] = pkey.substring(first_dot+1);
        return pkeys;
    };

    return that;
};

IPA.force_host_add_checkbox_widget = function(spec) {
    var metadata = IPA.get_command_option('host_add', spec.name);
    spec.label = metadata.label;
    spec.tooltip = metadata.doc;
    return IPA.checkbox_widget(spec);
};

IPA.host.enrollment_policy = function(spec) {

    var that =  IPA.facet_policy();

    that.init = function() {

        var keytab_field = that.container.fields.get_field('has_keytab');
        var password_field = that.container.fields.get_field('has_password');

        var super_set_password = password_field.set_password;
        password_field.set_password = function(password, on_success, on_error) {
            super_set_password.call(
                this,
                password,
                function(data, text_status, xhr) {
                    keytab_field.load(data.result.result);
                    if (on_success) on_success.call(this, data, text_status, xhr);
                },
                on_error);
        };
    };

    return that;
};

IPA.host_keytab_widget = function(spec) {

    spec = spec || {};

    var that = IPA.input_widget(spec);

    that.create = function(container) {

        that.widget_create(container);

        that.missing_span = $('<span/>', {
            name: 'missing',
            style: 'display: none;'
        }).appendTo(container);

        $('<img/>', {
            src: 'images/caution-icon.png',
            'class': 'status-icon'
        }).appendTo(that.missing_span);

        that.missing_span.append(' ');

        that.missing_span.append(text.get('@i18n:objects.host.keytab_missing'));

        that.present_span = $('<span/>', {
            name: 'present',
            style: 'display: none;'
        }).appendTo(container);

        $('<img/>', {
            src: 'images/check-icon.png',
            'class': 'status-icon'
        }).appendTo(that.present_span);

        that.present_span.append(' ');

        that.present_span.append(text.get('@i18n:objects.host.keytab_present'));
    };

    that.update = function(values) {
        set_status(values[0] ? 'present' : 'missing');
        that.updated.notify([], that);
    };

    that.clear = function() {
        that.present_span.css('display', 'none');
        that.missing_span.css('display', 'none');
    };

    function set_status(status) {
        that.present_span.css('display', status == 'present' ? 'inline' : 'none');
        that.missing_span.css('display', status == 'missing' ? 'inline' : 'none');
    }

    return that;
};

IPA.host_unprovision_dialog = function(spec) {

    spec.title = spec.title || '@i18n:objects.host.unprovision_title';

    spec = spec || {};

    var that = IPA.dialog(spec);
    that.facet = spec.facet;

    that.title = that.title.replace('${entity}', that.entity.metadata.label_singular);

    that.create = function() {
        that.container.append(text.get('@i18n:objects.host.unprovision_confirmation'));
    };

    that.create_buttons = function() {

        that.create_button({
            name: 'unprovision',
            label: '@i18n:objects.host.unprovision',
            click: function() {
                that.unprovision(
                    function(data, text_status, xhr) {
                        that.facet.refresh();
                        that.close();
                        IPA.notify_success('@i18n:objects.host.unprovisioned');
                    },
                    function(xhr, text_status, error_thrown) {
                        that.close();
                    }
                );
            }
        });

        that.create_button({
            name: 'cancel',
            label: '@i18n:buttons.cancel',
            click: function() {
                that.close();
            }
        });
    };

    that.unprovision = function(on_success, on_error) {

        var pkey = that.facet.get_pkeys();

        var command = IPA.command({
            name: that.entity.name+'_disable_'+pkey,
            entity: that.entity.name,
            method: 'disable',
            args: pkey,
            on_success: on_success,
            on_error: on_error
        });

        command.execute();
    };

    that.create_buttons();

    return that;
};

IPA.host.unprovision_action = function(spec) {

    spec = spec || {};
    spec.name = spec.name || 'unprovision';
    spec.label = spec.label || '@i18n:objects.host.unprovision';
    spec.enable_cond = spec.enable_cond || ['has_keytab', 'krbprincipalkey_w'];

    var that = IPA.action(spec);

    that.execute_action = function(facet) {

        var dialog = IPA.host_unprovision_dialog({
            entity: facet.entity,
            facet: facet
        });

        dialog.open();
    };

    return that;
};

IPA.host.krbprincipalkey_acl_evaluator = function(spec) {

    spec.name = spec.name || 'unprovision_acl_evaluator';
    spec.attribute = spec.attribute || 'krbprincipalkey';

    var that = IPA.acl_state_evaluator(spec);
    return that;
};

IPA.host.has_keytab_evaluator = function(spec) {

    spec.name = spec.name || 'has_keytab_evaluator';
    spec.attribute = spec.attribute || 'has_keytab';
    spec.value = spec.value || [true];
    spec.representation = spec.representation || 'has_keytab';

    var that = IPA.value_state_evaluator(spec);
    return that;
};

IPA.host_password_widget = function(spec) {

    spec = spec || {};

    var that = IPA.input_widget(spec);

    that.create = function(container) {

        that.widget_create(container);

        that.missing_span = $('<span/>', {
            name: 'missing'
        }).appendTo(container);

        $('<img/>', {
            src: 'images/caution-icon.png',
            'class': 'status-icon'
        }).appendTo(that.missing_span);

        that.missing_span.append(' ');

        that.missing_span.append(text.get('@i18n:objects.host.password_missing'));

        that.present_span = $('<span/>', {
            name: 'present',
            style: 'display: none;'
        }).appendTo(container);

        $('<img/>', {
            src: 'images/check-icon.png',
            'class': 'status-icon'
        }).appendTo(that.present_span);

        that.present_span.append(' ');

        that.present_span.append(text.get('@i18n:objects.host.password_present'));
    };

    that.update = function(values) {
        set_status(values[0] ? 'present' : 'missing');
        that.updated.notify([], that);
    };

    that.clear = function() {
        that.missing_span.css('display', 'none');
        that.present_span.css('display', 'none');
    };

    function set_status(status) {

        that.status = status;

        if (status == 'missing') {
            that.missing_span.css('display', 'inline');
            that.present_span.css('display', 'none');
        } else {
            that.missing_span.css('display', 'none');
            that.present_span.css('display', 'inline');
        }
    }

    return that;
};

IPA.host.set_otp_dialog = function(spec) {

    spec = spec || {};
    spec.width = spec.width || 400;
    spec.sections = spec.sections || [
        {
            fields: [
                {
                    name: 'password1',
                    label: '@i18n:password.new_password',
                    $type: 'password',
                    required: true
                },
                {
                    name: 'password2',
                    label: '@i18n:password.verify_password',
                    $type: 'password',
                    required: true,
                    validators: [{
                        $type: 'same_password',
                        other_field: 'password1'
                    }]
                }
            ]
        }
    ];

    var that = IPA.dialog(spec);

    IPA.confirm_mixin().apply(that);

    that.facet = spec.facet;

    that.set_status = function(status) {

        var button = that.get_button('set_password');

        if (status == 'missing') {
            that.title = text.get('@i18n:objects.host.password_set_title');
            button.label = text.get('@i18n:objects.host.password_set_button');
        } else {
            that.title = text.get('@i18n:objects.host.password_reset_title');
            button.label = text.get('@i18n:objects.host.password_reset_button');
        }
    };

    that.on_confirm = function() {

        if (!that.validate()) return;

        var new_password = that.fields.get_field('password1').save()[0];
        that.set_otp(new_password);

        that.close();
    };

    that.create_buttons = function() {

        that.create_button({
            name: 'set_password',
            label: '@i18n:objects.host.password_set_button',
            click: function() {
                that.on_confirm();
            }
        });

        that.create_button({
            name: 'cancel',
            label: '@i18n:buttons.cancel',
            click: function() {
                that.close();
            }
        });
    };

    that.set_otp = function(password) {
        var pkey = that.facet.get_pkeys();

        var command = IPA.command({
            entity: that.entity.name,
            method: 'mod',
            args: pkey,
            options: {
                all: true,
                rights: true,
                userpassword: password
            },
            on_success: function(data) {
                that.facet.load(data);
                that.close();
                IPA.notify_success('@i18n:objects.host.password_set_success');
            },
            on_error: function() {
                that.close();
            }
        });

        command.execute();
    };

    that.create_buttons();

    return that;
};

IPA.host.set_otp_action = function(spec) {

    spec = spec || {};
    spec.name = spec.name || 'set_otp';
    spec.label = spec.label || '@i18n:objects.host.password_set_title';
    spec.enable_cond = spec.enable_cond || ['userpassword_w'];

    var that = IPA.action(spec);
    that.status = spec.status || 'missing';

    that.execute_action = function(facet) {

        var dialog = IPA.host.set_otp_dialog({
            entity: facet.entity,
            facet: facet
        });

        dialog.set_status(that.status);

        dialog.open();
    };

    return that;
};

IPA.host.userpassword_acl_evaluator = function(spec) {

    spec.name = spec.name || 'userpassword_acl_evaluator';
    spec.attribute = spec.attribute || 'userpassword';

    var that = IPA.acl_state_evaluator(spec);
    return that;
};

IPA.host.has_password_evaluator = function(spec) {

    spec.name = spec.name || 'has_password_evaluator';
    spec.attribute = spec.attribute || 'has_password';
    spec.value = spec.value || [true];
    spec.representation = spec.representation || 'has_password';

    var that = IPA.value_state_evaluator(spec);
    return that;
};

IPA.host.certificate_policy = function(spec) {

    spec = spec || {};

    spec.get_pkey = spec.get_pkey || function(result) {
        var values = result.fqdn;
        return values ? values[0] : null;
    };

    spec.get_name = spec.get_name || function(result) {
        var values = result.fqdn;
        return values ? values[0] : null;
    };

    spec.get_principal = spec.get_principal || function(result) {
        var values = result.krbprincipalname;
        return values ? values[0] : null;
    };

    spec.get_hostname = spec.get_hostname || spec.get_name;

    var that = IPA.cert.load_policy(spec);
    return that;
};


exp.entity_spec = make_spec();
exp.register = function() {
    var e = reg.entity;
    var w = reg.widget;
    var f = reg.field;
    var a = reg.action;

    e.register({type: 'host', spec: exp.entity_spec});
    f.register('host_fqdn', IPA.host_fqdn_field);
    w.register('host_fqdn', IPA.host_fqdn_widget);
    f.register('dnszone_select', IPA.field);
    w.register('dnszone_select', IPA.dnszone_select_widget);
    f.register('host_dnsrecord_entity_link', IPA.host_dnsrecord_entity_link_field);
    w.register('host_dnsrecord_entity_link', IPA.link_widget);
    f.register('force_host_add_checkbox', IPA.checkbox_field);
    w.register('force_host_add_checkbox', IPA.force_host_add_checkbox_widget);
    f.register('host_password', IPA.field);
    w.register('host_password', IPA.host_password_widget);

    a.register('host_unprovision', exp.unprovision_action);
    a.register('set_otp', exp.set_otp_action);
};
phases.on('registration', exp.register);

return exp;
});
