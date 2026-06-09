from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SunarthaJournalTransaction(models.Model):
    _name = 'sunartha.journal.transaction'
    _description = 'Journal Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'transaction_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Referensi', default='New', readonly=True, copy=False, index=True)
    module = fields.Selection([
        ('ar', 'AR - Invoice'),
        ('ap', 'AP - Bills'),
        ('gl', 'GL - Journal Entry'),
        ('in', 'IN - Inventory'),
    ], string='Module', required=True, default='gl', tracking=True)
    batch_number = fields.Char(string='Batch Number', readonly=True, copy=False, index=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Diajukan'),
        ('approved', 'Disetujui'),
        ('rejected', 'Ditolak'),
        ('posted', 'Posted'),
        ('cancelled', 'Dibatalkan'),
    ], string='Status', default='draft', tracking=True, copy=False)
    transaction_date = fields.Date(
        string='Transaction Date', required=True, default=fields.Date.today, tracking=True)
    post_period = fields.Char(
        string='Post Period', compute='_compute_post_period', store=True)
    auto_reversing = fields.Boolean(string='Auto Reversing', default=False)
    branch_id = fields.Many2one('sunartha.branch', string='Branch', tracking=True)
    ledger_id = fields.Many2one('sunartha.ledger', string='Ledger', tracking=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id, required=True)
    currency_rate = fields.Float(string='Rate', digits=(16, 4), default=1.0)
    description = fields.Text(string='Description')
    type = fields.Selection([
        ('normal', 'Normal'),
        ('reversing', 'Reversing'),
    ], string='Type', default='normal', tracking=True)
    line_ids = fields.One2many(
        'sunartha.journal.transaction.line', 'transaction_id', string='Lines')
    debit_total = fields.Monetary(
        string='Debit Total', compute='_compute_totals', store=True)
    credit_total = fields.Monetary(
        string='Credit Total', compute='_compute_totals', store=True)
    is_balanced = fields.Boolean(
        string='Balanced', compute='_compute_totals', store=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one(
        'res.users', string='Created By',
        default=lambda self: self.env.user, readonly=True)
    approver_id = fields.Many2one(
        'res.users', string='Approved By', readonly=True, copy=False, tracking=True)
    approval_date = fields.Datetime(
        string='Approval Date', readonly=True, copy=False)
    rejection_reason = fields.Text(
        string='Rejection Reason', readonly=True, copy=False)
    reversal_id = fields.Many2one(
        'sunartha.journal.transaction', string='Reversal Entry', readonly=True, copy=False)
    reversed_entry_id = fields.Many2one(
        'sunartha.journal.transaction', string='Original Entry', readonly=True, copy=False)

    @api.depends('transaction_date')
    def _compute_post_period(self):
        for rec in self:
            rec.post_period = rec.transaction_date.strftime('%m-%Y') if rec.transaction_date else False

    @api.depends('line_ids.debit_amount', 'line_ids.credit_amount')
    def _compute_totals(self):
        for rec in self:
            debit = sum(rec.line_ids.mapped('debit_amount'))
            credit = sum(rec.line_ids.mapped('credit_amount'))
            rec.debit_total = debit
            rec.credit_total = credit
            rec.is_balanced = abs(debit - credit) < 0.01

    @api.depends('name', 'description')
    def _compute_display_name(self):
        for rec in self:
            parts = [rec.name or 'New']
            if rec.description:
                first_line = rec.description.split('\n')[0]
                short = first_line[:60] + ('...' if len(first_line) > 60 else '')
                parts.append(short)
            rec.display_name = ' - '.join(filter(None, parts))

    @api.onchange('module')
    def _onchange_module(self):
        if self.batch_number:
            self.name = f"{self.module.upper()} {self.batch_number}"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                seq = self.env['ir.sequence'].next_by_code(
                    'sunartha.journal.transaction') or '000001'
                module = vals.get('module', 'gl').upper()
                vals['batch_number'] = seq
                vals['name'] = f"{module} {seq}"
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Hanya transaksi Draft yang bisa diajukan.'))
            if not rec.line_ids:
                raise UserError(_('Tambahkan minimal satu baris detail sebelum mengajukan.'))
            rec.state = 'submitted'
            rec.message_post(
                body=_('Transaksi diajukan untuk persetujuan oleh <b>%s</b>.') % self.env.user.name,
                subtype_xmlid='mail.mt_comment',
            )

    def action_approve(self):
        self._check_manager()
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_('Hanya transaksi Diajukan yang bisa disetujui.'))
            rec.write({
                'state': 'approved',
                'approver_id': self.env.user.id,
                'approval_date': fields.Datetime.now(),
                'rejection_reason': False,
            })
            rec.message_post(
                body=_('Transaksi <b>disetujui</b> oleh <b>%s</b>.') % self.env.user.name,
                subtype_xmlid='mail.mt_comment',
            )

    def action_reject(self):
        self._check_manager()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tolak Transaksi'),
            'res_model': 'sunartha.journal.transaction.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_transaction_ids': [(6, 0, self.ids)]},
        }

    def action_post(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('Hanya transaksi Disetujui yang bisa diposting.'))
            if not rec.is_balanced:
                raise UserError(_(
                    'Debit Total (%(debit)s) tidak sama dengan Credit Total (%(credit)s).\n'
                    'Seimbangkan transaksi sebelum posting.'
                ) % {
                    'debit': '{:,.2f}'.format(rec.debit_total),
                    'credit': '{:,.2f}'.format(rec.credit_total),
                })
            rec.state = 'posted'
            rec.message_post(
                body=_('Transaksi <b>diposting</b> oleh <b>%s</b>.') % self.env.user.name,
                subtype_xmlid='mail.mt_comment',
            )
            if rec.auto_reversing:
                reversal = rec._create_reversal()
                rec.message_post(
                    body=_('Jurnal pembalik otomatis dibuat: <a href="#">%s</a>') % reversal.name,
                )

    def action_reset_draft(self):
        for rec in self:
            if rec.state == 'posted':
                raise UserError(_('Transaksi yang sudah Posted tidak bisa di-reset.'))
            rec.write({
                'state': 'draft',
                'approver_id': False,
                'approval_date': False,
                'rejection_reason': False,
            })
            rec.message_post(body=_('Transaksi di-reset ke Draft oleh <b>%s</b>.') % self.env.user.name)

    def action_cancel(self):
        self._check_manager()
        for rec in self:
            if rec.state == 'posted':
                raise UserError(_('Transaksi Posted tidak bisa dibatalkan. Buat reversal entry.'))
            rec.state = 'cancelled'
            rec.message_post(body=_('Transaksi <b>dibatalkan</b> oleh <b>%s</b>.') % self.env.user.name)

    def _create_reversal(self):
        self.ensure_one()
        reversal_date = self.transaction_date.replace(day=1) + relativedelta(months=1)
        lines = [(0, 0, {
            'account_id': l.account_id.id,
            'description': l.description,
            'subaccount': l.subaccount,
            'transaction_date': reversal_date,
            'debit_amount': l.credit_amount,
            'credit_amount': l.debit_amount,
            'transaction_description': l.transaction_description,
            'branch_id': l.branch_id.id if l.branch_id else False,
        }) for l in self.line_ids]

        reversal = self.env['sunartha.journal.transaction'].create({
            'module': self.module,
            'branch_id': self.branch_id.id if self.branch_id else False,
            'ledger_id': self.ledger_id.id if self.ledger_id else False,
            'currency_id': self.currency_id.id,
            'currency_rate': self.currency_rate,
            'description': f"Reversal: {self.name}",
            'type': 'reversing',
            'transaction_date': reversal_date,
            'auto_reversing': False,
            'company_id': self.company_id.id,
            'line_ids': lines,
            'reversed_entry_id': self.id,
        })
        self.reversal_id = reversal.id
        return reversal

    def action_view_reversal(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reversal Entry'),
            'res_model': 'sunartha.journal.transaction',
            'view_mode': 'form',
            'res_id': self.reversal_id.id,
        }

    def _check_manager(self):
        manager_group = self.env.ref(
            'sunartha_accounting_advance.group_accounting_advance_manager',
            raise_if_not_found=False)
        if manager_group and manager_group not in self.env.user.groups_id:
            raise UserError(_('Hanya Manager yang bisa melakukan aksi ini.'))
