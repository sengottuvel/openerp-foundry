openerp.kg_scheduler = function (instance)
{  
var _t = instance.web._t;
	_lt = instance.web._lt;
var QWeb = instance.web.qweb;	
	instance.kg_popup = {};
    instance.web.form.widgets.add('product_expiry_reminder', 'instance.kg_popup.Mywidget');
    instance.kg_popup.Mywidget = instance.web.form.FieldChar.extend(
        {
        template : "product_expiry_reminder",
        init: function () {
            this._super.apply(this, arguments);

        },
        start: function (ids) {
			var self = this;
			var model= new instance.web.Model("kg.popup")
			model.call("get_product_expiry_reminder_data",[ids]).then(function (i) {
				var title="<div class='grad3'><center><font color='white'>Product Expiry Reminders</font></center></div>"
				var body="<div class='sub'>"+
							"<table id='table1'>"+
							"<tr></th><th>GRN No.</th><th>Product</th><th>UOM</th><th>Exp Date</th><th>Pen Qty</th><th>Sl No.</tr>"
				//alert(i);
				n=i.length;
				if (n!=0){
					//To perform only if it contains to display as pop
					var body_1 = ''
					for(var m=0;m<n;m++) {
						body_1 += "<tr><td>"+i[m][0]+"</td><td>"+i[m][1]+"</td><td>"+i[m][2]+"</td><td>"+i[m][3]+"</td><td>"+i[m][4]+"</td><td>"+i[m][5]+"</td></tr>"
					}
					body_1 += "</table>"+
								"</div>"
					body = body + body_1
					var x=true
					var tiry=instance.webclient.notification.warn(_t(title), _t(body), x);
					setTimeout(function() {tiry.close();}, 18000)
					//To display the POP-up for every 'N' seconds
					this.__blur_timeout = setInterval(function () {
					var tiry=instance.webclient.notification.warn(_t(title), _t(body), x);
					setTimeout(function() {tiry.close();}, 18000)
					}, 3600000);
				}
				else{
					//If no data for the current date, it display the none or alert
					//alert('null');it is optional
				}
			});
		},
    });
};
