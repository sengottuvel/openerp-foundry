/***** Ticket 3237 */
/* Except Special Character */
var specialKeys = new Array();
	specialKeys.push(8); //Backspace
	specialKeys.push(9); //Tab
	specialKeys.push(46); //Delete
	specialKeys.push(36); //Home
	specialKeys.push(35); //End
	specialKeys.push(37); //Left
	specialKeys.push(39); //Right			

function aplhanumonly(e) {	
	var keyCode = e.keyCode == 0 ? e.charCode : e.keyCode;
	var ret = ((keyCode >= 48 && keyCode <= 57) || (keyCode >= 65 && keyCode <= 90) || (keyCode >= 97 && keyCode <= 122) || (specialKeys.indexOf(e.keyCode) != -1 && e.charCode != e.keyCode));
	return ret;
}
/* End Except Special Character */

/* For Email validation */
function email_validation(e) {	
	var keyCode = e.keyCode == 0 ? e.charCode : e.keyCode;
	var ret = ((keyCode >= 48 && keyCode <= 57) || (keyCode >= 65 && keyCode <= 90) || (keyCode >= 97 && keyCode <= 122) || (specialKeys.indexOf(e.keyCode) != -1 && e.charCode != e.keyCode));
	if(keyCode == 46 || keyCode == 64){ //allowed keyCode . ( ) -
		return true;
	}
	return ret;
}

function validateEmail(email) {	
	var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
	return re.test(email);
}

function email_validationn(e,ele) {
	$('body').find('.oe_form_button_save').attr('disabled',true);
	$(ele).text("");
	var email = $(ele).val();
	if (validateEmail(email)) {
	  $('body').find('.oe_form_button_save').attr('disabled',false);
	} else {
	  toastr.error('Invalid Email ID.', 'Error');
	}
	return false;
}
/* End For Email validation */

/* For Float Values */
function aplhanum_expect(e) {	
	var keyCode = e.keyCode == 0 ? e.charCode : e.keyCode;
	var ret = ((keyCode >= 48 && keyCode <= 57) || (keyCode >= 65 && keyCode <= 90) || (keyCode >= 97 && keyCode <= 122) || (specialKeys.indexOf(e.keyCode) != -1 && e.charCode != e.keyCode));
	if(keyCode == 46 || keyCode == 40 || keyCode == 41 || keyCode == 45 || keyCode == 32){ //allowed keyCode . ( ) -
		return true;
	}
	return ret;
}
/* End For Float Values */

/* Only Numbers */
function numberonly(evt) {
    evt = (evt) ? evt : window.event;
    var charCode = (evt.which) ? evt.which : evt.keyCode;
    if (charCode > 31 && (charCode < 48 || charCode > 57)) {
        return false;
    }
    return true;
}
/* End Only Numbers */

/* Only Letters */
function lettersOnly(evt) {
	evt = (evt) ? evt : window.event;
    var charCode = (evt.which) ? evt.which : evt.keyCode;
    if ((charCode > 64 && charCode < 91) || (charCode > 96 && charCode < 123) || charCode == 8) {
        return true;
    }
    return false;
}
/* End Only Letters */
/***** End Ticket 3237 */

/***** Current year in copyright */
var d = new Date();
var n = d.getFullYear();
function footer(){
	$('#curntyear').text(n);
	$('#nextyear').text(n+1);
}
/***** End Current year in copyright */
