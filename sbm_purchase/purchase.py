import time
from datetime import date, timedelta, datetime
import netsvc
from osv import osv, fields

class Pembelian_Barang(osv.osv):
	_name = 'pembelian.barang'
	_columns = {
		'name':fields.char('No.PB',required=True),
		'spk_no':fields.char('SPK No / PO No'),
		'tanggal':fields.date('Date', required=True),
		'duedate':fields.date('Due Date',required=True),
		'employee_id': fields.many2one('hr.employee', "Employee", required=True),
        'department_id':fields.many2one('hr.department','Department'),
        'customer_id':fields.many2one('res.partner','Customer', domain=[('customer','=',True)]),
        'detail_pb_ids': fields.one2many('detail.pb', 'detail_pb_id', 'Detail PB',readonly=True, states={'draft':[('readonly',False)],'edit':[('readonly',False)]}),
        'ref_pb':fields.char('Ref No',required=True, select=True),
        'notes': fields.text('Terms and Conditions'),
    	'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Check'),
            ('confirm2', 'Confirm'),
            ('purchase','Purchase'),
            ('done', 'Done'),
            ('edit','Edit PB'),
            ],
            'Status'),
    }
	_defaults = {
		'name': '/',
		'tanggal':time.strftime('%Y-%m-%d'),
		'state': 'draft'
	}

	def setDeuDate(self, cr, uid, ids, tanggal):
		setDueDateValue = datetime.strptime(tanggal, "%Y-%m-%d") + timedelta(days=4)
		return {'value':{'duedate':setDueDateValue.strftime('%Y-%m-%d')}}

	def setTanggal(self, cr, uid, ids, tanggal, duedate):
		setDueDateValue = datetime.strptime(tanggal, "%Y-%m-%d") + timedelta(days=4)
		cektanggal = setDueDateValue.strftime("%Y-%m-%d")
		if duedate < cektanggal:
			return {'value':{'duedate':cektanggal}}
		else:
			return {'value':{'duedate':duedate}}
		
	def create(self, cr, uid, vals, context=None):
		vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'pembelian.barang')
		return super(Pembelian_Barang, self).create(cr, uid, vals, context=context)
	def setDept(self,cr,uid,ids,pid):
		employee_id = self.pool.get('hr.employee').browse(cr,uid,pid) 
		dept_id = employee_id.department_id.id
		return {'value':{ 'department_id':dept_id} }
	
	def submit(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'confirm'})

	def edit(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'edit'})

	def setdraft(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'draft'})

	def confirm3(self,cr,uid,ids,context=None):
		val = self.browse(cr, uid, ids)[0]
		obj_detail_pb=self.pool.get('detail.pb')
		for detail in val.detail_pb_ids:
			if detail.state == 'draft':
				cr.execute('Update detail_pb Set state=%s Where id=%s', ('onproses',detail.id))
		return self.write(cr,uid,ids,{'state':'purchase'})

	def confirm(self,cr,uid,ids,context=None):
#		val = self.browse(cr, uid, ids)[0]
#		usermencet = self.pool.get('res.user')
#		if val.employee_id.parent_id.id != uid :
#			raise osv.except_osv(('Perhatian..!!'), ('Harus Atasannya langsung ..'))
		return self.write(cr,uid,ids,{'state':'confirm2'})

	def confirm2(self,cr,uid,ids,context=None):
#		val = self.browse(cr, uid, ids)[0]
#		usermencet = self.pool.get('res.user')
#		if val.employee_id.parent_id.id != uid :
#			raise osv.except_osv(('Perhatian..!!'), ('Harus Atasannya langsung ..'))
		cr.execute('Update detail_pb Set state=%s Where detail_pb_id=%s', ('onproses',ids[0]))
		return self.write(cr,uid,ids,{'state':'purchase'})

	def purchase(self,cr,uid,ids,context=None):
		return self.write(cr,uid,ids,{'state':'done'})


	def reportpb(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		datas = {'ids': context.get('active_ids', [])}
		datas['model'] = 'pembelian.barang'
		datas['form'] = self.read(cr, uid, ids)[0]
		
		return {
            'type': 'ir.actions.report.xml',
            'report_name': 'print.pb',
            'report_type': 'webkit',
            'datas': datas,
            }

Pembelian_Barang()

class Detail_PB(osv.osv):
    _name = 'detail.pb'
    _columns = {
        'name':fields.many2one('product.product','Product'),
        'variants':fields.many2one('product.variants','variants'),
        'part_no':fields.char('Part No'),
        'jumlah_diminta':fields.float('Qty'),
        'qty_available':fields.float('Qty Available'),
        'satuan':fields.many2one('product.uom','Product UOM'),
        'stok':fields.integer('Stock'),
        'customer_id':fields.many2one('res.partner','Customer', domain=[('customer','=',True)]),
        'harga':fields.float('Unit Price'),
        'subtotal':fields.float('Sub Total'),
        'keterangan':fields.text('Keterangan'),
        'detail_pb_id':fields.many2one('pembelian.barang', 'Referensi PB', required=True, ondelete='cascade'),
        'item': fields.many2many('set.po', 'pre_item_rel', 'permintaan_id', 'item_id', 'item'),
    	'state': fields.selection([
            ('draft', 'Draft'),
            ('onproses', 'Confirm'),
            ('proses','Proses'),
            ('done', 'Done'),
            ],
            'Status',readonly=True, select=True),
    }

    _defaults = {'state': 'draft'}

    def setvariants(self,cr,uid,ids, pid):
    	if pid:
	    	cek=self.pool.get('product.variants').search(cr,uid,[('product_id', '=' ,pid)])
	    	hasil=self.pool.get('product.variants').browse(cr,uid,cek)
	    	products=self.pool.get('product.product').browse(cr,uid,pid)
	    	pn = products.default_code
	    	product =[x.id for x in hasil]
	    	return {'domain': {'variants': [('id','in',tuple(product))]},'value':{'part_no':pn,'stok':products.qty_available,'satuan':products.uom_id.id}}

	def productvar(self,cr,uid,ids,idp):
		# cek=self.pool.get('product.variants').search(cr,uid,[('product_id', '=' ,idp)])
		print '========================',idp
		hasil=self.pool.get('product.variants').browse(cr,uid,idp)
		return {'value':{ 
						'part_no':hasil.default_code,
						'stok':hasil.qty_available,
						'satuan':hasil.uom_id.id,
						} }

    def jmlQty(self,cr,uid,ids, qty):
    	return {'value':{ 
						'qty_available':qty} }

Detail_PB()

class Type_PB(osv.osv):
	_name = 'type.pb'
	_columns= {
		'name' : fields.char('Type Permintaan'),
	}
		
Type_PB()

class Set_PO(osv.osv):
	_name = 'set.po'
	_columns ={
		'name':fields.many2one('res.partner','Supplier',required=True, domain=[('supplier','=',True),('is_company', '=', True)]),
		'pricelist_id':fields.many2one('product.pricelist', 'Pricelist', required=True),
		'permintaan': fields.many2many('detail.pb', 'pre_item_rel', 'item_id', 'permintaan_id', 'Detail Permintaan',domain=[('state','=','onproses')]),
	}
	
	def create_po(self,cr,uid,ids,fiscal_position_id=False,context=None):
		val = self.browse(cr, uid, ids)[0]
		# Perhitangan Pajak
		account_fiscal_position = self.pool.get('account.fiscal.position')
		account_tax = self.pool.get('account.tax')

		obj_purchase = self.pool.get("purchase.order")
		obj_purchase_line = self.pool.get('purchase.order.line')
		obj_detail_order_line=self.pool.get('detail.order.line')
		pb = [line.detail_pb_id.name for line in val.permintaan]
		detailpb = ''
		for x in set(pb):
			detailpb += x[:5] + ', '

		sid = obj_purchase.create(cr, uid, {
										'name':int(time.time()),
										'date_order': time.strftime("%Y-%m-%d"),
										'duedate':time.strftime("%Y-%m-%d"),
                                        'partner_id': val.name.id,
                                        'jenis': 'loc',
                                        'pricelist_id': val.pricelist_id.id,
                                        'location_id': 12,
                                        'origin':detailpb,
                                        'type_permintaan':'1',
                                        'term_of_payment':val.name.term_payment
                                       })
		noline=1
		for line in val.permintaan:
			taxes = account_tax.browse(cr, uid, map(lambda line: line.id, line.name.supplier_taxes_id))
			fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
			taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
			obj_purchase_line.create(cr, uid, {
										 'no':noline,
										 'date_planned': time.strftime("%Y-%m-%d"),
										 'order_id': sid,
                                         #'pb_id': products[line]['name'],
                                         # 'pb_id': line.detail_pb_id.id,
                                         'product_id': line.name.id,
                                         'variants':line.variants.id,
                                         'name':line.name.name,
                                         'part_number':line.name.default_code,
                                         'line_pb_general_id': line.id,
                                         'product_qty': line.qty_available,
                                         'product_uom': line.satuan.id,
                                         'price_unit': line.harga,
                                         'note_line':'-',
                                         'taxes_id': [(6,0,taxes_ids)],
                                         })
			noline=noline+1
			print '===================TEST NO====================',noline

		# purchase ==> Nama Module nya purchase_order_form ==> Nama Id Form nya
		pool_data=self.pool.get("ir.model.data")
		action_model,action_id = pool_data.get_object_reference(cr, uid, 'purchase', "purchase_order_form")     
		action_pool = self.pool.get(action_model)
		res_id = action_model and action_id or False
		action = action_pool.read(cr, uid, action_id, context=context)
		action['name'] = 'purchase.order.form'
		action['view_type'] = 'form'
		action['view_mode'] = 'form'
		action['view_id'] = [res_id]
		action['res_model'] = 'purchase.order'
		action['type'] = 'ir.actions.act_window'
		action['target'] = 'current'
		action['res_id'] = sid
		return action

Set_PO()

# class Search_PB(osv.osv_memory):
# 	_name = 'search.pb'
# 	_columns={
# 		'name':fields.many2many('detail.pb','search_pb_rel','search_detail_pb','id'),
# 	}

class Wizard_Detail_PB(osv.osv):
	_name = 'wizard.detail.pb'
	_columns ={
		'name':fields.many2one('pembelian.barang','No PB', domain=[('state','=','purchase')]),
		'product':fields.many2one('product.product','Product'),
		'variants':fields.many2one('product.variants','variants'),
		'qty':fields.integer('Qty'),
		'price_unit':fields.integer('Price Unit', required=True),
		'id_product_detail':fields.integer('id'),
		'detail_pb_id':fields.many2one('set.po', 'Detail PO', required=True, ondelete='cascade'),
		# 'detail_pb_ids': fields.many2many('detail.pb', 'detail_set_pb', 'Detail Permintaan Barang'),
	}
	
	def setProduct(self,cr,uid,ids, pid):
		pb_id = self.pool.get('pembelian.barang').browse(cr,uid, pid)
		cek=self.pool.get('detail.pb').search(cr,uid,[('detail_pb_id', '=' ,pb_id.id),('state', '=' ,'onproses')])
		#product =[x.name.id for x in pb_id.detail_pb_ids]
		hasil=self.pool.get('detail.pb').browse(cr,uid,cek)
		product =[x.name.id for x in hasil]
		return {'domain': {'product': [('id','in',tuple(product))]}}
	
	def setQty(self,cr,uid,ids, pid, pb):
		pb_id = self.pool.get('pembelian.barang').browse(cr,uid, pb) 
		pb_product = self.pool.get('pembelian.barang').browse(cr,uid, pid)
		cek=self.pool.get('detail.pb').search(cr,uid,[('detail_pb_id', '=' ,pb_id.id),('name', '=' ,pid)])
		hasil=self.pool.get('detail.pb').browse(cr,uid,cek)[0]
		return {'value':{ 'qty':hasil.qty_available, 'id_product_detail':hasil.id} }

Wizard_Detail_PB()


class Detail_Order_Line(osv.osv):
	_name = 'detail.order.line'
	_columns = {
		'name':fields.integer('Id'),
		'order_line_id':fields.integer('Id Order Line'),
		'detail_pb_id':fields.integer('Id Detail PB'),
		'qty':fields.float('Qty'),
	}

Detail_Order_Line()


class Product_Variants(osv.osv):
	_name = 'product.variants'
	_columns = {
		# 'name':fields.integer('variants_id'),
		'product_id':fields.many2one('product.product','Product'),
		'name':fields.char('Variants'),
		'satuan':fields.many2one('product.uom','Product UOM'),
	}

Product_Variants()