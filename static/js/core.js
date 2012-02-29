var pg; var nav;
var pageLoadSpinner;
var assets = new Hash({'xhrCount': 0});

window.addEvent('domready', function() {
    // spinners 
    pageLoadSpinner = new Spinner(document.body, {'message': 'loading page...'});
    
	nav = new Navigation();
    
	nav.addEvent('navigationChanged', function(navObject){
		// do page initialization here
        var loginState = checkLoginState();
//		console.log('navigationChanged event fired');
		if (loginState) {
			if (Cookie.read('TT_NEXT')){
				navObject = Cookie.read('TT_NEXT').parseQueryString(false, true);
				location.hash = '#' + Cookie.read('TT_NEXT');
				Cookie.dispose('TT_NEXT');
			}
		} else {
			Cookie.write('TT_NEXT', new Hash(navObject).toQueryString());
			navObject = new Hash({'section': 'begin', 'view': 'login'});
            // funny redirect
            location.href = location.protocol + '//'+ location.host + location.pathname + 'login/'
		}
		pg = new Page(navObject);
		setTopMenuSelect();
	});
    
	if (! location.pathname.contains('login/') ) {
        if (location.hash) {reloadPage();} 
        else {nav.set({'section': 'home', 'view': 'home'});}
    }
	
});

function clearPage(clear_sidebar){
	clear_sidebar = clear_sidebar || false; // init
	if (clear_sidebar && $('sidebar').getChildren()) {
		$('sidebar').getChildren().destroy();
	}
	$('tt-content').getChildren().destroy();
}

// A single tiote page
function Page(obj){
//	console.log('new Page() object created');
	this.options = new Hash();
	this.updateOptions({'navObj': obj, 'hash': location.hash});
	this.setTitle();
	this.generateTopMenu(obj);
	this.tbls = [];
	disable_unimplemented_links();
	self = this; 
	// unset all window resize events
	window.removeEvents(['resize']);
	clearPage();
	this.generateView(obj);
}

	
Page.prototype.startPageLoad =  function() {
    console.log('startPageLoad()!')
    pageLoadSpinner.show(true);
}

Page.prototype.endPageLoad =  function() {
//        if (pageLoadSpinner.active)
        pageLoadSpinner.hide();
}

Page.prototype.setTitle = function(new_title){
	new_title = new_title || false;
	if (! new_title) {
		var title = 'tiote';
		var r = location.hash.replace('#','').parseQueryString();
		Object.each(r, function(item, key){
			if (key == 'view' && r[key] == r['section']) {
			} else {
				if (key == 'view' || key =='section') { /* skip */ } 
				else {title += ' / ' + item;}
			}
		});
		title += ' / ' + r['view'];
	} else {
		title = new_title;
	}
	document.title = title
	this.updateOptions({'title': title});
}

Page.prototype.generateTopMenu = function(data){
	var links = new Hash();
	l = ['query', 'import', 'export', 'insert', 'structure', 'overview', 'browse', 'update', 'search', 'home'];
	l.append(['login', 'help', 'faq', 'users',]);
	l.each(function(item){
		links[item] = new Element('a', {'text': item});
	});
	
	var order = [];var prefix_str;var suffix;
	if (data['section'] == 'begin') {
		order = ['login', 'help', 'faq'];
		prefix_str = '#section=begin';
	}else if (data['section'] == 'home') {
		order = ['home', ,'users','query', 'import', 'export'];
		prefix_str = '#section=home';
	}else if (data['section'] == 'database') {
		order = ['overview', 'query','import','export'];
		prefix_str = '#section=database';
		suffix = ['&database=']
	}else if (data['section'] == 'table') {
		order = ['browse', 'structure', 'insert', 'search', 'query', 'import', 'export'];
		prefix_str = '#section=table';
		suffix = ['&database=','&table='];
	}
	
	var aggregate_links = new Elements();
	order.each(function(item, key){
		var elmt = links[item];
		elmt.href = prefix_str + '&view=' + elmt.text;
        if (data['section'] == 'database' || data['section'] == 'table'){
            elmt.href += suffix[0] + data['database'];
            if (data['schema'])
                elmt.href += '&schema=' + data['schema'];
        }
        if (data['section'] == 'table')
            elmt.href += suffix[1] + data['table'];
		// todo: add suffix_str eg &table=weed
		elmt.text = elmt.text.capitalize();
		var ela = new Element('li',{});
		ela.adopt(elmt);
		aggregate_links.include(ela);
	});
	var nava = new Element('ul',{'class':'nav'}); 
	if ($$('div.topbar ul.nav'))	$$('div.topbar ul.nav')[0].destroy();
	aggregate_links.inject(nava);
	$$('.topbar .container-fluid')[0].adopt(nava);
}

Page.prototype.generateSidebar = function(data) {
	// xhr request for table list
    var x = new XHR({'query':'sidebar', 'type':'representation',
		'section': this.options.navObj.section,
        'schema': this.options.navObj.schema, 
        'database': this.options.navObj.database,
        'table': this.options.navObj.table,
        'offset': this.options.navObj.offset,
        'method': 'get',
        'onSuccess': function(text,xml){
			// if there is already sidebar data clear it
			if ($('sidebar').getChildren())
				$('sidebar').getChildren().destroy();
			$('sidebar').set('html', text);
			window.addEvent('resize', function(){
				$('sidebar').setStyle('height', getHeight() - 40);
			});
			$('sidebar').setStyle('height', getHeight() - 40);
			// handle events
			if ($('db_select')) {
				$('db_select').addEvent('change', function(e){
					if (e.target.value != page_hash()['database']) {
						var context = {'section':'database','view':'overview',
							'database': e.target.value
						}
						if (Object.keys(page_hash()).contains('schema'))
							context['schema'] = 'public';
						redirectPage(context);
					}
				});
			}
			if ($('schema_select')) {
				$('schema_select').addEvent('change', function(e){
					if (e.target.value != page_hash()['schema']) {
						var context = {'section':'database','view':'overview',
							'database': page_hash()['database'], 'schema': e.target.value
						}
						redirectPage(context);
					}
				});
			}
		}
	}).send();
	
}


Page.prototype.updateOptions = function(obj) {
	this.options.extend(obj)
}


Page.prototype.generateView = function(data){
    var self = this;
	var x = new XHR(Object.merge({'method':'get',
        'onSuccess': function(text,xml){
            var viewData = {'text' : text,'xml' : xml};
            if (!data['section']) {
                nav.state.empty()
                nav.set({'section': 'home','view': 'home'});
            } else {
				$('tt-content').set('html', viewData['text']);
				self.completeTableView();
				self.completeTableOptions();
				if (data['section'] == 'home') {
					// further individual page processing
					if ( data['view'] == 'users') {
						self.userView();
					} else {
//						self.completeForm();
					}
				} else if (data['section'] == 'database'){
				
				} else if (data['section'] == 'table'){
				
				}
				self.generateSidebar();
			}
            runXHRJavascript();
        }
    },data)
    ).send()
}


Page.prototype.userView = function(){
	console.log('userView() called!');
	// xhr request users table and load it
	var h = getWindowHeight() * .45;
	this.loadTable('user_rpr','representation',
		{'height': h, 'with_checkboxes':true},{});
	window.addEvent('resize', function(){
		h = getWindowHeight() * .45;
		$(this.data_table).setStyle('height', 'auto');
		$(this.data_table).setStyle('max-height', h);
	});
	this.loadTableOptions('user')
	// hide some elmts
	var sbls_1 = [];var sbls_2 = [];
	var p1 = $$('.hide_1').getParent().getParent().getParent().getParent().getParent();
	p1.each(function(item,key){
		sbls_1.include(item.getSiblings()[0]);
	});
	var p2 = $$('.hide_2').getParent().getParent().getParent().getParent().getParent();
	p2.each(function(item,key){
		sbls_2.include(item.getSiblings()[0]);
		sbls_2.include(item.getSiblings()[1]);
	});
	hideAll(sbls_1);hideAll(sbls_2);
	$$('.addevnt').addEvent('change', function(e){
		if (e.target.id == 'id_access_0') {
			hideAll(sbls_1);
		} else if( e.target.id == 'id_privileges_0') {
			hideAll(sbls_2);
		}else if (e.target.id == 'id_access_1') {
			showAll(sbls_1);
		} else if (e.target.id == 'id_privileges_1'){
			showAll(sbls_2);
		}
	})
	
	this.completeForm();
}


Page.prototype.completeTableView = function() {
	var self = this;
	if ($$('table.sql') != null ) {
		$$('table.sql').each(function(tbl, tbl_in){
			self.tbls.include(new HtmlTable($(tbl)));
			make_checkable(self.tbls[tbl_in]);
			// attach the variables passed down as javascript objects to the 
			// table object
			self.tbls[tbl_in]['vars'] = {}; // container
			if ($(self.tbls[tbl_in]).get('data')) {
				var data = {}
				$(self.tbls[tbl_in]).get('data').split(';').each(function(d){
					var ar = d.split(':');
					data[ar[0]] = ar[1];
				});
				self.tbls[tbl_in]['vars']['data'] = data; // schema: [key: value]
			}
			if ($(self.tbls[tbl_in]).get('keys')) {
				var data = []; // data[[1,2,3],...] indexes 1: name of column,
							   // 2 : index type
						       // 3 : column position in tr
				$(self.tbls[tbl_in]).get('keys').split(';').each(function(d){
					var ar = d.split(':');
					if (ar[0] != "") data.include(ar);
				});
				// loop through the ths to see which corresponds to the keys
				$(self.tbls[tbl_in]).getElements('th').each(function(th, th_in){
					for (var i = 0; i < data.length; i++) {
						if ($(th).get('text') == data[i][0] )
							data[i].include(th_in);
					}
				});
				
				self.tbls[tbl_in]['vars']['keys'] = data; // schema: [column, key_type, column index]
			}
			
			// make a.display_row(s) clickable
			$(tbl).getElements('a.display_row').each(function(al, al_in){
				if ($(tbl).get('keys' != null)) {	// functionality requires keys
					al.addEvent('click', function(e) {	// attach click event
						var where_stmt = generate_where(self.tbls[tbl_in], al_in);
						// make xhr request
						var x = new XHR(Object.merge({
							'method': 'post', 'query': 'get_row','type':'representation',
							'showLoader': false,
							onSuccess : function(text, xml) {
								showDialog("Entry", text);
							}, data: where_stmt
						}, page_hash())
						).send();
					});
				}
			});
		});
		
	}
}


Page.prototype.completeTableOptions = function() {
	// .table-options processing : row selection
	if ($$('.table-options') != null) {
		$$('.table-options').each(function(tbl_opt, tbl_opt_index){
			// enable selection of rows
			$(tbl_opt).getElements('a.selecters').each(function(a_sel){
				a_sel.addEvent('click', function() {
					a_sel.get('class').split(' ').each(function(cl){
						if (cl.contains('select_')) {
							var option = cl.replace('select_', '');
							set_all_tr_state(self.tbls[tbl_opt_index], (option == 'all') ? true : false);
						}
					});
				});
			});
			
			// table's needing pagination
			if (Object.keys(self.tbls[tbl_opt_index]['vars']).contains('data')) {
				$(tbl_opt).adopt(tbl_pagination(
					self.tbls[tbl_opt_index]['vars']['data']['total_count'],
					self.tbls[tbl_opt_index]['vars']['data']['limit'], 
					self.tbls[tbl_opt_index]['vars']['data']['offset']));
			}
		});
	}
	
}



var XHR = new Class({

	Extends: Request,
	
	initialize: function(options) {
		options.headers = {
			'X-CSRFToken': Cookie.read('csrftoken')
		};
		options.chain = 'link';
				
		if (!options.url)
			options.url = 'ajax/?';
		if (options.loginCheck)
			options.url += 'check=login';	
		else if (options.commonQuery)
			options.url += 'commonQuery=' + options.commonQuery;
        else if (options.query){
            options.url += 'query=' + options.query;
            if (options.type)
                options.url += '&type=' + options.type;
        }
		// 
		if (options.url.substr(-1) != "?") options.url += "&";
		//
		if (options.section) {
			
			options.url += 'section=' + options.section;
		}
		if (options.view)
			options.url += '&view=' + options.view;
		if (options.database)
			options.url += '&database=' + options.database
		if (options.schema)
			options.url += '&schema=' + options.schema
		if (options.table)
			options.url += '&table=' + options.table
		if (options.table)
			options.url += '&table=' + options.table;
		if (options.offset)
			options.url += '&offset=' + options.offset;
		// append ajax validation key
		options.url += '&ajaxKey=' + ajaxKey;
		this.parent(options);
		
		if (options && options.showLoader != false) {
			var spinnerTarget = (options.spinnerTarget) ? options.spinnerTarget: document.body;
			var ajaxSpinner = new Spinner(spinnerTarget, {'message': 'loading data...'});
			show('header-load');
            ajaxSpinner.show(true);
			
			this.addEvent("onSuccess", function() {
//				hide('header-load');
//				ajaxSpinner.hide();
			});
			
			this.addEvent('onComplete', function(xhr){
				hide('header-load');
				ajaxSpinner.hide();
				ajaxSpinner.destroy();
			});
			
			
			this.addEvent("onFailure", function(xhr) {
				var msg = 'An unexpected error was encountered. Please reload the page and try again.';
				if (xhr.status == 500 && xhr.statusText == "UNKNOWN STATUS CODE") msg = xhr.response;
//				hide('header-load');
//                ajaxSpinner.hide();
                if (msg == 'invalid ajax request!') 
                    location.reload()
                else
                    showDialog('Error!', msg, {'draggable':false,'overlayClick':false})
			});
			
		}
	},
	
	// redefined to avoid auto script execution
	success: function(text, xml) {
		assets.xhrCount += 1;
		assets['xhrData_'+ assets.xhrCount] = {'text':text,'xml':xml};
		this.onSuccess(text, xml);
	}
	
});


function shortXHR(data){
	var op = new Hash(data)
	op.extend({'method': 'get', 'async': false, 'timeout': 10000, 'showLoader':false})
	var x = new XHR(op).send();
	
	if (x.isSuccess() ) {
		return x.response.text;
	} else {
		return '!! request failed !!';
	}
}


function show(a) {
	$(a).style.display = 'block';
}

function hideAll(a){
	a.each(function(item, key){
		$(item).style.display = 'none'
	});
}
function showAll(a){
	a.each(function(item, key){
		$(item).style.display = ''
	});
}
function toggleDisplayEls(a, force){
	a.each(function(item, key){
		if ( $(item).style.display == 'none' ) show(item);
		else hide(item);
	});
}
function hide(a) {
	$(a).style.display = 'none';
}


