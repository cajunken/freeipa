/*  Authors:
 *    Petr Vobornik <pvoborni@redhat.com>
 *
 * Copyright (C) 2012 Red Hat
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

define([], function() {

/**
 * Specification of menu
 * @singleton
 * @class navigation.menu_spec
 */
var nav = {};
    /**
     * Admin menu
     */
    nav.admin = {
    name: 'admin',
    items: [
        {
            name: 'identity',
            label: '@i18n:tabs.identity',
            children: [
                { entity: 'user' },
                { entity: 'group' },
                { entity: 'host' },
                { entity: 'hostgroup' },
                { entity: 'netgroup' },
                { entity: 'service' },
                {
                    name:'dns',
                    label: '@i18n:tabs.dns',
                    children: [
                        {
                            entity: 'dnszone',
                            children: [
                                { entity: 'dnsrecord', hidden:true }
                            ]
                        },
                        { entity: 'dnsconfig' }
                    ]
                },
                { entity: 'cert', label: '@i18n:tabs.cert' },
                { entity: 'realmdomains' }
            ]
        },
        {name: 'policy', label: '@i18n:tabs.policy', children: [
            {name: 'hbac', label: '@i18n:tabs.hbac', children: [
                {entity: 'hbacrule'},
                {entity: 'hbacsvc'},
                {entity: 'hbacsvcgroup'},
                {entity: 'hbactest'}
            ]},
            {name: 'sudo', label: '@i18n:tabs.sudo', children: [
                {entity: 'sudorule'},
                {entity: 'sudocmd'},
                {entity: 'sudocmdgroup'}
            ]},
            {
                name:'automount',
                label: '@i18n:tabs.automount',
                entity: 'automountlocation',
                children:[
                 {entity: 'automountlocation', hidden:true},
                 {entity: 'automountmap', hidden: true},
                 {entity: 'automountkey', hidden: true}]
            },
            {entity: 'pwpolicy'},
            {entity: 'krbtpolicy'},
            {entity: 'selinuxusermap'},
            {
                name: 'automember',
                label: '@i18n:tabs.automember',
                children: [
                    {
                        name: 'amgroup',
                        entity: 'automember',
                        facet: 'searchgroup',
                        label: '@i18n:objects.automember.usergrouprules',
                        children: [
                            {
                                entity: 'automember',
                                facet: 'usergrouprule',
                                hidden: true
                            }
                        ]
                    },
                    {
                        name: 'amhostgroup',
                        entity: 'automember',
                        facet: 'searchhostgroup',
                        label: '@i18n:objects.automember.hostgrouprules',
                        children: [
                            {
                                entity: 'automember',
                                facet: 'hostgrouprule',
                                hidden: true
                            }
                        ]
                    }
                ]
            }
        ]},
        {name: 'ipaserver', label: '@i18n:tabs.ipaserver', children: [
            {name: 'rolebased', label: '@i18n:tabs.role', children: [
                {entity: 'role'},
                {entity: 'privilege'},
                {entity: 'permission'}
            ]},
            {entity: 'selfservice'},
            {entity: 'delegation'},
            {entity: 'idrange'},
            {
                name: 'trusts',
                label: '@i18n:tabs.trust',
                children:[
                    {entity: 'trust'},
                    {entity: 'trustconfig'}
                ]
            },

            {entity: 'config'}
        ]}
    ]
};

/**
 * Self-service menu
 */
nav.self_service = {
    name: 'self-service',
    items: [
        {
            name: 'identity',
            label: '@i18n:tabs.identity',
            children: [{entity: 'user'}]
        }
    ]
};

return nav;
});