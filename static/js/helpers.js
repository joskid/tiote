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


function serializeForm(context){
	var form_data = new Object();
	// input[type=text]
	$$('#' + context +' input[type=text]').each(function(item,key){
		form_data[item.get('name')] = item.get('value');
	});
	// hidden input
	$$('#'+context+' input[type=hidden]').each(function(item){
		form_data[item.name] = item.value;
	});
	// input[type=password]
	$$('#' + context +' input[type=password]').each(function(item, key){
		form_data[item.get('name')] = item.get('value');
	});
	// input[type=radio]
	$$('#' + context + ' input[type=radio]').each(function(item, key){
		if (item.checked)
			form_data[item.name] = item.value;
	});
	// input[type=checkbox]
	$$('#' + context + ' input[type=checkbox]').each(function(item,key){
		if ( ! form_data.has(item.name) ) 
			form_data[item.name] = [];
		if (item.checked) {
			ar = form_data[item.name];
			form_data[item.name][ar.length] = item.value;
		}
	});
	// select
	$$('#' + context + ' select').each(function(item,key){
		form_data[item.name] = item.value;
	})
	return form_data;
}

function generate_ajax_url(withAjaxKey,extra_data) {
	extra_data = extra_data || {};
	withAjaxKey = withAjaxKey || false;
	var n = new Hash( page_hash() );
	n.extend(extra_data);
	var request_url = 'ajax/?';
	n.each(function(item,key){
		if (key == 'section') {
			request_url += key + '=' + item;
		}
		else {
			request_url += '&' + key + '=' + item;
		}
	})
	if (withAjaxKey) request_url += '&ajaxKey=' + ajaxKey;
	return request_url
}


// table related functions
// uses moo
function create_data_table(thead_rows, tbody_rows, options) {
	var default_options = {
		'tbl': new Element('table', {
			'class': 'sql zebra-striped',
			'id': 'query_results',
			'summary': 'items returned from table'
		}),
		'insertion_point': 'sql-container'
	}
	options = Object.merge(default_options, options);
	// table height
	if (Object.keys(options).contains('height'))
		options['tbl'] = options['tbl'].setStyle('max-height', options['height']);
	// force markable
	if (options['with_checkboxes'])
		options['markable'] = true;
	else {
		
	}
	// checkboxes
	if (options['markable']) {
		thead_rows = [''].append(thead_rows);        
	}
	// create tbl
	data_table = new HtmlTable(options['tbl'], {
		properties: {},
		headers: thead_rows,
		zebra: true, 
		selectable:false,
		sortable:true
	});
	// add primary keys
	if (Object.keys(options).contains('keys'))
		data_table['keys'] = options['keys'];
	// create ids for the generated table
	for (var i = 0; i < tbody_rows.length; i++) {
		data_table.push(tbody_rows[i], {
			'id': 'row_'+ i
		});
	}
	
	if (options['markable']) {
		// add checkboxes to the table
		var trs = $(data_table).getElements('tr')
		var tdd = new Element('th', {
			'id': 'selector'
		});
		for (var i=1; i < trs.length; i++) {
			var td_select = new Element('td', {
				'class': 'selector'
			});
			var anc_check = new Element('input', {
				'class': 'checker',	
				'id': 'check_' + (i-1),	
				'type': 'checkbox'
			});
			anc_check.inject(td_select)
			td_select.inject(trs[i], 'top')
		}
	}
	
	if ( $('query_results') == null) {
		data_table.inject($(options['insertion_point']) );
	}
	else {
		data_table.replaces( $('query_results') );
		data_table.id = 'query_results';
	}
	
	if (options['markable']) {
		//reduce the width of the first tr element
		var sels = $$('table.sql tbody td.selector')
		sels.include($$('.sql thead tr th')[0].addClass('selector'));
		sels.each(function(item){
			item.setStyles({
				'max-width': '25px',
				'min-width': '25px',
				'width': '25px',
				'padding': '0px 0px 0px 4px'
			});
		})

		// select a tr element or a range of tr elements when the shift key is pressed
		selected_tr = ''
		$$('input.checker').addEvent('click', function(e) {
			last_selected_tr = selected_tr || '';
			var id =  e.target.getProperty('id');
			id = id.replace('check', 'row'); // id of equivalent <tr>
			selected_tr = $(id)
			if (e.shift && typeof(last_selected_tr == 'element')){
				var checker_status;
				if (data_table.isSelected(last_selected_tr)) {
					data_table.selectRange(last_selected_tr, selected_tr);
					checker_status = true;
				}else if (data_table.isSelected(selected_tr)) {
					data_table.deselectRange(last_selected_tr, selected_tr);
					checker_status = false;
				}
				// (un)check the checkboxes
				var start_i;var end_i;
				var sel_tr_index = parseInt(id.split('_')[1])
				var last_sel_tr_index = parseInt(last_selected_tr.id.split('_')[1])
				if (sel_tr_index > last_sel_tr_index) {
					start_i = last_sel_tr_index;
					end_i = sel_tr_index;
				} else {
					start_i = sel_tr_index;
					end_i = last_sel_tr_index;
				}
				for (var j = start_i; j < (end_i + 1); j++){
					$('check_'+String(j)).setProperty('checked', checker_status);
				}
			} else {
				data_table.toggleRow(e.target.getParent('tr'));
			}		

		});
	}
	return data_table;
}


// for selecting and deselecting all the trs of a table
// state = true : ticks all checkboxes and selects all rows
// state = false : unticks all checkboxes and deselects all rows
function set_all_tr_state(context, state) {
	state ? context.selectAll() : context.selectNone();
	for (var i=0; i < $(context).getElements('tbody tr').length; i++) {
		$('check_'+i).setProperty('checked', state);
	}
}

function generate_where_using_pk(wrk_table) {
	if (! Object.keys(wrk_table).contains('keys'))
		return '';
	else {
		// index of cols with primary key
		var col_titles = [];
		wrk_table['keys']['rows'].each(function(obj,obj_in){
			$(wrk_table).getElements('thead th').each(function(th, th_i){
				if (th.getElement('div').get('text').trim() == obj[0] )
					col_titles.include({'title':obj[0], 'index':th_i});
			});
		});
		// generate where stmt
		var where_stmt = '';
		if (wrk_table.getSelected().length > 0) {
			wrk_table.getSelected().each(function(row,row_in){
				var cols = row.getElements('td');
				col_titles.each(function(obj){
					where_stmt += ' ' + obj['title'] +'='+cols[obj['index']].get('text');
					where_stmt += (row_in == wrk_table.getSelected().length - 1) ? '' : ';';
				});
			});
		}
		return where_stmt.trim(); // empty string indeicateds no row was selected
	}
}

function generate_where(wrk_table) {
	var selected_rows = wrk_table.getSelected();
	var whereToEdit = '';
	if (! selected_rows) {
		return whereToEdit;
	}else {
		var th_divs = $(wrk_table).getElements('th div');
		var cols = [];
		th_divs.each(function(diva, diva_index){
			if (diva_index != 0) cols.push(diva.childNodes[1].nodeValue);
		})
		selected_rows.each(function(tiri,tiri_index){
			var where = '';
			tiri.getChildren('td[class!=selector]').each(function(tida,tida_index){
				if (cols[tida_index] != undefined) { // condition skips the last empty td
					if (! tida.hasChildNodes())
						where += ' ' + cols[tida_index] + '=' + '';
					else
						where += ' ' + cols[tida_index] + '=' + tida.childNodes[0].nodeValue +'';
					if (tida_index != tiri.getChildren('td[class!=selector]').length - 1 ) // last td before empty td
						where += ' AND';
				}
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

function redirectPage(context){
	location.hash = '#' + Object.toQueryString(context);
}

function reloadPage(){
	var context = new Hash();
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

function showDialog(title, msg, options){
	var op = {
		'offsetTop': 0.2 * screen.availHeight
		}
	if (options) op = Object.merge(op, options)
	var SM = new SimpleModal(op);
	SM.show({
		'title': title, 
		'contents': msg
	})
}


function checkLoginState(){
	return shortXHR({
		'loginCheck': 'yeah'
	})
}

// add a class of select to the current displayed menu
function setTopMenuSelect(){
	var aas = $$('.nav')[0].getElements('a');
	aas.each(function(item){
		if (location.href.contains(item.hash)){
			item.getParent().addClass('active');
			item.setStyle('font-weight', 'bold');
		}
	});
}


function getWindowWidth() {
	if (window.innerWidth)
		return window.innerWidth;
	else
		return document.documentElement.clientWidth;
}

function getWindowHeight() {
	if (window.innerHeight)
		return window.innerHeight;
	else
		return document.documentElement.clientHeight;
}

function tbl_pagination(total_count, limit, offset) {
	var pag_max = Math.floor(total_count / limit);
	var pag_lnks = new Elements();
	for ( i = 0; i < (pag_max + 1); i++) {
		var navObj = location.hash.parseQueryString(false, true);
		navObj['offset'] = String(i*limit);
		var request_url = location.protocol+'//'+location.host+location.pathname+Object.toQueryString(navObj);
		pag_lnks.include( new Element('a',{
			'href': request_url, 
			'class':'pag_lnk', 
			'text':(i+1)
			})
		);
	}
	var ancs = new Elements();
	var j = Math.floor(offset/limit);
	if ( pag_max > 0 ) {
		if (j == 0) {
			ancs.append( [ pag_lnks[0].addClass('active'),
				(pag_max > 2) ? pag_lnks[1] : pag_lnks[1].addClass('last'),
				(pag_max > 2) ? pag_lnks[2].addClass('last') : null, 
				pag_lnks[1].clone().set('text','Next').addClass('cntrl').removeClass('last'),
				pag_lnks[pag_max].clone().set('text', 'Last').addClass('cntrl')
				]);
				
		} else if (j == pag_max) {
			ancs.append( [ pag_lnks[0].clone().set('text','First').addClass('cntrl'), 
				pag_lnks[j-1].clone().set('text','Prev').addClass('cntrl last'),
				pag_lnks[j-1], pag_lnks[j].addClass('active') 
				]);
		} else {
			ancs.append( [ pag_lnks[0].clone().set('text','First').addClass('cntrl').removeClass('last'),
				pag_lnks[j-1].clone().set('text','Prev').addClass('cntrl last'),
				pag_lnks[j-1], pag_lnks[j].addClass('active'), pag_lnks[j+1].addClass('last'),
				pag_lnks[j+1].clone().set('text','Next').addClass('cntrl').removeClass('last'),
				pag_lnks[pag_max].clone().set('text', 'Last').addClass('cntrl').removeClass('last')
				] );
		}
	}
	
	return new Element('p', {'class':'paginatn pull-right'}).adopt(ancs,
		// span to display no of pages created
		new Element('span',{'style':'color:#888;padding-left:20px;',
			'text': (pag_max > 0) ? '[ '+(pag_max+1)+' pages ]' : '[ 1 page ]' 
		})
	);
}

var updateSelectNeedsValues = function(){
	console.log('updateSelectNeedsValues');
	$$('#tt_form .compact-form select').each(function(sel_item){
		if (sel_item.get('class').contains('needs:')) {
			// find definition statement
			var stmt = '';
			sel_item.get('class').split(' ').each(function(class_item){
				if (class_item.contains('needs') )
					stmt = class_item;
			});
			//
			var stmt_cond = stmt.split(':');
			sel_item.addEvent('change', function(e){
				if (stmt_cond[2].split('|').contains(e.target.value))
					e.target.getParent('table').getElements('.'+stmt_cond[1]+'-needed').removeClass('hidden');
				else
					e.target.getParent('table').getElements('.'+stmt_cond[1]+'-needed').addClass('hidden');
			});
		}
	});
}

function updateForeignKeyColumns(){
	console.log('updateForeingKeyColumns');
	var tbl_nd_cols = JSON.decode($('table_with_columns').get('text'));
	// events
	$$('#tt_form .compact-form select').each(function(sel_item){
		if (sel_item.id.contains('references') ) 
			sel_item.addEvent('change', function(e){
				var template = "<option value='{column}'>{column}</option>";
				var childEls = ''
				if (e.target.value != '')
					tbl_nd_cols[e.target.value].each(function(column){
						childEls += template.substitute({'column': column})
					});
				$('id_column_' + sel_item.id.split('_')[2]).set('html', '');
				$('id_column_' + sel_item.id.split('_')[2]).set('html', childEls );
			});
	});
}


function disable_unimplemented_links(){
	var implemented = {
		'home': ['home', 'users'],
		'database': ['overview'],
		'table': ['browse', 'structure']
	}
	var section = page_hash()['section']
	$$('.nav a').each(function(nav_link){
		if ( ! implemented[section].contains( nav_link.get('html').toLowerCase() ) ){
			new Element('span', {
				'style': 'display: block;float: none;line-height: 19px;padding: 10px 10px 11px;text-decoration: none;',
				'text': nav_link.get('html'),
				'alt': 'feature not yet implemented',
				'help': 'feature not yet implemented'
				}
			).replaces(nav_link)
		}
	});	
}

function page_hash(){
	return location.hash.replace('#','').parseQueryString(false, true);
}