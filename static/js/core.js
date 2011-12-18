var pg;var nav;
var pageLoadSpinner;
var assets = new Hash({'xhrCount': 0});

window.addEvent('domready', function() {
    // spinners 
    pageLoadSpinner = new Spinner(document.body, {'message': 'loading page...'});
    
	nav = new Navigation();
    
	nav.addEvent('navigationChanged', function(navObject){
		// do page initialization here
        loginState = checkLoginState();
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

function clearPage(){
	$('sidebar').getChildren().destroy();
	$('tt-content').getChildren().destroy();
}

// A single tiote page
Page = new Class({
		
	options: new Hash(),
	
	initialize: function(obj) {
		console.log('new Page() object created');
		this.updateOptions({'navObj': obj, 'hash': location.hash});
		this.setTitle('here');
		this.generateTopMenu(obj);
		disable_unimplemented_links();
		self = this; 
		if (Cookie.read('dont_touch')) {
			console.log('The page returned contains errors!');
			Cookie.dispose('dont_touch');
		} else {
            clearPage();
			this.generateView(obj); 
		}
	},
	
    startPageLoad: function() {
        console.log('startPageLoad()!')
        pageLoadSpinner.show(true);
    },
    
    endPageLoad: function() {
//        if (pageLoadSpinner.active)
            pageLoadSpinner.hide();
    },
    
	setTitle: function(){
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
		document.title = title
		this.updateOptions({'title': title});
	},
	
	generateTopMenu: function(data){
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
	},
	
	generateSidebar: function(data) {
		console.log('generateSidebar()!');
		$('sidebar').adopt( $('sidebar_data').getChildren() );
//		$('sidebar_data').dispose();
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
	},
    
    
	updateOptions: function(obj) {
		this.options.extend(obj)
	},
	
    
	generateView: function(data){
        var self = this;
		var x = new XHR(Object.merge({'method':'get',
            'onSuccess': function(text,xml){
                var viewData = {'text' : text,'xml' : xml};
                if (!data['section']) {
                    nav.state.empty()
                    nav.set({'section': 'home','view': 'home'});
                } else {
					if (data['section'] == 'home') {
						$('tt-content').set('html', viewData['text']);
						// further individual page processing
						if ( data['view'] == 'users') {
							self.userView();
						} else {
							self.completeForm();
						}
					} else if (data['section'] == 'database'){
						$('tt-content').set('html', viewData['text']);
						if (data['view'] == 'overview') {
							self.overviewView();
						} else if (data['view'] == 'schemas'){
							self.schemasView();
						}
					} else if (data['section'] == 'table'){
						$('tt-content').set('html', viewData['text']);
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
	},
	
	
	structureView: function(){
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
	},
	
	
    browseView: function(){
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
    },
    
    
    overviewView: function(){
        console.log('overviewView()!');
		var h = getWindowHeight() * .7;
        this.loadTable('table_rpr', 'representation',
			{'height': h, 'with_checkboxes':true})
		window.addEvent('resize', function(){
			h = getWindowHeight() * .7;
			$(this.data_table).setStyle('height', 'auto');
			$(this.data_table).setStyle('max-height', h);
		});
		
        // new field event and handler
            $('newColumnForm').addEvent('click', function(e){
                var temp_t = $('newColumnForm').getParent().getSiblings('.column-form');
                var newForm = temp_t[temp_t.length - 1].clone();
                var form_count = temp_t.length;
                var trs = newForm.getChildren()[1].getChildren()[0].getChildren();
                trs.each(function(tira,tira_index){
                    var tds = tira.getChildren();
                    tds.each(function(tidi, tid_index){
                        if( tidi.getChildren('label')[0] &&  tidi.getChildren('label')[0].getChildren('input')[0]){
                            tidi.getChildren('label').each(function(lab,key){
                                tt = lab.get('for').split('_');
                                lab.set('for',tt[0]+'_'+tt[1]+'_'+String(form_count)+'_'+String(key));
                                var lab_input = lab.getChildren('input')[0];
                                if (lab_input.checked) {
                                    lab_input.removeAttribute('checked');
                                }
                                lab_input.name = tt[1]+'_'+String(form_count);
                                lab_input.id = tt[0]+'_'+tt[1]+'_'+String(form_count)+'_'+String(key);                                
                            });
                        }else if( tidi.getChildren('label')[0] ){
                            var labi = tidi.getChildren('label')[0];
                            var att = labi.get('for').split('_');
                            labi.set('for',att[0]+'_'+att[1]+'_'+String(form_count));
                        } else if ( tidi.getChildren('input')[0]){
                            var inputi = tidi.getChildren('input')[0];
                            var temp_name = inputi.name.split('_');
                            inputi.name = temp_name[0] +'_'+ String(form_count);
                            inputi.id = 'id_'+inputi.name;
                            inputi.value = '';
                        } else if ( tidi.getChildren('select')[0]){
                            var sel = tidi.getChildren('select')[0];
                            temp_name = sel.name.split('_');
                            sel.name = temp_name[0] +'_'+ String(form_count);
                            sel.id = 'id_'+sel.name;var cl = ''
                            // fix the select_requires class needed for validation
                            sel.get('class').split(' ').each(function(item){
                                if (item.contains('select_requires:')){
                                    var ar_t = item.split(':');
                                    cl += ar_t[0]+':'+ar_t[1].split('_')[0]+'_'+String(form_count)+':'+ar_t[2]+' ';
                                } else {
                                    cl += item + ' ';
                                }
                            });
                            sel.removeProperty('class').set('class', cl);
                        }
                    });
                });
                newForm.inject($$('div.form-controls')[0], 'before');
                var delete_form = new Element('a',{'text':'delete column',
                    'class':'delete-form pull-right pointer'});
                // delete form event and handler
                delete_form.inject(newForm, 'top').addEvent('click',function(e){
                    e.target.getParent().destroy();
                });
                // delete all validation advice
                newForm.getElements('.validation-advice').destroy();
                updateSelectNeedsValues();

            });
        this.loadTableOptions('table');
        updateSelectNeedsValues();
        this.completeForm();
    },


	userView: function(){
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
	},
	
    loadTable: function(query, type, opts){
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
                
	},
    
    
	loadTableOptions: function(opt_type){
		var get_where = function(){
			var w = '';
			if (page_hash()['view'] == 'browse')
				w = generate_where_using_pk(data_table)
			else
				w = generate_where(data_table) ;
			return w;
		};
		
		var actions = function(e){ // basic router
			var whereToEdit = get_where();
			if ( whereToEdit ) {
				var msg = 'Are you sure you want to ';
				if (e.target.id == 'action_edit') msg += 'edit ';
				else if (e.target.id == 'action_delete') msg += 'delete ';
                else if (e.target.id == 'action_drop') msg += 'drop ';
                else if (e.target.id == 'action_empty') msg += 'empty ';
				msg += ' selected rows?';
                var confirmDiag = new SimpleModal({'btn_ok': 'Yes',
                    'overlayClick': false, 'draggable':false, 'offsetTop': 0.2 * screen.availHeight
                });
                confirmDiag.show({
                    'model': 'confirm',
                    'callback': function(){
//                        if (e.target.id == 'action_edit' ) return action_edit(e);
//						else if (e.target.id == 'action_delete') return action_delete(e);
//                        else if (e.target.id == 'action_drop') return action_drop(e);
//                        else if (e.target.id == 'action_empty') return action_empty(e);
                        return do_action(e);
                        this.hide();
                    },
                    'title': 'Confirm Action!',
                    'contents': msg
                });
			} else {console.log('nothing to work on!')}
		}

        var do_action = function(e){
			var whereToEdit = get_where();
            console.log('do_action()');
            var navObj = location.hash.replace('#','').parseQueryString();
            var fail_msgs = {'action_delete': navObj['view']+' deletion failed!',
                'action_drop': navObj['view']+' drop failed!'
            }
            
            if (whereToEdit) {
                var request_url = generate_ajax_url(true,{});
                if (e.target.id == 'action_delete') request_url += '&update=delete';
                else if (e.target.id == 'action_edit') request_url += '&update=edit';
                else if (e.target.id == 'action_drop') request_url += '&update=drop';
                else if (e.target.id == 'action_empty') request_url += '&update=empty';
                // make action request
                var x = new XHR({'url':request_url,
                    'spinnerTarget': $(data_table),
                	'onSuccess':function(){
                		var resp = JSON.decode(this.response.text);
                		if (resp.status == 'failed') {
                			showDialog(fail_msgs[e.target.id], resp.msg, {});
                		} else {
                			reloadPage();
                		}
                	}
                    
                }).post({'whereToEdit':whereToEdit});
            }
        }

		// opt_type = user || table || data
		console.log('loadTableOptions()!');
		var diva = new Element('div#table-options').inject($('sql-container'), 'top');
		if (opt_type != 'no_key') {
			var pipi = new Element('p',{'class':'pull-left'}).adopt(new Element('span',{'text':'Select: '}));

			var or = ['all', 'none'];var evnts = [true, false]
			or.each(function(item, key){
				var i = new Element('a',{'text':'select '+item,'id':'select_'+item,
				'events': {
						click: function(){set_all_tr_state(data_table, evnts[key])}
					} 
				});
				pipi.adopt(i);
			});
			pipi.adopt(new Element('span',{'text':'With Selected: '}));
			if (opt_type == 'user')
				or = ['delete'];
			else if (opt_type == 'table')
				or = ['empty', 'drop'];
			else if (opt_type == 'data')
				or = ['edit', 'delete'];
			or.each(function(item, key){
				var a = new Element('a',{'text':item,'id':'action_'+item,
					'events': {
						click: actions
					}
				});
				pipi.adopt(a);
			});
			diva.adopt( pipi ).inject($('sql-container'), 'top');
		} else {
			diva.adopt(new Element('p',{'class':'pull-left'}).adopt(
				new Element('span',{'text':'[No Primary Key defined]','style':'color:#888;'}))
			).inject($('sql-container'), 'top');
		}
		
	},
    
    
	completeForm : function(){
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
	
});


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


