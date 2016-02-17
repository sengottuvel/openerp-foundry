
import time
from report import report_sxw
from reportlab.pdfbase.pdfmetrics import stringWidth
import locale
from datetime import datetime, date
import ast


class kg_category_count_report(report_sxw.rml_parse):
    
    _name = 'kg.category.count.report'
    
    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(kg_category_count_report, self).__init__(cr, uid, name, context=context)
        self.query = ""
        self.period_sql = ""
        self.localcontext.update( {
            'time': time,
            'get_filter': self._get_filter,
            'get_start_date':self._get_start_date,
            'get_end_date':self._get_end_date,
            'get_data':self.get_data,
            'locale':locale,
            #'get_data_line':self.get_data_line,

        })
        self.context = context
        
    def get_data(self,form):
        
        res = {}
        where_sql = []
        partner = []
        product = []
        ap_state1 = []
        ap_state2 = []
        ap_state3 = []
        gr_tot1 = 0
        gr_tot2 = 0
        gr_tot3 = 0
        gr_tot4 = 0
        gr_tot5 = 0
        gr_tot6 = 0
        gr_other_tot = 0
        gr_qty1 = 0
        gr_qty2 = 0
        gr_qty3 = 0
        gr_qty4 = 0
        gr_qty5 = 0
        gr_qty6 = 0
        gr_other_qty = 0
        data = []
        user_list = [1,2,3,4,5,6]   
        other_user = [] 
        gr_sum_col = 0
        gr_sum_qty = 0
         
        if form['supplier']:
            for ids1 in form['supplier']:
                partner.append("po.partner_id = %s"%(ids1))
        
        if form['product_id']:
            for ids2 in form['product_id']:
                product.append("pol.product_id = %s"%(ids2))        
        
        if form['status']:
            if form['status'] == 'approved':
                ap_state1.append("po.state = %s"%('approved'))  
                ap_state2.append("so.state = %s"%('approved'))  
                ap_state3.append("gg.state = %s"%('done'))  
                
            if form['status'] == 'cancelled':
                ap_state1.append("po.state = %s"%('cancel'))    
                ap_state2.append("so.state = %s"%('cancel'))    
                ap_state3.append("gg.state = %s"%('cancel'))    
    

        if partner:
            partner = 'and ('+' or '.join(partner)
            partner =  partner+')'
            print "partner -------------------------->>>>", partner
        else:
            partner = ''
            
        if product:
            product = 'and ('+' or '.join(product)
            product =  product+')'
            print "product -------------------------->>>>", product
        else:
            product = ''
        
        if ap_state1:
            ap_state1 = 'and ('+' or '.join(ap_state1)
            ap_state1 =  ap_state1+')'
            
        else:
            ap_state1 = ''
            
        if ap_state2:
            ap_state2 = 'and ('+' or '.join(ap_state2)
            ap_state2 =  ap_state2+')'
            
        else:
            ap_state2 = ''
        
        if ap_state3:
            ap_state3 = 'and ('+' or '.join(ap_state3)
            ap_state3 =  ap_state3+')'
            
        else:
            ap_state3 = ''      
        
        self.cr.execute('''select res.id as uid,res.login as name from res_users res where active='t' and res.id != 1''')
        
        data1=self.cr.dictfetchall()
        for user in data1:
            if user['name'] == 'kavitha':
                user_list[0] = user['uid']
            elif user['name'] == 'tamilselvi':
                user_list[1] = user['uid']
            elif user['name'] == 'reena':
                user_list[2] = user['uid']
            elif user['name'] == 'nandakumar':
                user_list[3] = user['uid']
            elif user['name'] == 'vadivel':
                user_list[4] = user['uid']
            elif user['name'] == 'senthil':
                user_list[5] = user['uid']
            else:
                other_user.append(user['uid'])                  
        print "--------------------------->",user_list  
        print "--------------------------->",other_user 
        
        self.cr.execute('''SELECT      
                            pc.name as category,
                            pc.id as cat_id,
                            res.login as user,
                            res.id as user_id,
                            sum(pol.product_qty * pol.price_unit) as quantity,
                            count(pc.name) as cat_count
                                  
                            FROM  purchase_order_line pol 

                            JOIN purchase_order po ON (po.id = pol.order_id)
                            JOIN res_users res ON (res.id = pol.create_uid)
                            JOIN product_product prd ON (prd.id=pol.product_id)
                            JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
                            JOIN product_category pc ON (pc.id=pt.categ_id)
                            where po.date_order >=%s and po.date_order <=%s
                            group by 1,2,3,4

                            union

                            SELECT      
                            pc.name as category,
                            pc.id as cat_id,
                            res.login as user,
                            res.id as user_id,
                            sum(sol.product_qty * sol.price_unit) as quantity,
                            count(pc.name) as cat_count
                                  
                            FROM  kg_service_order_line sol 

                            JOIN kg_service_order so ON (so.id = sol.service_id)
                            JOIN res_users res ON (res.id = sol.create_uid)
                            JOIN product_product prd ON (prd.id=sol.product_id)
                            JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
                            JOIN product_category pc ON (pc.id=pt.categ_id)
                            where so.date >=%s and so.date <=%s
                            group by 1,2,3,4

                            union

                            SELECT      
                            pc.name as category,
                            pc.id as cat_id,
                            res.login as user,
                            res.id as user_id,
                            sum(ggl.grn_qty * ggl.price_unit) as quantity,
                            count(pc.name) as cat_count
                                  
                            FROM  kg_general_grn_line ggl 

                            JOIN kg_general_grn gg ON (gg.id = ggl.grn_id)
                            JOIN res_users res ON (res.id = ggl.create_uid)
                            JOIN product_product prd ON (prd.id=ggl.product_id)
                            JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
                            JOIN product_category pc ON (pc.id=pt.categ_id)
                            where gg.grn_date >=%s and gg.grn_date <=%s
                            group by 1,2,3,4
                            ''',(form['date_from'],form['date_to'],form['date_from'],form['date_to'],form['date_from'],form['date_to']))
        
        data11=self.cr.dictfetchall()
        
        category_list = []
        
            
        for item in data11:
            if item['cat_id'] not in category_list and item['cat_count'] > 0:
                category_list.append(item['cat_id'])
        print "--------------------------->",category_list  
        
        for cat in category_list:
            category_dict = {}
            user_cot = []   
            other_cot = 0.0 
            sum_col = 0
            sum_qty = 0
           
            user_qty = []   
            other_qty = 0.0 
            cat_rec = self.pool.get('product.category').browse(self.cr, self.uid, cat)
            category_dict['cat_name'] = cat_rec.name
            for use in user_list:
                self.cr.execute('''SELECT      
                    pc.name as category,
                    pc.id as cat_id,
                    res.login as user,
                    res.id as user_id,
                    sum(pol.product_qty * pol.price_unit) as quantity,
                    count(pc.name) as cat_count
                              
                    FROM  purchase_order_line pol 
                        
                    JOIN purchase_order po ON (po.id = pol.order_id)
                    JOIN res_users res ON (res.id = pol.create_uid)
                    JOIN product_product prd ON (prd.id=pol.product_id)
                    JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
                    JOIN product_category pc ON (pc.id=pt.categ_id)
                
                      where po.date_order >=%s and po.date_order <=%s and pc.id = %s and res.id = %s'''+ product + partner + ap_state1 +'''
                      group by 1,2,3,4''',(form['date_from'],form['date_to'],cat,use)) 
                data2=self.cr.dictfetchall()
                
                self.cr.execute('''SELECT      
                        pc.name as category,
                        pc.id as cat_id,
                        res.login as user,
                        res.id as user_id,
                        sum(sol.product_qty * sol.price_unit) as quantity,
                        count(pc.name) as cat_count
                              
                        FROM  kg_service_order_line sol 

                        JOIN kg_service_order so ON (so.id = sol.service_id)
                        JOIN res_users res ON (res.id = sol.create_uid)
                        JOIN product_product prd ON (prd.id=sol.product_id)
                        JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
                        JOIN product_category pc ON (pc.id=pt.categ_id)         
                        where so.date >=%s and so.date <=%s and pc.id = %s and res.id = %s'''+ product + partner + ap_state2 +'''
                      group by 1,2,3,4''',(form['date_from'],form['date_to'],cat,use))
    
                data3=self.cr.dictfetchall()
                
                self.cr.execute('''SELECT      
                            pc.name as category,
                            pc.id as cat_id,
                            res.login as user,
                            res.id as user_id,
                            sum(ggl.grn_qty * ggl.price_unit) as quantity,
                            count(pc.name) as cat_count
                                  
                            FROM  kg_general_grn_line ggl 

                            JOIN kg_general_grn gg ON (gg.id = ggl.grn_id)
                            JOIN res_users res ON (res.id = ggl.create_uid)
                            JOIN product_product prd ON (prd.id=ggl.product_id)
                            JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
                            JOIN product_category pc ON (pc.id=pt.categ_id)     
                        where gg.grn_date >=%s and gg.grn_date <=%s and pc.id = %s and res.id = %s'''+ product + partner + ap_state3 +'''
                      group by 1,2,3,4''',(form['date_from'],form['date_to'],cat,use))
    
                data4=self.cr.dictfetchall()
                if data2:
                    a2 = data2[0]['cat_count']
                    b2 = data2[0]['quantity']
                else:
                    a2 = 0   
                    b2 = 0    
                if data3:
                    a3 = data3[0]['cat_count']
                    b3 = data3[0]['quantity']
                else:
                    a3 = 0
                    b3 = 0
                if data4:
                    a4 = data4[0]['cat_count']
                    b4 = data4[0]['quantity']
                else:
                    a4 = 0
                    b4 = 0            
                user_cot.append(a2 + a3 + a4)
                user_qty.append(b2 + b3 + b4)
            gr_tot1 += user_cot[0]    
            gr_tot2 += user_cot[1]    
            gr_tot3 += user_cot[2]    
            gr_tot4 += user_cot[3]    
            gr_tot5 += user_cot[4]    
            gr_tot6 += user_cot[5]    
            
            gr_qty1 += user_qty[0] 
            gr_qty2 += user_qty[1] 
            gr_qty3 += user_qty[2] 
            gr_qty4 += user_qty[3] 
            gr_qty5 += user_qty[4] 
            gr_qty6 += user_qty[5] 
            
            category_dict['count'] = user_cot[0]    
            category_dict['count1'] = user_cot[1]    
            category_dict['count2'] = user_cot[2]    
            category_dict['count3'] = user_cot[3]    
            category_dict['count4'] = user_cot[4]    
            category_dict['count5'] = user_cot[5]
            category_dict['quantity'] = user_qty[0]    
            category_dict['quantity1'] = user_qty[1]    
            category_dict['quantity2'] = user_qty[2]    
            category_dict['quantity3'] = user_qty[3]    
            category_dict['quantity4'] = user_qty[4]    
            category_dict['quantity5'] = user_qty[5] 
               
            category_dict['gr_count'] = gr_tot1
            category_dict['gr_count1'] = gr_tot2  
            category_dict['gr_count2'] = gr_tot3   
            category_dict['gr_count3'] = gr_tot4   
            category_dict['gr_count4'] = gr_tot5   
            category_dict['gr_count5'] = gr_tot6
            category_dict['gr_quantity'] = gr_qty1     
            category_dict['gr_quantity1'] = gr_qty2    
            category_dict['gr_quantity2'] = gr_qty3  
            category_dict['gr_quantity3'] = gr_qty4    
            category_dict['gr_quantity4'] = gr_qty5    
            category_dict['gr_quantity5'] = gr_qty6   
                
            if  form['user_name']:
                   
                self.cr.execute('''SELECT      
                    pc.name as category,
                    pc.id as cat_id,
                    res.login as user,
                    res.id as user_id,
                    sum(pol.product_qty * pol.price_unit) as quantity,
                    count(pc.name) as cat_count
                              
                    FROM  purchase_order_line pol 
                        
                    JOIN purchase_order po ON (po.id = pol.order_id)
                    JOIN res_users res ON (res.id = pol.create_uid)
                    JOIN product_product prd ON (prd.id=pol.product_id)
                    JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
                    JOIN product_category pc ON (pc.id=pt.categ_id)
                
                      where po.state = 'approved' and po.date_order >=%s and po.date_order <=%s and pc.id = %s and res.login = %s'''+ product + partner + ap_state1 + '''
                      group by 1,2,3,4''',(form['date_from'],form['date_to'],cat,form['user_name']))
    
                data5=self.cr.dictfetchall()
                
                self.cr.execute('''SELECT      
                        pc.name as category,
                        pc.id as cat_id,
                        res.login as user,
                        res.id as user_id,
                        sum(sol.product_qty * sol.price_unit) as quantity,
                        count(pc.name) as cat_count
                              
                        FROM  kg_service_order_line sol 

                        JOIN kg_service_order so ON (so.id = sol.service_id)
                        JOIN res_users res ON (res.id = sol.create_uid)
                        JOIN product_product prd ON (prd.id=sol.product_id)
                        JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
                        JOIN product_category pc ON (pc.id=pt.categ_id)         
                        where so.date >=%s and so.date <=%s and pc.id = %s and res.login = %s'''+ product + partner + ap_state2 +'''
                      group by 1,2,3,4''',(form['date_from'],form['date_to'],cat,form['user_name']))
    
                data6=self.cr.dictfetchall()
                
                self.cr.execute('''SELECT      
                            pc.name as category,
                            pc.id as cat_id,
                            res.login as user,
                            res.id as user_id,
                            sum(ggl.grn_qty * ggl.price_unit) as quantity,
                            count(pc.name) as cat_count
                                  
                            FROM  kg_general_grn_line ggl 

                            JOIN kg_general_grn gg ON (gg.id = ggl.grn_id)
                            JOIN res_users res ON (res.id = ggl.create_uid)
                            JOIN product_product prd ON (prd.id=ggl.product_id)
                            JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
                            JOIN product_category pc ON (pc.id=pt.categ_id)     
                        where gg.grn_date >=%s and gg.grn_date <=%s and pc.id = %s and res.login = %s'''+ product + partner + ap_state3 +'''
                      group by 1,2,3,4''',(form['date_from'],form['date_to'],cat,form['user_name']))
    
                data7=self.cr.dictfetchall()
                if data5:
                    a5 = data5[0]['cat_count']
                    b5 = data5[0]['quantity']
                else:
                    a5 = 0
                    b5 = 0    
                if data6:
                    a6 = data6[0]['cat_count']
                    b6 = data6[0]['quantity']
                else:
                    a6 = 0
                    b6 = 0
                if data7:
                    a7 = data7[0]['cat_count']
                    b7 = data7[0]['quantity']
                else:
                    a7 = 0
                    b7 = 0            
                
                other_cot +=(a5 + a6 + a7)
                other_qty +=(b5 + b6 + b7)
        
            else:
                for other_use in other_user:
                    self.cr.execute('''SELECT      
                    pc.name as category,
                    pc.id as cat_id,
                    res.login as user,
                    res.id as user_id,
                    sum(pol.product_qty * pol.price_unit) as quantity,
                    count(pc.name) as cat_count
                              
                    FROM  purchase_order_line pol 
                        
                    JOIN purchase_order po ON (po.id = pol.order_id)
                    JOIN res_users res ON (res.id = pol.create_uid)
                    JOIN product_product prd ON (prd.id=pol.product_id)
                    JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
                    JOIN product_category pc ON (pc.id=pt.categ_id)
                
                      where po.date_order >=%s and po.date_order <=%s and pc.id = %s and res.id = %s'''+ product + partner + ap_state1 +'''
                      group by 1,2,3,4''',(form['date_from'],form['date_to'],cat,other_use))
    
                    data8=self.cr.dictfetchall()
                    
                    self.cr.execute('''SELECT      
                            pc.name as category,
                            pc.id as cat_id,
                            res.login as user,
                            res.id as user_id,
                            sum(sol.product_qty * sol.price_unit) as quantity,
                            count(pc.name) as cat_count
                                  
                            FROM  kg_service_order_line sol 

                            JOIN kg_service_order so ON (so.id = sol.service_id)
                            JOIN res_users res ON (res.id = sol.create_uid)
                            JOIN product_product prd ON (prd.id=sol.product_id)
                            JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
                            JOIN product_category pc ON (pc.id=pt.categ_id)         
                            where so.date >=%s and so.date <=%s and pc.id = %s and res.id = %s'''+ product + partner + ap_state2 +'''
                          group by 1,2,3,4''',(form['date_from'],form['date_to'],cat,other_use))
        
                    data9=self.cr.dictfetchall()
                    
                    self.cr.execute('''SELECT      
                                pc.name as category,
                                pc.id as cat_id,
                                res.login as user,
                                res.id as user_id,
                                sum(ggl.grn_qty * ggl.price_unit) as quantity,
                                count(pc.name) as cat_count
                                      
                                FROM  kg_general_grn_line ggl 

                                JOIN kg_general_grn gg ON (gg.id = ggl.grn_id)
                                JOIN res_users res ON (res.id = ggl.create_uid)
                                JOIN product_product prd ON (prd.id=ggl.product_id)
                                JOIN product_template pt ON (pt.id=prd.product_tmpl_id)
                                JOIN product_category pc ON (pc.id=pt.categ_id)     
                            where gg.grn_date >=%s and gg.grn_date <=%s and pc.id = %s and res.id = %s'''+ product + partner + ap_state3 +'''
                          group by 1,2,3,4''',(form['date_from'],form['date_to'],cat,other_use))
        
                    data10=self.cr.dictfetchall()
                    if data8:
                        a8 = data8[0]['cat_count']
                        b8 = data8[0]['quantity']
                    else:
                        a8 = 0
                        b8 = 0    
                    if data9:
                        a9 = data9[0]['cat_count']
                        b9 = data9[0]['quantity']
                    else:
                        a9 = 0
                        b9 = 0
                    if data10:
                        a10 = data10[0]['cat_count']
                        b10 = data10[0]['quantity']
                    else:
                        a10 = 0
                        b10 = 0       
                    other_cot += (a8 + a9 + a10)
                    other_qty += (b8 + b9 + b10)
                
            category_dict['other_count'] = other_cot
            category_dict['other_quantity'] = other_qty 
            gr_other_tot += other_cot
            gr_other_qty += other_qty 
            category_dict['gr_other_count'] = gr_other_tot 
            category_dict['gr_other_quantity'] = gr_other_qty 
            sum_col = (category_dict['count'] +  category_dict['count1'] + category_dict['count2'] + category_dict['count3'] + 
                        category_dict['count4'] + category_dict['count5'] + category_dict['other_count'] )
            sum_qty = (category_dict['quantity'] +  category_dict['quantity1'] + category_dict['quantity2'] + category_dict['quantity3'] + 
                        category_dict['quantity4'] + category_dict['quantity5'] + category_dict['other_quantity'] )
                        
            gr_sum_col += (category_dict['count'] +  category_dict['count1'] + category_dict['count2'] + category_dict['count3'] + 
                        category_dict['count4'] + category_dict['count5'] + category_dict['other_count'] )
            gr_sum_qty += (category_dict['quantity'] +  category_dict['quantity1'] + category_dict['quantity2'] + category_dict['quantity3'] + 
                        category_dict['quantity4'] + category_dict['quantity5'] + category_dict['other_quantity'] ) 
                        
            category_dict['sum_col'] = sum_col                  
            category_dict['sum_qty'] = sum_qty                  
            category_dict['gr_sum_col'] = gr_sum_col                    
            category_dict['gr_sum_qty'] = gr_sum_qty
            if  sum_col > 0:
                data.append(category_dict)      
            else:
                pass            
            print "----------------------------------------------------------->",category_dict
        
                
        print "----------------------------------------------------------->",data 
           
        return data
        
        
    def _get_filter(self, data):
        if data.get('form', False) and data['form'].get('filter', False):
            if data['form']['filter'] == 'filter_date':
                return _('Date')
            
        return _('No Filter')
        
    def _get_start_date(self, data):
        if data.get('form', False) and data['form'].get('date_from', False):
            return data['form']['date_from']
        return ''
        
    def _get_end_date(self, data):
        if data.get('form', False) and data['form'].get('date_to', False):
            return data['form']['date_to']
        return ''          
  

report_sxw.report_sxw('report.kg.category.count.report', 'purchase.order', 
            'addons/kg_po_reports/report/kg_category_count_report.rml', 
            parser=kg_category_count_report, header = False)
