odoo.define('approval.dashboard', function (require) {
"use strict";

var ListRenderer = require('web.ListRenderer');
var ListView = require('web.ListView');
var core = require('web.core');
var QWeb = core.qweb;
var view_registry = require('web.view_registry');
var ApprovalListDashboardRenderer = ListRenderer.extend({

     events: _.extend({}, ListRenderer.prototype.events, {
            'click .o_dashboard_action': '_onDashboardOpenAction',
            'click .o_all':'_onDashboardFullOpenAction',
            'click .filter_btn':'_onFilterOpenAction',
            'click .app_state':'_onAppStateOpenAction'
    }),
    _onAppStateOpenAction: function(e){
        var self = this;
        e.preventDefault();
        var $action = $(e.currentTarget);
        e.stopPropagation();
        e.preventDefault();
        var doc_id = $action.children('a').attr('ctg-id');
        var state = $action.children('a').attr('ap-state');
        var cr_domain = doc_id ? [['approval_category_id', '=', parseInt(doc_id)], ['state', '=', state]] : [[]];
        this.do_action({
            name: $action.children('a').attr('title'),
            type: 'ir.actions.act_window',
            res_model: 'approval.approval',
            view_mode: 'tree,form',
            views: [[false,'list'],[false,'form']],
            domain: cr_domain,
            target: 'main',
        }, {clear_breadcrumbs: true});
    },
    _onDashboardFullOpenAction: function(){
        this.do_action({
                name: 'All Documents',
                type: 'ir.actions.act_window',
                res_model: 'approval.approval',
                view_mode: 'tree,form',
                views: [[false,'list'],[false,'form']],
                domain: [],
                target: 'main',
            }, {clear_breadcrumbs: true});
    },
    _onFilterOpenAction:function(e){
        var self = this;
        e.preventDefault();
        var $action = $(e.currentTarget);
        e.stopPropagation();
        e.preventDefault();
        var doc_id = $action.children('a').attr('id');
        var ctg_doc_id = $action.children('a').attr('ctg-id');
        var cr_domain = doc_id ? [['approval_category_type_id', '=', parseInt(doc_id)], ['approval_category_id', '=', parseInt(ctg_doc_id)]] : [[]];
        this.do_action({
            name: $action.children('a').attr('title'),
            type: 'ir.actions.act_window',
            res_model: 'approval.approval',
            view_mode: 'tree,form',
            views: [[false,'list'],[false,'form']],
            domain: cr_domain,
            target: 'main',
        }, {
        clear_breadcrumbs: true,
        });
    },
    _onDashboardOpenAction: function (e) {
        var self = this;e.preventDefault();
        var $action = $(e.currentTarget);
        e.stopPropagation();
        e.preventDefault();
        var doc_id = $action.attr('id');
        var cr_domain = doc_id ? [['approval_category_id', '=', parseInt(doc_id)]] : [[]];
        this.do_action({
            name: $action.attr('title'),
            type: 'ir.actions.act_window',
            res_model: 'approval.approval',
            view_mode: 'tree,form',
            views: [[false,'list'],[false,'form']],
            domain: cr_domain,
            target: 'main',
        }, {clear_breadcrumbs: true});
    },

    _renderView: function () {
        var self = this;
        return this._super.apply(this, arguments).then(() => {
            self._rpc({
                model: 'approval.approval',
                method: 'compute_dashboard',
                args: [],
            }).then((result) => {
                if (result.top_board){
                    var purchase_dashboard1 = QWeb.render('ltindia_approvals.ApprovalDashboard1', {lines: result});
                    self.$el.prepend(purchase_dashboard1);
                }


            });

        });
    },

});
var ApprovalListDashboardView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Renderer: ApprovalListDashboardRenderer,
    }),
});

view_registry.add('approval_list_dashboard', ApprovalListDashboardView);
});