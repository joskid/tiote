var pg, nav; // global variables
// catalog of all abbreviations in use
var _abbrev = {
	'sctn': 'section',
	'tbl': 'table',
	'v': 'view',
	'schm': 'schema',
	'idxs': 'indexes',
	'cols': 'columns'
};

function navigationChangedListener(navObject, oldNavObject){
	// redirect to the next page as gotten from the location hash
	if (Cookie.read('TT_NEXT')){
		navObject = Cookie.read('TT_NEXT').parseQueryString(false, true);
		location.hash = '#' + Cookie.read('TT_NEXT');
		Cookie.dispose('TT_NEXT');
	}
	// create a new Page object which begins page rendering
	pg = new Page(navObject, oldNavObject);
}

window.addEvent('domready', function() {
	preloadImages();
	nav = new Navigation();	
	nav.addEvent('navigationChanged', navigationChangedListener);
	
	// if the location string contains hash tags
	if (location.hash) {
		// begin page rendering
		var navObj = page_hash();
		pg = new Page(navObj, null);
	}
	// there are no hashes set a default
	else
		nav.set({'sctn': 'home', 'v': 'home'});
	// higlight the element (.navbar a) that corresponds to the currently displayed view

});


/*
 * make UI images accessible by the DOM before they are required
 * 
 * notice: to make sure this list is accurate and doesn't generate funny 404 errors: 
 * to update the images collection below use a list generated from reading the contents
 * of the directory containing the images (python was used here)
 */
function preloadImages() {
	var images = ['schemas.png', 'sequences.png', 'sortdesc.gif', 'table.png', 'sequence.png',
		'tables.png', 'databases.png', 'views.png', 'spinner.gif', 'database.png', 'goto.png',
		'schema.png', 'sortasc.gif'
	];
	
	var pre;
	for (var i=0; i<images.length; i++) {
		pre = new Image();
		pre.src = _staticUrl +"img/" + images[i];
	}	
}


// A single tiote page
function Page(obj, oldObj){
	this.options = new Hash({navObj: obj, oldNavObj: oldObj});
	this.tbls = [];
	// unset all window resize events
	window.removeEvents(['resize']);
	this.clearPage();
	this.loadPage(true);
}

Page.prototype.clearPage = function(clr_sidebar) {
	clr_sidebar = clr_sidebar || false; // init
	if (clr_sidebar && $('sidebar').getChildren()) {
		$('sidebar').getChildren().destroy();
	}
	$('tt-content').getChildren().destroy();
}

Page.prototype.loadPage = function(clr_sidebar) {
	clr_sidebar = clr_sidebar || false;
	var obj = this.options.navObj, oldObj = this.options.oldNavObj;
	this.setTitle();
	this.generateTopMenu(obj);
	disable_unimplemented_links();
	this.generateView(obj, oldObj); 
	this.generateSidebar(clr_sidebar);
	highlightActiveMenu();
}


/*
 * Generates the title of the current page from location.hash
 * It follows the following format
 *
 *		tiote / view [ / subview ] :  / database [ / schm  ]/ table [/ subv] [/ page ]
 */
Page.prototype.setTitle = function(new_title){
	new_title = new_title || false;
	if (! new_title) {
		var title = 'tiote';
		var r = location.hash.replace('#','').parseQueryString();
		title += ' / ' + r['v'];
		// append spilter to the title of the page
		//- functions(more like navigation depth) : objects ( db or tbl or schm we are working on)
		title += " :  ";
		['db','schm','tbl'].each(function(or_item){
			if (Object.keys(r).contains(or_item)) title += ' / ' + r[or_item];
		});
		if (Object.keys(r).contains('offset')) title += ' / page ' + (r['offset'] / 100 + 1);
		if (Object.keys(r).contains('subv')) title += ' / ' + _abbrev[ r['subv'] ];
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
	if (data['sctn'] == 'begin') {
		order = ['login', 'help', 'faq'];
		prefix_str = '#sctn=begin';
	} else if (data['sctn'] == 'home') {
		order = ['home', ,'users','query', 'import', 'export'];
		prefix_str = '#sctn=home';
	} else if (data['sctn'] == 'db') {
		order = ['overview', 'query','import','export'];
		prefix_str = '#sctn=db';
		suffix = ['&db=']
	} else if (data['sctn'] == 'tbl') {
		order = ['browse', 'structure', 'insert', 'query', 'import', 'export'];
		prefix_str = '#sctn=tbl';
		suffix = ['&db=','&tbl='];
	}
	
	var aggregate_links = new Elements();
	order.each(function(item, key){
		var elmt = links[item];
		elmt.href = prefix_str + '&v=' + elmt.text;
        if (data['sctn'] == 'db' || data['sctn'] == 'tbl'){
            elmt.href += suffix[0] + data['db'];
            if (data['schm'])
                elmt.href += '&schm=' + data['schm'];
        }
        if (data['sctn'] == 'tbl')
            elmt.href += suffix[1] + data['tbl'];
		// todo: add suffix_str eg &tbl=weed
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

Page.prototype.generateView = function(navObj, oldNavObj){
//	console.log(navObj), console.log(oldNavObj);
	new XHR({
		url: generate_ajax_url(), 
		method: 'GET',
		onSuccess: function(text, xml) {
			if (Cookie.read('TT_NEXT')){
				// don't understand why but this cookie is usually appended with 
				// - quotes at the beginning and at the end (not its representation)
				var o = Cookie.read('TT_NEXT').parseQueryString(true, true);
				var o2 = {};
				Object.keys(o).each(function(k){
					o2[ k.replace("\"", "") ] = o[k].replace("\"",'');
				});
				Cookie.dispose('TT_NEXT');
				redirectPage(o2);
				return;
			}
			$('tt-content').set('html', text);
			if (navObj['sctn']=='tbl' && navObj['v'] =='browse') {
				pg.jsifyTable(true);
				pg.browseView();
			} else {pg.jsifyTable(false);}
			pg.addTableOpts();
			// attach events to forms
			if ($$('.tt_form')) {pg.completeForm();}
			runXHRJavascript();
		}
	}).send();
}

// decide if the sidebar needs to be refreshed
function canUpdateSidebar(navObj, oldNavObj) {
	var clear_sidebar = false; // default action is not to clear the sidebar
	if (Cookie.read('TT_UPDATE_SIDEBAR')){
		clear_sidebar = true;
		Cookie.dispose('TT_UPDATE_SIDEBAR');
	} else {
		// other necessary conditions
		// if the #sidebar element is empty reload the sidebar
		if ($('sidebar') && $('sidebar').getChildren().length) {
			if (oldNavObj == undefined || oldNavObj == null || oldNavObj == "")
				return clear_sidebar; // short circuit the function
			
		// if there is no percievable change in the location.hash of the page
		// - dont clear sidebar
		if (oldNavObj['sctn'] == navObj['sctn'] && oldNavObj['tbl'] == navObj['tbl']
			&& oldNavObj['db'] == navObj['db']
		) {
			// check if the hash obj contains a schema key
			if (Object.keys(oldNavObj).contains('schm') && Object.keys(navObj).contains('schm')) {
				// postgresql dialect
				if (oldNavObj['schm'] == navObj['schm']) clear_sidebar = false;
			} else {
				// mysql dialect
				clear_sidebar = false;
			}
		}
		}
	}
	return clear_sidebar;
}

Page.prototype.generateSidebar = function(clear_sidebar) {
	// autosize the sidebar to the available height after below the #topbar
	var resize_sidebar = function() {
		if ($('sidebar').getScrollSize().y > (getHeight() - 50) || 
		$('sidebar').getSize().y < (getHeight() - 50)) {
			$('sidebar').setStyle('height', getHeight() - 50);
		}
	};
	
	// decide if there should be a sidebar update
	// if clear_sidebar is already true then there must be a sidebar update
	// - if it isn't decide from the context of the current view if there should be
	clear_sidebar = clear_sidebar || false;
	var navObj = this.options.navObj, oldNavObj = this.options.oldNavObj;
	if (!clear_sidebar)
		clear_sidebar = canUpdateSidebar(navObj, oldNavObj);
	
	if (clear_sidebar) {
		var x = new XHR({
			url : generate_ajax_url() + '&q=sidebar&type=repr',
			method: 'get',
			onSuccess: function(text,xml){
				// if the sidebar contains elements destroy them
				if ($('sidebar').getChildren())
					$('sidebar').getChildren().destroy();
				$('sidebar').set('html', text);
				window.addEvent('resize', resize_sidebar);
				window.fireEvent('resize'); // fire immediately to call resize handler
				// handle events
				if ($('db_select')) {
					$('db_select').addEvent('change', function(e){
						if (e.target.value != page_hash()['db']) {
							var context = {'sctn':'db','v':'overview', 'db': e.target.value};
							if (Object.keys(page_hash()).contains('schm'))
								context['schm'] = 'public';
							redirectPage(context);
						}
					});
				}
				if ($('schema_select')) {
					$('schema_select').addEvent('change', function(e){
						if (e.target.value != page_hash()['schm']) {
							var context = {'sctn':'db','v':'overview',
								'db': page_hash()['db'], 'schm': e.target.value
							}
							redirectPage(context);
						}
					});
				}
				// highlights the link corresponding to the current view in the sidebar
				//  in cases where the sidebar wasn't refreshed
				if ($('sidebar').getChildren('ul a')) {
					$$('#sidebar ul a').each(function(lnk){
						lnk.addEvent('click', function(e){
							$$('#sidebar ul li').removeClass('active');
							lnk.getParent().addClass('active');
						});
					});
				}
				}
		}).send();
	}
	window.addEvent('resize', resize_sidebar);
	window.fireEvent('resize'); // fire immediately to call resize handler
}


Page.prototype.jsifyTable = function(syncHeightWithWindow) {
	// display
	if ($$('.jsifyTable').length) {
		$$('.jsifyTable').each(function(cont, cont_in) {
//			console.log('cont #' + cont_in);
			// auto update height
			syncHeightWithWindow = syncHeightWithWindow || false;
			if (syncHeightWithWindow) {
				window.addEvent('resize', function() {
					if ($E('.tbl-body table', cont) != null) {
						var t = $E('.tbl-body table', cont);
						if (t.getScrollSize().y > (getHeight() - 110)) {
							t.setStyle('height', (getHeight() - 110));
						} else {
							t.setStyle('height', null);
						}
					}
				});
				window.fireEvent('resize');
			}
			if (cont.getElements('.tbl-body table tr').length) {
				// same size body and header
				var tds = cont.getElements('.tbl-body table tr')[0].getElements('td');
				var ths = cont.getElements('.tbl-header table tr')[0].getElements('td');
	
				for (var i = 0; i < ths.length - 1; ++i) {
					var width;
					if (ths[i].getDimensions().x > tds[i].getDimensions().x) {
						width = ths[i].getDimensions().x + 10;
						tds[i].setStyles({'min-width':width, 'width': width});
						width = tds[i].getDimensions().x - 1; // -1 for border
						ths[i].setStyles({'min-width': width, 'width': width});
					} else {
						width = tds[i].getDimensions().x - 1; // -1 for border
						ths[i].setStyles({'min-width': width, 'width': width});
					}
				}
				tds = null, ths = null;
			}

			if (cont.getElement('.tbl-body table') != undefined
				&& cont.getElement('.tbl-header table') != undefined) {
				// variables needed
				var tblhead_tbl = cont.getElement('.tbl-header table');
				var tblbody_tbl = cont.getElement('.tbl-body table');
				// sync scrolling 
				tblbody_tbl.addEvent('scroll', function(e){
					var scrl = tblbody_tbl.getScroll();
					cont.getElement('.tbl-header table').scrollTo(scrl.x, scrl.y);
				});
				// add the width of scrollbar to min-width property of ".tbl-header td.last-td"
				var w = tblbody_tbl.getScrollSize().x - tblhead_tbl.getScrollSize().x;
				w = w + 25 + 7;
				tblhead_tbl.getElement('td.last-td').setStyle('min-width', w);	
			}
		});
	}
	// behaviour
	if ($$('table.sql') != null ) {
		$$('table.sql').each(function(tbl, tbl_in){
			pg.tbls.include(new HtmlTable($(tbl)));
			make_checkable(pg.tbls[tbl_in]);
			// attach the variables passed down as javascript objects to the 
			// table object
			pg.tbls[tbl_in]['vars'] = {}; var data;// containers
			if ($(pg.tbls[tbl_in]).get('data')) {
				data = {}
				$(pg.tbls[tbl_in]).get('data').split(';').each(function(d){
					var ar = d.split(':');
					data[ar[0]] = ar[1];
				});
				pg.tbls[tbl_in]['vars']['data'] = data; // schema: [key: value]
			}
			if ($(pg.tbls[tbl_in]).get('keys')) {
				data = []; // data[[1,2,3],...] indexes 1: name of column,
							   // 2 : index type
						       // 3 : column position in tr
				$(pg.tbls[tbl_in]).get('keys').split(';').each(function(d){
					var ar = d.split(':');
					if (ar[0] != "") data.include(ar);
				});
				// loop through the tds int .tbl-header to see which corresponds to the keys
				$$('.tbl-header table')[tbl_in].getElements('td').each(function(th, th_in){
					for (var i = 0; i < data.length; i++) {
						if ($(th).get('text') == data[i][0] )
							data[i].include(th_in);
					}
				});
				
				pg.tbls[tbl_in]['vars']['keys'] = data; // schema: [column, key_type, column index]
			}
			
			// handle a.display_row(s) click events
			$(tbl).getElements('a.display_row').each(function(al, al_in){
				if ($(tbl).get('keys' != null)) {	// functionality requires keys
					// attach click event
					al.addEvent('click', function(e) {
						var where_stmt = generate_where(pg.tbls[tbl_in], al_in, true);
						// make xhr request
						var x = new XHR({
							url: generate_ajax_url() + '&q=get_row&type=fn',
							spinnerTarget: tbl,
							onSuccess : function(text, xml) {
								showDialog("Entry", text, {
									offsetTop: null, width: 475, hideFooter: true,
									overlayOpacity: 0, overlayClick: false
								});
							}
						}).post(where_stmt);
					});
				}
			});
		});
		
	}
}


Page.prototype.addTableOpts = function() {
	// .table-options processing : row selection
	if ($$('.table-options') != null && Object.keys(pg.tbls).length) {
		$$('.table-options').each(function(tbl_opt, opt_in){
			htm_tbl = pg.tbls[opt_in]; // short and understandable alias
			// enable selection of rows
			$(tbl_opt).getElements('a.selector').each(function(a_sel) {
				a_sel.addEvent('click', function() {
					// loop through all the classes to find the "select_" class
					a_sel.get('class').split(' ').each(function(cl){
						if (cl.contains('select_')) {
							var option = cl.replace('select_', '').toLowerCase();
							set_all_tr_state(htm_tbl, (option == 'all') ? true : false);
						}
					});
				});
			});
			
			// table's needing pagination
			if (Object.keys(htm_tbl['vars']).contains('data')) {
				var pg_htm = tbl_pagination( // pagination html
					htm_tbl['vars']['data']['total_count'],
					htm_tbl['vars']['data']['limit'], 
					htm_tbl['vars']['data']['offset']
				);
				$(tbl_opt).getElement('p').adopt(pg_htm);
			}
			
			
			// links that do something (edit, delete ...)
			$ES('a.doer', tbl_opt).each(function(doer){
				doer.addEvent('click', function(e) {
					if (doer.hasClass('action_refresh'))
						// action to be performed is a page refresh
						pg.loadPage(false)
					else 
						do_action(htm_tbl, e);
				});

			});
			
			// disable or enable if no row is selected or rows are selected respectively.
			var needy_doer_options = function(tr, tr_all) {
				if (tr_all.length) {
					$$('a.needy_doer').setStyles({
						'color': '#0069D6',
						'cursor': 'pointer'
					});
				} else {
					$$('a.needy_doer').setStyles({
						'color': '#888', 
						'cursor': 'default'
					});
				}
			}
			
			htm_tbl.addEvent('rowFocus', needy_doer_options).addEvent('rowUnfocus', needy_doer_options);
			
		});
	}
	
}

function edit_page(where_stmt) {
//	console.log('row have been selected for edition');
	// 1. clear page
	pg.clearPage(false);
	// 2. request edit page
	var navObj = page_hash(); navObj['subv'] = 'edit';
	new XHR({
		url: 'ajax/?' + Object.toQueryString(navObj), spinTarget: $('tt_content'),
		onSuccess: function(text, xml) {
			$('tt-content').set('html', text);
			pg.completeForm();
		}
	}).post({where_stmt: where_stmt});

	// update location hash
	nav.set('subv', 'edit', true);

	// 3. add edit handle to the topbar
	$$('#topbar .nav li').removeClass('active')
	$E('#topbar .nav').adopt(
		new Element('li', {'class': 'active'}).adopt(
			new Element('a',{'href':'#' + Object.toQueryString(navObj), text: 'Edit' })
		)
	);
}


function do_action(tbl, e) {
//	console.log('do_action()!');
	if (!tbl.getSelected()) return; // necessary condition to begin
	var where_stmt = where_from_selected(tbl);
	if (!where_stmt) return; // empty where stmt
	var msg = "Are you sure you want to ";
	// describe the action to be performed
	var action;
	if (e.target.hasClass("action_edit")) action = 'edit';
	else if (e.target.hasClass("action_delete")) action = 'delete';
	else if (e.target.hasClass("action_drop")) action = "drop";
	else if (e.target.hasClass("action_empty")) action = "empty";
	
	msg += action + " the selected ";
	var navObject = page_hash();
	if (navObject['sctn'] == "db" && navObject['v'] == 'overview')
		msg += where_stmt.contains(';') ? "tables" : "table";
	else if (navObject['sctn'] == "tbl" && navObject['v'] == 'browse')
		msg += where_stmt.contains(';') ? "rows" : "row";
	// confirm if intention is to be carried out
	var confirmDiag = new SimpleModal({'btn_ok': 'Yes', overlayClick: false,
		draggable: true, offsetTop: 0.2 * screen.availHeight
	});
	confirmDiag.show({
		model: 'confirm', 
		callback: function() {
			if (action == 'edit') {
				edit_page(where_stmt);
			} else {
				new XHR({
					url: generate_ajax_url(false, {}) + '&upd8=' + action,
					spinnerTarget: $(tbl), 
					onSuccess: function(text, xml) {
						var resp = JSON.decode(text);
						if (resp['status'] == "fail") {
							showDialog("Action not successful", resp['msg']);
						} else if (resp['status'] == 'success')
							pg.reload();
					}
				}).post({'where_stmt': where_stmt});
			}
		}, 
		title: 'Confirm intent',
		contents: msg
	});
}


Page.prototype.browseView = function() {	
	if (! document.getElement('.tbl-header')) return;
	var theads = document.getElement('.tbl-header table tr').getElements('td[class!=controls]');
	theads.setStyle('cursor', 'pointer');
	theads.each(function(thead, thead_in){
		// add click event
		thead.addEvent('click', function(e){
			var o = page_hash(); var key = thead.get('text'); var dir = '';
			if (o.sort_key != undefined && o.sort_key != key ) {
				dir = 'asc'
			} else {
				if (o.sort_dir == 'asc') dir = 'desc';
				else if (o.sort_dir == 'desc') dir = 'asc';
				else dir = 'asc';
			}
			o['sort_dir'] = dir; o['sort_key'] = key;
			location.hash = "#" + Object.toQueryString(o);
		});
		// mark as sort key
		if (thead.get('text') == page_hash()['sort_key']) {
			thead.setStyle('font-weight', 'bold');
			thead.addClass(page_hash()['sort_dir'] == 'asc'? 'sort-asc': 'sort-desc');
		}
	});
}

Page.prototype.updateOptions = function(obj) {
	this.options.extend(obj)
}

Page.prototype.reload = function() {
	this.loadPage();
}

// function that is called on on every form request
function formResponseListener(text, xml, form, navObject) {
	$E('.msg-placeholder').getChildren().destroy();
	if (navObject['v'] == 'query') {
		$E('.query-results').set('html', text);
		if ($E('.query-results').getElement('div.alert-message')) {
			tweenBgToWhite($E('.query-results div.alert-message'))
		}
		pg.jsifyTable();
		return; // end this function here
	}
	var resp = JSON.decode(text);
	if (resp['status'] == 'success'){
		if (navObject['subv'] == 'edit') {
			$(form).destroy();
			if (!$$('.tt_form').length) {
				delete navObject.subv;
				redirectPage(navObject);
				return;
			}
		} else {
			form.reset(); // delete the input values
		}
	}
	var html = ("" + resp['msg']).replace("\n","&nbsp;")
	if (navObject['v']=='insert' || navObject['subv']=='edit') {
		$E('.msg-placeholder').set('html', html);
		tweenBgToWhite($E('.msg-placeholder').getElement('div.alert-message'))
	}
	
}


Page.prototype.completeForm = function(){
//	console.log('completeForm()!');
	if (! $$('.tt_form').length) return ; 
	
	$$('.tt_form').each(function(form){
		// - function calls formResponseListener with needed variables
		// - hack to pass out the needed variables to an first class function
		var onFormResponse = function(text,xml) {
			formResponseListener(text,xml,form, page_hash());
		};
		
		//attach validation object
		var form_validator = new Form.Validator.Inline(form, {
			'evaluateFieldsOnBlur':false, 'evaluateFieldsOnChange': false}
		);
		// handle submission immediately after validation
		form_validator.addEvent('formValidate', function(status, form, e){
			if (!status) return; // form didn't validate
			e.stop(); // stop propagation of event and also prevent default
			// submit the values of the form
			new XHR({
				url: generate_ajax_url(false, {}),
				spinnerTarget: form,
				onSuccess: onFormResponse
			}).post(form.toQueryString());

		});		
	});
}


var XHR = new Class({

	Extends: Request,
	
	initialize: function(options) {
		options.headers = {
			'X-CSRFToken': Cookie.read('csrftoken')
		};
		options.chain = 'link';
		
		// append ajax validation key
		options.url += '&ajaxKey=' + _ajaxKey;
		this.parent(options);
		
		if (options && options.showLoader != false) {
			
			this.addEvent('onRequest', function() {
				var spinnerTarget = (options.spinnerTarget) ? options.spinnerTarget: document.body;
				var ajaxSpinner = new Spinner(spinnerTarget, {'message': 'loading data...'});
				show('header-load');
				ajaxSpinner.show(true);
				
				this.addEvent('onComplete', function(xhr){
					hide('header-load');
					ajaxSpinner.hide();
					ajaxSpinner.destroy();
				});				
			});

		}
		
		this.addEvent("onSuccess", function() {});
		
		// redirect page based on Cookie
		this.addEvent('onComplete', function() {
			if (Cookie.read('TT_SESSION_TIMEOUT')) {
				console.log('session timeout');
				Cookie.dispose('TT_SESSION_TIMEOUT');
				Cookie.write('TT_NEXT', Object.toQueryString(page_hash()));
			    // funny redirect
		        location.href = location.protocol + '//'+ location.host + location.pathname + 'login/'

			}
		});
		
		var msg = 'An unexpected error was encountered. Please reload the page and try again.';
		this.addEvent("onException", function() {
			showDialog("Exception", msg, {'draggable':false,'overlayClick':false});
		});
		
		this.addEvent("onFailure", function(xhr) {
			if (xhr.status == 500 && xhr.statusText == "UNKNOWN STATUS CODE") msg = xhr.response;
//				hide('header-load');
//                ajaxSpinner.hide();
			if (msg == 'invalid ajax request!') 
				location.reload()
			else
				showDialog('Error!', msg, {'draggable':false,'overlayClick':false})
		});
	},
	
	// redefined to avoid auto script execution
	success: function(text, xml) {
		this.onSuccess(text, xml);
	}
	
});


function show(a) {
	$(a).style.display = 'block';
}

function hide(a) {
	$(a).style.display = 'none';
}
