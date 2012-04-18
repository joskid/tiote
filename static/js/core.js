var pg, nav, pageLoadSpinner; // global variables

window.addEvent('domready', function() {
    // spinners 
    pageLoadSpinner = new Spinner(document.body, {'message': 'loading page...'});
    
	nav = new Navigation();
    
	nav.addEvent('navigationChanged', function(navObject, OldNavObject){
		// do page initialization here
        var loginState = shortXHR({'loginCheck': 'yeah'});
//		console.log('navigationChanged event fired');
		if (loginState) {
			if (Cookie.read('TT_NEXT')){
				navObject = Cookie.read('TT_NEXT').parseQueryString(false, true);
				location.hash = '#' + Cookie.read('TT_NEXT');
				Cookie.dispose('TT_NEXT');
			}
		} else {
			Cookie.write('TT_NEXT', new Hash(navObject).toQueryString());
			navObject = new Hash({'sctn': 'begin', 'v': 'login'});
            // funny redirect
            location.href = location.protocol + '//'+ location.host + location.pathname + 'login/'
		}
		pg = new Page(navObject, OldNavObject);
		highlightActiveMenu();
	});
    
	if (! location.pathname.contains('login/') ) {
        if (location.hash) {reloadPage();} 
        else {nav.set({'sctn': 'home', 'v': 'home'});}
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
function Page(obj, oldObj){
	this.options = new Hash({navObj: obj, oldNavObj: oldObj});
	this.tbls = [];
	self = this; 
	// unset all window resize events
	window.removeEvents(['resize']);
	clearPage();
	this.loadPage(true)
}

Page.prototype.loadPage = function(clr_sidebar) {
	clr_sidebar = clr_sidebar || false;
	var obj = this.options.navObj, oldObj = this.options.OldNavObj;
	this.setTitle();
	this.generateTopMenu(obj);
	disable_unimplemented_links();
	this.generateView(obj, oldObj);
	if (clr_sidebar) this.generateSidebar(obj, oldObj);
}


Page.prototype.setTitle = function(new_title){
	new_title = new_title || false;
	if (! new_title) {
		var title = 'tiote';
		var r = location.hash.replace('#','').parseQueryString();
		['db','schm','tbl'].each(function(or_item){
			if (Object.keys(r).contains(or_item)) title += ' / ' + r[or_item];
		});
		if (Object.keys(r).contains('offset')) title += ' / page ' + (r['offset'] / 100 + 1);
		title += ' / ' + r['v'];
		if (Object.keys(r).contains('subv')) title += ' / ' + r['subv'];
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

Page.prototype.generateView = function(data, oldData){
//	console.log(data), console.log(oldData);
    var self = this;
	// decide if the there should be a request for sidebar
	var x = new XHR(Object.merge(data, {'method':'get',
        'onSuccess': function(text,xml){
            var viewData = {'text' : text,'xml' : xml};
            if (!data['sctn']) {
                nav.state.empty()
                nav.set({'sctn': 'home','v': 'home'});
            } else {
				$('tt-content').set('html', viewData['text']);
				if (data['sctn']=='tbl' && data['v'] =='browse') {
					self.jsifyTable(true);
					self.browseView();
				} else {self.jsifyTable(false);}
				self.addTableOpts();
				// attach events to forms
				if ($$('.tt_form')) { pg.completeForm();}				
			}
            runXHRJavascript();
        }
    })).send()
}


Page.prototype.generateSidebar = function(data, oldData) {
	var resize_sidebar = function() {
		if ($('sidebar').getScrollSize().y > (getHeight() - 50) || 
		$('sidebar').getSize().y < (getHeight() - 50)) {
			$('sidebar').setStyle('height', getHeight() - 50);
		}
	};
	// xhr request for table list
	var clear_sidebar = true;
	if (Cookie.read('TT_UPDATE_SIDEBAR')){
		clear_sidebar = true;
		Cookie.dispose('TT_UPDATE_SIDEBAR');
	} else {
		// other necessary conditions
		if ($('sidebar') && $('sidebar').getChildren().length) {
			if (oldData && 
					(oldData['sctn'] == data['sctn'] 
						&& oldData['tbl'] == data['tbl']
						&& oldData['db'] == data['db']
					)) {
						if (Object.keys(oldData).contains('schm') 
							&& Object.keys(data).contains('schm')) { // pg dialect
							if (oldData['schm'] == data['schm'])
								clear_sidebar = false;
						} else {										// mysql dialect
							clear_sidebar = false;
						}
					}
		}
	}
	
	if (clear_sidebar) {
		var x = new XHR(Object.merge({'query':'sidebar', 'type':'repr', 'method': 'get',
			onSuccess: function(text,xml){
				// if there is already sidebar data clear it
				if ($('sidebar').getChildren())
					$('sidebar').getChildren().destroy();
				$('sidebar').set('html', text);
				window.addEvent('resize', resize_sidebar);
				window.fireEvent('resize');
				// handle events
				if ($('db_select')) {
					$('db_select').addEvent('change', function(e){
						if (e.target.value != page_hash()['db']) {
							var context = {'sctn':'db','v':'overview',
								'db': e.target.value
							}
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
		}, page_hash())).send();
	}
	window.addEvent('resize', resize_sidebar);
	window.fireEvent('resize');
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
			pg.tbls[tbl_in]['vars'] = {}; // container
			if ($(pg.tbls[tbl_in]).get('data')) {
				var data = {}
				$(pg.tbls[tbl_in]).get('data').split(';').each(function(d){
					var ar = d.split(':');
					data[ar[0]] = ar[1];
				});
				pg.tbls[tbl_in]['vars']['data'] = data; // schema: [key: value]
			}
			if ($(pg.tbls[tbl_in]).get('keys')) {
				var data = []; // data[[1,2,3],...] indexes 1: name of column,
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
						var x = new XHR(Object.merge(page_hash(), {
							query: 'get_row','type':'repr',	'spinnerTarget': tbl,
							onSuccess : function(text, xml) {
								showDialog("Entry", text, {
									offsetTop: null, width: 475, hideFooter: true,
									overlayOpacity: 0, overlayClick: false
								});
							}
						})).post(where_stmt);
					});
				}
			});
		});
		
	}
}


Page.prototype.addTableOpts = function() {
	// .table-options processing : row selection
	if ($$('.table-options') != null && Object.keys(pg.tbls).length) {
		$$('.table-options').each(function(tbl_opt, tbl_opt_index){
			// enable selection of rows
			$(tbl_opt).getElements('a.selecters').each(function(a_sel){
				a_sel.addEvent('click', function() {
					a_sel.get('class').split(' ').each(function(cl){
						if (cl.contains('select_')) {
							var option = cl.replace('select_', '');
							set_all_tr_state(pg.tbls[tbl_opt_index], (option == 'all') ? true : false);
						}
					});
				});
			});
			
			// table's needing pagination
			if (Object.keys(pg.tbls[tbl_opt_index]['vars']).contains('data')) {
				$(tbl_opt).adopt(tbl_pagination(
					pg.tbls[tbl_opt_index]['vars']['data']['total_count'],
					pg.tbls[tbl_opt_index]['vars']['data']['limit'], 
					pg.tbls[tbl_opt_index]['vars']['data']['offset']));
			}
			
			$ES('a.doers', tbl_opt).each(function(doer, doer_in){
				doer.addEvent('click', function(e) {
					do_action(pg.tbls[tbl_opt_index], e);
				});

			});
		});
	}
	
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
			var x = new XHR({
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
		}, 
		title: 'Confirm intent',
		contents: msg
	});
}

function sort_dir() {
	if (page_hash()['sort_dir'] == undefined) return "asc"
	else if (!['asc','desc'].contains(page_hash()['sort_dir']) ) return "asc";
	else if (page_hash()['sort_dir']=='desc') return "asc";
	else return "desc"
}
	
	
Page.prototype.browseView = function() {	
	if (! document.getElement('.tbl-header')) return;
	var theads = document.getElement('.tbl-header table tr').getElements('td[class!=controls]');
	theads.setStyle('cursor', 'pointer');
	theads.each(function(thead, thead_in){
		// add click event
		thead.addEvent('click', function(e){
			var o = Object.merge(page_hash(), {'sort_key': thead.get('text'),
				'method': 'get', 'sort_dir': sort_dir()
				});
			redirectPage(o);
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

Page.prototype.reload = function() {this.loadPage();}

// function that is called on on every form request
function formResponseListener(text, xml, form, navObject) {
	if (navObject['v'] == 'query') {
		$E('.query-results').set('html', text);
		if ($E('.query-results').getElement('div.alert-message')) {
			tweenBgToWhite($E('.query-results div.alert-message'))
		}
		// jsifyTable
		pg.jsifyTable();
		return; // end this function here
	}
	var resp = JSON.decode(text);
	if (resp['status'] == 'success')
		form.reset() // delete the input values
	var html = ("" + resp['msg']).replace("\n","&nbsp;")
	if (navObject['v']=='insert') {
		$E('.msg-placeholder', form).set('html', html);
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
			e.stop();
			var x = new XHR({
				url: generate_ajax_url(false, {}),
				spinnerTarger: form,
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
				
		if (!options.url)
			options.url = 'ajax/?';
		if (options.loginCheck)
			options.url += 'check=login';	
		else if (options.commonQuery)
			options.url += 'commonQuery=' + options.commonQuery;
        else if (options.query){
            options.url += 'q=' + options.query;
            if (options.type) options.url += '&type=' + options.type;
        }

		if (options.url.substr(-1) != "?") options.url += "&";
		if (options.sctn) options.url += 'sctn=' + options.sctn; 
		if (options.v) options.url += '&v=' + options.v;
		if (options.db) options.url += '&db=' + options.db;
		if (options.schm) options.url += '&schm=' + options.schm;
		if (options.tbl) options.url += '&tbl=' + options.tbl;
		if (options.offset)	options.url += '&offset=' + options.offset;
		if (options.sort_key) options.url += '&sort_key=' + options.sort_key;
		if (options.sort_dir) options.url += "&sort_dir=" + options.sort_dir;
		if (options.subv) options.url += '&subv=' + options.subv;
		
		// append ajax validation key
		options.url += '&ajaxKey=' + ajaxKey;
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
			})

		}
		
		this.addEvent("onSuccess", function() {});
		
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

function hide(a) {
	$(a).style.display = 'none';
}
