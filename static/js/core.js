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
		console.log('navigationChanged event fired');
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
	console.log('new Page() object created');
	this.options = new Hash();
	this.updateOptions({'navObj': obj, 'hash': location.hash});
	this.setTitle();
	this.generateTopMenu(obj);
	disable_unimplemented_links();
	self = this; 
	
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
	console.log('generateSidebar()!');
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
						self.completeForm();
					}
				} else if (data['section'] == 'database'){
					if (data['view'] == 'overview') {
						self.overviewView();
					}
				} else if (data['section'] == 'table'){
					if (data['view'] == 'browse'){
						self.browseView();
					} else if (data['view'] == 'structure') {
						self.structureView();
					}
				}
				self.generateSidebar();
			}
            runXHRJavascript();
        }
    },data)
    ).send()
}


Page.prototype.structureView = function(){
	console.log('structureView()!');
    this.loadTable('table_structure', 'representation',
		{'height': getWindowHeight() * .7, 'with_checkboxes':true})
	window.addEvent('resize', function(){
		$(this.data_table).setStyle('height', 'auto')
		$(this.data_table).setStyle('max-height', getWindowHeight() * .45);
	});
	
	this.loadTableOptions('data');
    updateSelectNeedsValues();
	updateForeignKeyColumns();
    this.completeForm();
}


Page.prototype.browseView = function(){
	var height = getWindowHeight() - 88;
//		var resizeTable = function(){
//			height = getWindowHeight() - 88;
//			$(this.data_table).setStyle('height', height);
//			$(this.data_table).setStyle('max-height', height);
//		}
	// heights
//        this.loadTable('browse_table','representation',{'height':height});

//		window.addEvent('resize', function(){
//			resizeTable();
//		});
}

Page.prototype.overviewView = function(){
    console.log('overviewView()!');
	var h = getWindowHeight() * .7;
//    this.loadTable('table_rpr', 'representation',
//		{'height': h, 'with_checkboxes':true})
	window.addEvent('resize', function(){
		h = getWindowHeight() * .7;
		$(this.data_table).setStyle('height', 'auto');
		$(this.data_table).setStyle('max-height', h);
	});
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

Page.prototype.loadTable = function(query, type, opts){
    console.log('loadTable() called!')
    // xhr request for table list
    var x = new XHR({'query':query, 'type':type,
        'schema': this.options.navObj.schema, 
        'database': this.options.navObj.database,
        'table': this.options.navObj.table,
        'offset': this.options.navObj.offset,
        'method': 'get',
        'onSuccess': function(text,xml){
            self.startPageLoad();
            if (JSON.validate(text)) {
                var tbl_json = JSON.decode(text);
				// keys
				if (Object.keys(tbl_json).contains('keys')){
					if (tbl_json['keys']['count'] == 0 && self.options.navObj['view'] == 'browse') {
						self.loadTableOptions('no_key');
					} else {
						var t = true;
						self.loadTableOptions('data');
						opts = Object.merge(opts, {'keys': tbl_json['keys']});
					}
				}
				// table
				if ( (t) || Object.keys(opts).contains('with_checkboxes'))
					opts['with_checkboxes'] = true;
                self.data_table = create_data_table(tbl_json['columns'],
                    tbl_json['rows'], opts);
				// pagination
                if (Object.keys(tbl_json).contains('total_count')) {
                    $('table-options').adopt(tbl_pagination(tbl_json['total_count'],
                        tbl_json['limit'], tbl_json['offset']) )
                }
            } else {
                $('sql-container').set('text','!! invalid JSON data !!');
            }

            self.endPageLoad();
        }
    }).send()
            
}


Page.prototype.completeTableView = function() {
	console.log('completeTableView()!')
	if ($('sql_table') != null ) {
		Page.prototype.data_table = new HtmlTable($('sql_table'));
		make_checkable(this.data_table);
	}
}


Page.prototype.completeTableOptions = function() {
	// #table-options processing : row selection
	if ($('table-options') != null && $('table-options').getElements('a.selecters')) {
		$('table-options').getElements('a.selecters').each(function(a_sel){
			a_sel.addEvent('click', function() {
				var option = a_sel.id.replace('select_', '');
				set_all_tr_state(self.data_table, (option == 'all') ? true : false);
			});
		});
	}

}


Page.prototype.completeForm = function(){
	console.log('completeForm()!');
    var form_name = 'tt_form';
	var form = $(form_name);
	var undisplayed_result = $('undisplayed_result');
	//validation
	var form_validator = new Form.Validator.Inline(form, {
        'evaluateFieldsOnBlur':false, 'evaluateFieldsOnChange': false}
    );
    // add new vaildation
    form_validator.add('select_requires', {
        errorMsg: function(el){
//                var stmt = '';
//                el.get('class').split(' ').each(function(item){
//                    if (item.contains('select_requires:') && assets['stmt'] != item && stmt != '')
//                        stmt = item;
//                });
//                updateAssets({'stmt':stmt})
            var ar_t = assets['stmt'].split(':');
			var msg = '';
			ar_t[1].split('|').each(function(field){
				msg += field.split('_')[0]
				if ( field != ar_t[1].split('|').getLast() )
					msg += ', '
			});
			msg +=  (ar_t[1].split('|').length > 1) ? ' fields' : ' field';
            return 'This field requires '+msg;
        },
        test: function(el){
            var stmt = '';
            el.get('class').split(' ').each(function(item){
                if (item.contains('select_requires:') && assets['stmt'] != item)
                    stmt = item;
            });
            updateAssets({'stmt':stmt});
            var ar_t = assets['stmt'].split(':');var ex_vals = ar_t[2].split('|');
            if (ex_vals.contains(el.value)) {
				var ret = 0;
				ar_t[1].split('|').each(function(cond){
					if ($('id_'+cond).value )
						ret += 0
					else
						ret += 1
				});
				return ( ret == 0) ? true : false ;
//                    if ($('id_'+ar_t[1]).value )
//                        return true
//                    else
//                        return false
            } else 
                return true
        }
    });
    
//        form_validator.addEvent('onElementFail', function(field, validatorsFailed){
//            if ($$('div.validation-advice'))
//                $$('div.validation-advice').each(function(item){
//                    item.addClass('alert-message warning')
//                });
//        });
	var request_url = generate_ajax_url(true);
    self = this;
    var xx = new Form.Request(form,undisplayed_result,{
		requestOptions:{
			'spinnerTarget': form,
			'header': {
				'X-CSRFToken': Cookie.read('csrftoken')
			},
			'url': request_url,
            onRequest: function(){
//                    form_data = serializeForm(form_name);
//                    updateAssets(form_data);
            }, 
            onSuccess: function(responseTree, responseElements, responseHTML, responseJavaScript){
            	var result_holder = $('undisplayed_result');
                $('msg-placeholder').getChildren().destroy();
                if (Cookie.read('tt_formContainsErrors')){
                    console.log('the submitted form contains errors!');
                    $('msg-placeholder').adopt($(undisplayed_result).getChildren());
                    Cookie.dispose('tt_formContainsErrors');
                } else {
                    var resp = JSON.decode( result_holder.childNodes[0].nodeValue)
                    if (resp.status == 'failed') {
                        showDialog('Error!', resp.msg, {'overlayClick':false});
                    } else {
                        // decide next course of action
                        if (self.options.navObj['view'] == home && this.options.navObj['view'] == 'home')
                            nav.set({'section':'database','view':'overview','database':form_data['name']});
                        else
                            reloadPage(); 
                    }                        
                }

            },
            onFailure: function(xhr){
                showDialog('Error!',
                    'An unexpected error was encountered. Please reload the page and try again',
                    {'overlayClick':false}
                );
            }
            
		}
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
            options.url += 'query=' + options.query;
            if (options.type)
                options.url += '&type=' + options.type;
			if (options.section)
				options.ulr += '&section' + options.section;
            if (options.schema)
                options.url += '&schema=' + options.schema;
            if (options.database)
                options.url += '&database=' + options.database;
            if (options.table)
                options.url += '&table=' + options.table;
            if (options.offset)
                options.url += '&offset=' + options.offset;
        }
		else {
			if (options.section)
				options.url += 'section=' + options.section;
			if (options.view)
				options.url += '&view=' + options.view;
			if (options.database)
				options.url += '&database=' + options.database
            if (options.schema)
                options.url += '&schema=' + options.schema
			if (options.table)
				options.url += '&table=' + options.table
		}
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


