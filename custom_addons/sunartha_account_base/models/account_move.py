from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_approval_state = fields.Selection([
        ('not_required', 'Tidak Perlu Approval'),
        ('waiting', 'Menunggu Persetujuan'),
        ('approved', 'Disetujui'),
        ('rejected', 'Ditolak'),
    ], string='Status Approval', default='not_required', copy=False,
       tracking=True, index=True)

    x_approver_id = fields.Many2one(
        'res.users', string='Disetujui Oleh', copy=False, readonly=True)
    x_approval_date = fields.Datetime(
        string='Tanggal Persetujuan', copy=False, readonly=True)
    x_approval_notes = fields.Text(
        string='Catatan Approval', copy=False)
    x_approval_request_ids = fields.One2many(
        'sunartha.account.approval.request', 'move_id',
        string='Riwayat Approval')
    x_requires_approval = fields.Boolean(
        string='Perlu Approval', compute='_compute_requires_approval', store=False)

    @api.depends('amount_total', 'journal_id', 'journal_id.x_approval_threshold', 'currency_id')
    def _compute_requires_approval(self):
        for move in self:
            threshold = move.journal_id.x_approval_threshold or 0.0
            move.x_requires_approval = threshold > 0 and move.amount_total >= threshold

    def action_submit_approval(self):
        for move in self:
            if move.state != 'draft':
                raise UserError(_('Hanya jurnal Draft yang bisa diajukan untuk approval.'))
            if not move.x_requires_approval:
                raise UserError(_('Jurnal ini tidak memerlukan approval (di bawah threshold).'))

            approver_group = move.journal_id.x_approver_group_id
            if not approver_group:
                raise UserError(_(
                    'Tidak ada group approver yang dikonfigurasi untuk jurnal "%s".\n'
                    'Hubungi administrator untuk mengatur threshold dan approver.'
                ) % move.journal_id.name)

            approvers = self.env['res.users'].search([
                ('groups_id', 'in', approver_group.ids),
                ('active', '=', True),
            ])
            if not approvers:
                raise UserError(_(
                    'Tidak ada pengguna aktif dalam group approver "%s".'
                ) % approver_group.name)

            move.x_approval_state = 'waiting'
            self.env['sunartha.account.approval.request'].create({
                'move_id': move.id,
                'requester_id': self.env.user.id,
                'state': 'pending',
            })
            move.message_post(
                body=_('Jurnal diajukan untuk persetujuan oleh <b>%s</b>.<br/>'
                       'Total: <b>Rp %s</b> | Threshold: <b>Rp %s</b>') % (
                    self.env.user.name,
                    '{:,.0f}'.format(move.amount_total),
                    '{:,.0f}'.format(move.journal_id.x_approval_threshold),
                ),
                partner_ids=approvers.mapped('partner_id').ids,
                subtype_xmlid='mail.mt_comment',
            )
        return True

    def action_approve(self):
        self._check_approver_rights()
        for move in self:
            if move.x_approval_state != 'waiting':
                raise UserError(_('Hanya jurnal "Menunggu Persetujuan" yang bisa diapprove.'))
            move.write({
                'x_approval_state': 'approved',
                'x_approver_id': self.env.user.id,
                'x_approval_date': fields.Datetime.now(),
            })
            move.x_approval_request_ids.filtered(
                lambda r: r.state == 'pending'
            ).write({
                'state': 'approved',
                'approver_id': self.env.user.id,
                'date_responded': fields.Datetime.now(),
            })
            move.message_post(
                body=_('Jurnal <b>disetujui</b> oleh <b>%s</b>.') % self.env.user.name,
                subtype_xmlid='mail.mt_comment',
            )
        return True

    def action_reject(self):
        self._check_approver_rights()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tolak Jurnal'),
            'res_model': 'sunartha.account.approval.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_ids': [(6, 0, self.ids)],
            },
        }

    def action_post(self):
        for move in self:
            threshold = move.journal_id.x_approval_threshold or 0.0
            if threshold > 0 and move.amount_total >= threshold:
                if move.x_approval_state not in ('approved',):
                    raise UserError(_(
                        'Jurnal "%s" memerlukan persetujuan terlebih dahulu.\n'
                        'Total Rp %s melebihi threshold Rp %s.\n'
                        'Klik "Ajukan Persetujuan" untuk memulai proses approval.'
                    ) % (
                        move.name or move.ref or '(Draft)',
                        '{:,.0f}'.format(move.amount_total),
                        '{:,.0f}'.format(threshold),
                    ))
        return super().action_post()

    def _check_approver_rights(self):
        approver_group = self.env.ref(
            'sunartha_account_base.group_account_approver', raise_if_not_found=False)
        manager_group = self.env.ref(
            'sunartha_account_base.group_account_manager', raise_if_not_found=False)
        user_groups = self.env.user.groups_id
        if not ((approver_group and approver_group in user_groups) or
                (manager_group and manager_group in user_groups)):
            raise UserError(_('Anda tidak memiliki hak akses untuk menyetujui atau menolak jurnal.'))
