/* Navigation.js Copyright (c) 2010 Jay Carlson */
var Navigation = new Class({
	Implements: [Options, Events],
	options: {
		interval: 200
		
	},
	state: null,
	oldLocation: "",
	initialize: function(options) {
		this.setOptions(options);
		this.state = new Hash();
		if("onhashchange" in window) {
			window.onhashchange = this.agent.bind(this);
			this.agent();
		} else {
		var navigationChangeTimer = setInterval(this.agent.bind(this), this.options.interval);
		}
	},
	
	agent: function() {
		if(this.oldLocation.length < 1 || this.oldLocation != window.location.hash.substr(1, window.location.hash.length-1)) { //only update if the location changed
			this.oldLocation = window.location.hash.substr(1, window.location.hash.length-1);
			this.state.empty();
			this.state.extend(this.oldLocation.parseQueryString(false, true));
			this.fireEvent("navigationChanged", this.state);
		}	
	},
	updateLocation: function() {
		window.location.hash = this.state.toQueryString().cleanQueryString();	
	},
	set: function(key, value) {
		if(typeOf(key) != "string" && value == null) {
			this.state.extend(key);
		} else {
			this.state.set(key, value);
		}
		this.updateLocation();
	},
	unset: function(keys) {
		if(typeOf(keys)=="string") {
			this.state.erase(keys);
		} else {
			keys.each(function(item) {
				this.state.erase(item);
			}.bind(this));	
		}
		this.updateLocation();
	},
	clearAndSet: function(key, value) {
		this.state.empty();
		this.set(key, value);
	}
});

Element.implement({
	switchClass : function(first, second) {
		var hasSecond = this.hasClass(second);
		this.removeClass( hasSecond ? second : first);
		this.addClass( hasSecond ? first : second);
		return this;
	}
});

// deprecated from 1.3; found in 1.2
var $defined = function(obj){
	return (obj != undefined);
};


var serialize = function(context){
	var form = $(context);
	var form_data = new Hash();
	// input[type=text]
	$$(context +' input[type=text]').each(function(item,key){
		form_data[item.get('name')] = item.get('value');
	});
	// input[type=password]
	$$(context +' input[type=password]').each(function(item, key){
		form_data[item.get('name')] = item.get('value');
	});
	// input[type=radio]
	$$(context + ' input[type=radio]').each(function(item, key){
		if (item.checked)
			form_data[item.name] = item.value
	});
	// input[type=checkbox]
	$$(context + ' input[type=checkbox]').each(function(item,key){
		if ( ! form_data.has(item.name) ) 
			form_data[item.name] = [];
		if (item.checked) {
			ar = form_data[item.name]
			form_data[item.name][ar.length] = item.value;
			console.log(form_data[item.name])
		}
	});
	return form_data;
}

function generate_ajax_url(withAjaxKey,extra_data) {
    extra_data = extra_data || {};
    withAjaxKey = withAjaxKey || false;
    var n = new Hash( location.hash.replace('#','').parseQueryString(false, true) );
    n.extend(extra_data);
    var request_url = 'ajax/?';
    n.each(function(item,key){
        if (key == 'section') {request_url += key + '=' + item; }
        else {request_url += '&' + key + '=' + item;}
    })
    if (withAjaxKey) request_url += '&ajaxKey=' + ajaxKey;
    return request_url
}


// table related functions
// uses moo
function create_data_table(thead_rows, tbody_rows, insertion_point) {

	var tbl = new Element('table', {
		'class': 'sql zebra-striped',
		'id': 'query_results',
		'summary': 'items returned from table'
	})
	th_rows = ['']
	th_rows.append(thead_rows)
	thead_rows = th_rows;
	
	data_table = new HtmlTable(tbl, {
		properties: {},
		headers: thead_rows,
		zebra: true, 
		selectable:false,
		sortable:true
	});
	
	// hack: create ids for the generated table
	for (var i = 0; i < tbody_rows.length; i++) {
		data_table.push(tbody_rows[i], {
			'id': 'row_'+(i + 1)
		})
	}
	
	// add checkboxes to the table
	trs = $(data_table).getElements('tr')
	tdd = new Element('th', {'id': 'selector'});
	for (var i=1; i < trs.length; i++) {
		td_select = new Element('td', {'class': 'selector'});
		anc_check = new Element('input', {'class': 'checker',	'id': 'check_' + i,	'type': 'checkbox'	});
		anc_check.inject(td_select)
		td_select.inject(trs[i], 'top')
	}
	
    if ( $('query_results') == null) { data_table.inject($(insertion_point) ); }
    else { data_table.replaces( $('query_results') ); data_table.id = 'query_results'; }
	
	
	//reduce the width of the first tr element
	$$('.sql thead tr th')[0].addClass('selector').setStyles({
		'max-width': '25px',
		'min-width': '25px',
		'width': '25px'
	});
	
	// select a tr element or a range of tr elements when the shift key is pressed
	selected_tr = ''
	$$('input.checker').addEvent('click', function(e) {
		last_selected_tr = selected_tr || '';
		id =  e.target.getProperty('id');
		id = id.replace('check', 'row'); // id of equivalent <tr>
		selected_tr = $(id)
		if (e.shift && typeof(last_selected_tr == 'element')){
			toggle_tr_range_selection(data_table, last_selected_tr, selected_tr)
		} else {
			toggle_tr_selection( $(id) )
		}		
		
	});
	return data_table;
}

function toggle_tr_selection(selected_row) {
	if ( selected_row.hasClass('table-tr-selected') ) {
		selected_row.removeClass('table-tr-selected')
	} else {
		selected_row.addClass('table-tr-selected')
	}
}

// for selecting and deselecting all the trs of a table
// state = true : ticks all checkboxes and selects all rows
// state = false : unticks all checkboxes and deselects all rows
function set_all_tr_state(context, state) {
	tbody_children = $(context).getChildren()[1].getChildren();
	for (var i=0; i < tbody_children.length; i++) {
	  	state ? tbody_children[i].addClass('table-tr-selected'): tbody_children[i].removeClass('table-tr-selected');
	  	$('check_'+(i + 1)).setProperty('checked', state);
	}
}

// selects a range of tr elements and checkboxes
// context: HtmlTableElement, begin: Element, end: Element
function toggle_tr_range_selection(context, begin, end) {
	tbody_children = $(context).getChildren()[1].getChildren();
	begin_index = tbody_children.indexOf($(begin));
	end_index = tbody_children.indexOf($(end));
	for (var i = (begin_index + 1); i < (end_index + 1); i++) {
		// toggle selection state of a tr element
		toggle_tr_selection( tbody_children[i] );
		// toggle check boxes checked property
		checker_id = tbody_children[i].getChildren()[0].getChildren()[0].id
		if ($(checker_id).getProperty('checked')) {
			$(checker_id).setProperty('checked', false)
		} else {
			$(checker_id).setProperty('checked', true)
		}
	}
	// includes selection and deselection of the last checkbox
	last_checker_id = tbody_children[end_index].getChildren()[0].getChildren()[0].id;
	if ($(last_checker_id).getProperty('checked')) {
		$(last_checker_id).setProperty('checked', false);
	} else {
		$(last_checker_id).setProperty('checked', true);
	}
}

var ss_rows = ''
/**
 * function: generates data from the selected trs
 * returns: an array withe each member an array of the contents of one row
 */
function generate_submit_data(context, e) {
	var selected_rows = $$('#'+context+' tr.table-tr-selected');
	var rows = [];
    selected_rows.each(function(row){
        row_kids = row.getChildren('[class!=selector]');
        var r = [];
        row_kids.each(function(kid){
           r.push( kid.childNodes[0].nodeValue ) 
        }); rows.push( r );
    });
    var th_divs = $$('#'+context+' th div'); var cols = [];
    th_divs.each(function(diva, diva_index){
        if (diva_index != 0) cols.push(diva.childNodes[1].nodeValue);
    })
    if (e) e.preventDefault()
	h_tab = new Hash({'count': rows.length,'rows': rows,'columns': cols});
	return h_tab;
	
}

function isThereSelection(context,e) {
	if ( $$('#'+context+' tr.table-tr-selected') ) return true
	else return False
}
function generate_where(context, e) {
	var selected_rows = $$('#'+context+' tr.table-tr-selected');
    var whereToEdit = '';
    if (! selected_rows) {
        return whereToEdit;
    }else {
        var th_divs = $$('#'+context+' th div'); var cols = [];
        th_divs.each(function(diva, diva_index){
            if (diva_index != 0) cols.push(diva.childNodes[1].nodeValue);
        })
        selected_rows.each(function(tiri,tiri_index){
            var where = '';
            tiri.getChildren('td[class!=selector]').each(function(tida,tida_index){
                where += ' ' + cols[tida_index] + '=' + tida.childNodes[0].nodeValue +'';
                if (tida != tiri.getLast() )
                    where += ' AND';
            });
            whereToEdit += where
            if (tiri != selected_rows.getLast() ) whereToEdit += '; ';
        });
        return whereToEdit;   
    }
}

function runXHRJavascript(){
    console.log('runXHRJavaxript() called!');
	var scripts = $ES("script", 'rightside');
	for (var i=0; i<scripts.length; i++) {
		// basic xss prevention
		if (scripts[i].get("ajaxKey") == ajaxKey) {
			var toRun = scripts[i].get('html');
			var newScript = new Element("script");
			newScript.set("type", "text/javascript");
			if (!Browser.ie) {
				newScript.innerHTML = toRun;
			} else {
				newScript.text = toRun;
			}
			document.body.appendChild(newScript);
			document.body.removeChild(newScript);
		}
	}
}

function f(g) {
	if (g == undefined || g == "undefined" || g == null)
		return "";
	else
		return g;
}

var $E = function(selector, filter) {
	return ($(filter) || document).getElement(selector);
};

var $ES = function(selector, filter) {
	return ($(filter) || document).getElements(selector);
};

function reloadPage(){
	context = new Hash();
	context.extend(location.hash.replace("#",'').parseQueryString(false, true));
	nav.state.empty();
	nav.set(context);
	nav.fireEvent('navigationChanged', context);
}

// hack: avoiding bind of a Request callback
var updateAssets = function(obj, bool){
	bool = false || Boolean(bool);
	assets.extend(obj);
	if (bool) {
		assets['xhrCount'] += 1;
		assets['xhrData_' + assets['xhrCount']] = assets['xhrData'];
		assets['xhr_last'] = assets['xhrData_' + assets['xhrCount']];
		assets.erase('xhrData')
	}
	
}

function create_diag(title, msg, options){
	options = options || {};
	Object.append(options, {
        title: title, buttons: [{title:'OK', click: 'close'}],
        content: new Element('p',{'html': msg })
	});
	new MUX.Dialog(options);
}

function checkLoginState(){
	return shortXHR({'loginCheck': 'yeah'})
}

// add a class of select to the current displayed menu
function setTopMenuSelect(){
	aas = $$('.nav')[0].getElements('a');
	aas.each(function(item){
		if (location.href.contains(item.hash)){
			item.getParent().addClass('active');
			item.setStyle('font-weight', 'bold');
		}
	});
}

function templating(s,d){
    for(var p in d)
        s=s.replace(new RegExp('{'+p+'}','g'),d[p]);return s;
}