import base64
from lxml import etree
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SunarthaCoretaxExport(models.Model):
    _name = 'sunartha.coretax.export'
    _description = 'Ekspor Faktur CoreTax DJP'
    _order = 'date_export desc, id desc'
    _rec_name = 'name'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Nama Ekspor', required=True,
        default=lambda self: _('New'), copy=False)
    date_from = fields.Date(string='Dari Tanggal', required=True)
    date_to = fields.Date(string='Sampai Tanggal', required=True)
    export_type = fields.Selection([
        ('outgoing', 'Faktur Pajak Keluaran'),
        ('incoming', 'Faktur Pajak Masukan'),
    ], string='Tipe Faktur', required=True, default='outgoing')
    company_id = fields.Many2one(
        'res.company', string='Perusahaan',
        default=lambda self: self.env.company, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('exported', 'Diekspor'),
    ], string='Status', default='draft', tracking=True)
    date_export = fields.Datetime(
        string='Tanggal Ekspor', readonly=True)
    exported_by = fields.Many2one(
        'res.users', string='Diekspor Oleh', readonly=True)
    move_ids = fields.Many2many(
        'account.move', string='Faktur',
        domain="[('move_type', 'in', ['out_invoice','out_refund','in_invoice','in_refund']),"
               "('state','=','posted'), ('company_id','=',company_id)]")
    xml_filename = fields.Char(string='Nama File XML', readonly=True)
    xml_data = fields.Binary(
        string='File XML', readonly=True, attachment=True)
    line_count = fields.Integer(
        string='Jumlah Faktur', compute='_compute_line_count')
    notes = fields.Text(string='Catatan')

    @api.depends('move_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.move_ids)

    def action_load_invoices(self):
        self.ensure_one()
        move_type = (['out_invoice', 'out_refund']
                     if self.export_type == 'outgoing'
                     else ['in_invoice', 'in_refund'])
        moves = self.env['account.move'].search([
            ('move_type', 'in', move_type),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id),
        ])
        self.move_ids = [(6, 0, moves.ids)]
        return True

    def action_export_xml(self):
        self.ensure_one()
        if not self.move_ids:
            raise UserError(_('Tidak ada faktur yang dipilih untuk diekspor.'))

        root = etree.Element('BundleEFaktur')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')

        npwp_penjual = (self.company_id.vat or '').replace('.', '').replace('-', '')
        header = etree.SubElement(root, 'TaxpayerTIN')
        header.text = npwp_penjual

        faktur_list = etree.SubElement(root, 'EFakturList')

        for move in self.move_ids:
            faktur = etree.SubElement(faktur_list, 'CFaktur')

            # Header Faktur
            hf = etree.SubElement(faktur, 'KodeFaktur')
            hf.text = getattr(move, 'l10n_id_efaktur_document_number', '') or ''

            tgl = etree.SubElement(faktur, 'TanggalFaktur')
            tgl.text = move.invoice_date.strftime('%d/%m/%Y') if move.invoice_date else ''

            npwp_lawan = etree.SubElement(faktur, 'NPWPLawanTransaksi')
            npwp_lawan.text = (move.partner_id.vat or '').replace('.', '').replace('-', '')

            nama_lawan = etree.SubElement(faktur, 'NamaLawanTransaksi')
            nama_lawan.text = move.partner_id.name or ''

            dpp = etree.SubElement(faktur, 'JumlahDPP')
            dpp.text = str(int(move.amount_untaxed))

            ppn = etree.SubElement(faktur, 'JumlahPPN')
            ppn.text = str(int(move.amount_tax))

        xml_bytes = etree.tostring(root, pretty_print=True,
                                   xml_declaration=True, encoding='UTF-8')
        filename = 'CoreTax_%s_%s_%s.xml' % (
            self.export_type,
            self.date_from.strftime('%Y%m'),
            self.company_id.vat or 'unknown',
        )
        self.write({
            'state': 'exported',
            'date_export': fields.Datetime.now(),
            'exported_by': self.env.user.id,
            'xml_filename': filename,
            'xml_data': base64.b64encode(xml_bytes),
        })
        self.message_post(
            body=_('File XML berhasil dibuat: %s (%d faktur)') % (filename, len(self.move_ids)))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/xml_data/%s?download=true' % (
                self._name, self.id, filename),
            'target': 'self',
        }
