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
    })
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
function create_data_table(thead_rows, tbody_rows, insertion_point, markable, tbl) {
	var tbl = new Element('table', {
		'class': 'sql zebra-striped',
		'id': 'query_results',
		'summary': 'items returned from table'
	}) || tbl;
    
    markable = markable || true;
    
    if (markable) {
        var th_rows = ['']
        th_rows.append(thead_rows)
        thead_rows = th_rows;        
    }
	
	data_table = new HtmlTable(tbl, {
		properties: {},
		headers: thead_rows,
		zebra: true, 
		selectable:false,
		sortable:true
//        rowFocus: function(e){
//            console.log(e.target)
//        },
//        rowUnFocus: function(e){
//            console.log(e.target)
//        }
	});
	
	// hack: create ids for the generated table
    // but should slow down the table creation
	for (var i = 0; i < tbody_rows.length; i++) {
		data_table.push(tbody_rows[i], {
			'id': 'row_'+ i
		});
	}
	
    if (markable) {
        // add checkboxes to the table
        var trs = $(data_table).getElements('tr')
        var tdd = new Element('th', {'id': 'selector'});
        for (var i=1; i < trs.length; i++) {
            var td_select = new Element('td', {'class': 'selector'});
            var anc_check = new Element('input', {'class': 'checker',	'id': 'check_' + (i-1),	'type': 'checkbox'	});
            anc_check.inject(td_select)
            td_select.inject(trs[i], 'top')
        }
    }
	
    if ( $('query_results') == null) { data_table.inject($(insertion_point) ); }
    else { data_table.replaces( $('query_results') ); data_table.id = 'query_results'; }
	
	if (markable) {
        //reduce the width of the first tr element
        $$('.sql thead tr th')[0].addClass('selector').setStyles({
            'max-width': '25px',
            'min-width': '25px',
            'width': '25px',
            'padding': '0px 0px 0px 4px'
        });

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
                var start_i; var end_i;
                var sel_tr_index = parseInt(id.split('_')[1])
                var last_sel_tr_index = parseInt(last_selected_tr.id.split('_')[1])
                if (sel_tr_index > last_sel_tr_index) {
                    start_i = last_sel_tr_index; end_i = sel_tr_index;
                } else {
                    start_i = sel_tr_index; end_i = last_sel_tr_index;
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


function generate_where(wrk_table, e) {
	var selected_rows = wrk_table.getSelected();
    var whereToEdit = '';
    if (! selected_rows) {
        return whereToEdit;
    }else {
        var th_divs = $(wrk_table).getElements('th div'); var cols = [];
        th_divs.each(function(diva, diva_index){
            if (diva_index != 0) cols.push(diva.childNodes[1].nodeValue);
        })
        selected_rows.each(function(tiri,tiri_index){
            var where = '';
            tiri.getChildren('td[class!=selector]').each(function(tida,tida_index){
                if (! tida.hasChildNodes())
                    where += ' ' + cols[tida_index] + '=' + '';
                else
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

function showDialog(title, msg, options){
    op = {'offsetTop': 0.2 * screen.availHeight}
	if (options) op = Object.merge(op, options)
	var SM = new SimpleModal(op);
    SM.show({
        'title': title, 'contents': msg
    })
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

function create_pagination(total, limit, present_index){
    // total is the number of rows,
    // limit is the number of rows that can be displayed
    var pag_no = Math.ceil( total / limit);
    present_index = present_index || 1;
    var lnks = new Elements();
    var li_prv = new Element('li',{'class':'prev'}).adopt(new Element('a',
        {'text':'&larr; Previous','href':'#'})
    );
    var li_nxt = new Element('li',{'class':'next'}).adopt(new Element('a',
        {'text':'Next &rarr;','href':'#'})
    );
    for (var i = 1; i <= pag_no; i++) {
        var eli = new Element('li').adopt(new Element('a',{'text':i,'href':'#'}));
        if (present_index == i)
            eli.addClass('active');
        lnks.include(eli);
    }
    if (present_index == pag_no)
        li_nxt.addClass('disabled');
    else if (present_index == 1)
        li_prv.addClass('disabled');
    var div_pag = new Element('div',{'class':'pagination'}).adopt(
        new Element('ul').adopt(li_prv, lnks, li_nxt)
    )
    return div_pag
}
