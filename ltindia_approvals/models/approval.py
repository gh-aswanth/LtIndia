# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def name_get(self):
        if self._context.get('lt_product_code'):
            return [(product.id, '%s - %s' % (product.default_code, product.name)) for product in self]
        return [(product.id, product.default_code) for product in self]


class Department(models.Model):
    _name = 'department.department'
    _description = 'Department'

    name = fields.Char(string='Department Name', required=True)


class ApprovalDocument(models.Model):
    _name = 'approval.document'
    _description = 'Approval Document'
    _rec_name = 'doc_no'

    doc_no = fields.Char(string='Document No', required=True)
    rev_no = fields.Char(string='Revision No', required=True)
    date = fields.Date(string='Date', required=True)


class ApprovalDeviation(models.Model):
    _name = 'approval.deviation'
    _description = 'Approval Deviation'
    _rec_name = 'mrp_no'

    mrp_no = fields.Char(string='Mrp No / JO No', required=True)
    deviation_qty = fields.Char(string='Deviation Qty', required=True)
    approval_id = fields.Many2one('approval.approval', string='Approval')


class ApprovalLocation(models.Model):
    _name = 'approval.location'
    _description = 'Approval Location'

    name = fields.Char(string='Location Name', required=True)


class ApprovalCategory(models.Model):
    _name = 'approval.category'
    _description = 'Approval Category'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active', default=True)
    is_need_driver_notes = fields.Boolean(string='Driver Notes', default=False)
    approval_category_stage_ids = fields.One2many('approval.category.stage', 'approval_category_id',
                                                  string='Approval Category Stage')


class ApprovalCategoryType(models.Model):
    _name = 'approval.category.stage'
    _description = 'Approval Category Stage'
    _rec_name = 'department_id'
    _order = 'sequence desc'

    department_id = fields.Many2one('department.department', string='Department')
    active = fields.Boolean(string='Active', default=True)
    approval_category_id = fields.Many2one(
        'approval.category',
        string='Category'
    )
    sequence = fields.Integer(string='Sequence')
    user_ids = fields.Many2many('res.users', string='Users')
    sequence_dum = fields.Integer(string='Sequence Dummy', compute='_compute_sequence_dum')
    state = fields.Selection([
        ('verified', 'Verified'),
        ('qc_ok', 'QC OK'),
        ('stock_ok', 'Stock OK'),
        ('approved', 'Change Implemented')
    ], string='State')

    @api.depends('sequence')
    def _compute_sequence_dum(self):
        for rec in self:
            rec.sequence_dum = rec.sequence


class ApprovalApprovalLines(models.Model):
    _name = 'approval.approval.line'
    _description = 'Approval Line'
    _rec_name = 'department_id'
    _order = 'sequence desc'

    department_id = fields.Many2one('department.department', string='Department')
    user_ids = fields.Many2many('res.users', string='Users')
    approved = fields.Boolean(string='Approved', default=False)
    rejected = fields.Boolean(string='Rejected', default=False)
    approval_category_type_id = fields.Many2one(
        'approval.category.stage',
        string='Category'
    )
    approval_id = fields.Many2one('approval.approval', string='Approval')
    sequence = fields.Integer(related="approval_category_type_id.sequence", string='Sequence', store=True)
    date = fields.Date(string='Date')
    comment = fields.Text(string='Comment')

    def get_next_stage(self, seq):
        app_ctg = self.approval_id.approval_category_id.mapped('approval_category_stage_ids').filtered(
            lambda r: r.sequence == seq)
        return app_ctg

    def action_approve(self):
        for rec in self:
            if self.env.user in rec.user_ids and not rec.approved and not rec.rejected:
                demon = False
                seq = rec.sequence + 1
                app = rec.approval_id
                app_ctg = self.get_next_stage(seq)
                rec.write({
                    'approved': True,
                    'rejected': False,
                    'date': fields.Date.today(),
                })
                if app_ctg.department_id == app.department_id:
                    demon = app_ctg if app_ctg.state == 'approved' else False
                    app_ctg = self.get_next_stage(seq + 1)
                vals = {}
                if app_ctg and app_ctg.department_id != app.department_id:
                    vals['approval_category_type_id'] = app_ctg.id
                vals['state'] = rec.approval_category_type_id.state
                app.write(vals)
                if app.state != 'approved' and not demon:
                    app.load_next_level()

                if all(app.approval_line_ids.mapped('approved')):
                    app.write({
                        'state': 'approved',
                        'fourm_prepared_and_submitted': fields.Date.today()
                    })
                    mail_tm = self.env.ref('ltindia_approvals.email_template_change_implemented_info')
                    app.with_context(partner_to=','.join(app.message_follower_ids.mapped(lambda r: str(r.partner_id.id)))).message_post_with_template(mail_tm.id)


    def action_reject(self):
        for rec in self:
            if self.env.user in rec.user_ids:
                if rec.approval_id.state != 'approved':
                    rec.write({
                        'approved': False,
                        'rejected': True,
                        'date': fields.Date.today(),
                    })
                    if not rec.comment:
                        raise UserError('Please update the reject reason.')
                    rec.approval_id.write({'state': 'rejected'})
                    mail_tm = self.env.ref('ltindia_approvals.email_template_document_reject')
                    rec.approval_id.with_context(
                        partner_to=','.join(rec.approval_id.message_follower_ids.
                                            mapped(lambda r: str(r.partner_id.id)))).\
                        message_post_with_template(mail_tm.id)


class ApprovalRequestLine(models.Model):
    _name = "approval.request.line"
    _description = "Approval Request Line"

    product_id = fields.Many2one('product.product', string='Part Code', required=True)
    item_description = fields.Char(string='Part Description')
    request_product_id = fields.Many2one('product.product', string='Deviated Part Code', required=True)
    req_item_description = fields.Char(string='Deviated Part Description')
    reason = fields.Text(string='Reason')
    approval_id = fields.Many2one('approval.approval', string='Approval')

    @api.onchange('product_id')
    def onchange_finished_product_id(self):
        if self.product_id:
            self.item_description = self.product_id.name

    @api.onchange('request_product_id')
    def onchange_request_product_id(self):
        if self.request_product_id:
            self.req_item_description = self.request_product_id.name


class Approvals(models.Model):
    _name = 'approval.approval'
    _description = 'Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # def _default_category_id(self):
    #     return self.env['approval.category.stage'].search([], limit=1)

    @api.model
    def _read_group_category_ids(self, stages, domain, order):
        print('Domain:   ', domain)
        print('Order:    ', order)
        print('Stages:   ', stages)
        return self.env['approval.category.stage'].search(domain, order=order)

    name = fields.Char(string='Process Name', required=True)
    approval_category_id = fields.Many2one(
        'approval.category',
        required=True,
    )
    is_need_driver_notes = fields.Boolean(related="approval_category_id.is_need_driver_notes", string='Driver Notes',
                                          readonly=True)
    department_id = fields.Many2one('department.department', string='Department', tracking=True)
    approval_category_type_id = fields.Many2one(
        'approval.category.stage',
        string='Category',
        ondelete='restrict',
        domain="[('approval_category_id', '=', approval_category_id), ('department_id', '!=', department_id)]",
        group_expand='_read_group_category_ids'
    )
    end_date = fields.Char(string='End Date', required=False, tracking=True)
    approval_line_ids = fields.One2many('approval.approval.line', 'approval_id', string='Approval Line',
                                        tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'Running'),
        ('verified', 'Verified'),
        ('qc_ok', 'QC OK'),
        ('stock_ok', 'Stock OK'),
        ('approved', 'Change Implemented'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', tracking=True)
    roll_no = fields.Char(string='4M Roll No', tracking=True, readonly=True)
    location_id = fields.Many2one('approval.location', string='Location', tracking=True)
    starting_serial = fields.Char(string='Starting Serial', tracking=True)
    ending_serial = fields.Char(string='Ending Serial', tracking=True)
    deviation_qty = fields.Char(string='Deviation Qty', tracking=True)
    finished_product_ids = fields.Many2many('product.product', string='Product Code')
    request_line_ids = fields.One2many('approval.request.line', 'approval_id', string='Request Line',
                                       tracking=True)
    major_control_points = fields.Text(string='Major Control Points', tracking=True)
    verification_results = fields.Text(string='Verification Results', tracking=True)
    remarks = fields.Text(string='Remarks', tracking=True)
    request_user_id = fields.Many2one('res.users', string='Process Change Initiated By',
                                      default=lambda self: self.env.user, tracking=True)
    change_verified_by = fields.Many2many('res.users', string='Process Change Review and Validated By',
                                          tracking=True)
    document_id = fields.Many2one('approval.document', string='Doc No', tracking=True,
                                  default=lambda self: self.env['approval.document'].search([], order='id asc',
                                                                                            limit=1))
    date = fields.Date(string='Date', tracking=True)
    rev_no = fields.Char(string='Rev No', tracking=True)
    reference = fields.Char(string='Reference', tracking=True)
    fourm_prepared_and_submitted = fields.Date(string='4M Prepared and Submitted', tracking=True)
    deviation_line_ids = fields.One2many('approval.deviation', 'approval_id', string='Deviation')
    note = fields.Text(string='Note')

    @api.onchange('document_id')
    def onchange_document_id(self):
        if self.document_id:
            self.date = self.document_id.date
            self.rev_no = self.document_id.rev_no

    @api.model
    def create(self, values):
        seq_code = self.env['ir.sequence'].next_by_code('approve.approve')
        values['roll_no'] = seq_code
        re = super(Approvals, self).create(values)
        return re

    @api.model
    def compute_dashboard(self):
        result = dict()
        category = self.env['approval.category'].search([])
        for ctg in category:
            doc = self.env['approval.approval'].search([('approval_category_id', '=', ctg.id)])
            state = self.env['approval.approval'].read_group([
                ('state', 'not in', [False, 'done']),
                ('approval_category_id', '=', ctg.id)
            ], ['state', 'approval_category_id'], ['state', 'approval_category_id'])
            for st in state:
                if st['state'] == 'draft':
                    st['state'] = ['draft', 'Draft']
                elif st['state'] == 'in_progress':
                    st['state'] = ['in_progress', 'Running']
                elif st['state'] == 'verified':
                    st['state'] = ['verified', 'Verified']
                elif st['state'] == 'qc_ok':
                    st['state'] = ['qc_ok', 'QC OK']
                elif st['state'] == 'stock_ok':
                    st['state'] = ['stock_ok', 'Stock OK']
                elif st['state'] == 'approved':
                    st['state'] = ['approved', 'Change Implemented']
                elif st['state'] == 'rejected':
                    st['state'] = ['rejected', 'Rejected']
                elif st['state'] == 'closed':
                    st['state'] = ['closed', 'Closed']
                elif st['state'] == 'cancelled':
                    st['state'] = ['cancelled', 'Cancelled']

            result.setdefault('top_board', []).append({
                'ctg': [ctg.id, ctg.name],
                'count': len(doc),
                'stage': doc.mapped('approval_category_type_id').mapped(lambda r: [r.id, r.department_id.name]),
                'bottom_board': state
            })
        return result

    def action_impl_change_close_revert(self):
        self.ensure_one()
        self.write({'state': 'approved', 'end_date': False})

    def action_impl_change_close(self):
        self.ensure_one()
        mail_tm = self.env.ref('ltindia_approvals.email_template_document_close')
        self.write({'state': 'closed', 'end_date': fields.Date.today().strftime('%d/%m/%Y')})
        self.with_context(partner_to=','.join(self.message_follower_ids.mapped(lambda r: str(r.partner_id.id)))).message_post_with_template(mail_tm.id)

    def load_next_level(self):
        self.ensure_one()
        self.approval_line_ids = [(0, 0, {
            'department_id': self.approval_category_type_id.department_id.id,
            'user_ids': [(6, 0, self.approval_category_type_id.user_ids.ids)],
            'approval_category_type_id': self.approval_category_type_id.id
        })]
        partners = self.approval_category_type_id.user_ids.mapped('partner_id')
        self.message_subscribe(partners.ids)
        mail_tm = self.env.ref('ltindia_approvals.email_template_approval_doc_invite')
        self.with_context(partner_to=','.join(partners.mapped(lambda r: str(r.id)))).message_post_with_template(mail_tm.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return '4M - %s' % self.roll_no

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_draft(self):
        self.write({'state': 'draft', 'approval_category_type_id': False})
        self.mapped('approval_line_ids').unlink()

    def action_confirm(self):
        for rec in self:
            if not rec.finished_product_ids or not rec.deviation_line_ids or not rec.request_line_ids:
                raise UserError('No Request Data found on this document.')
            stages = rec.approval_category_id.mapped('approval_category_stage_ids').\
                filtered(lambda r: r.department_id.id != rec.department_id.id).\
                sorted(key=lambda r: r.sequence)
            if stages:
                stages = stages[0]
            rec.write({
                'state': 'in_progress',
                'approval_category_type_id': stages and stages.id or False,
            })
            rec.load_next_level()
