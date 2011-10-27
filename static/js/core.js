var pg; var nav;
var pageLoadSpinner; var ajaxSpinner;
var assets = new Hash({'xhrCount': 0});

window.addEvent('domready', function() {
    // spinners 
    pageLoadSpinner = new Spinner(document.body, {'message': 'loading page...'});
    ajaxSpinner = new Spinner(document.body, {'message': 'loading data...'});
    
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
        if (location.hash) { reloadPage(); } 
        else { nav.set({'section': 'home', 'view': 'home'}); }
    }
	
});

function clearPage(){
    if ( ! $('db-tree') || Cookie.read('tt_updateSidebar'))
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
		self = this; 
		if (Cookie.read('dont_touch')) {
			console.log('The page returned contains errors!');
			Cookie.dispose('dont_touch');
		} else {
            clearPage();
            if (! $('db-tree') || ! $('db-tree').hasChildNodes() ||Cookie.read('tt_updateSidebar')) {
                this.generatesidebar(obj);
                if (Cookie.read('updateSidebar')) Cookie.dispose('tt_updateSidebar');
            }
            
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
		title = 'tiote';
		r = location.hash.replace('#','').parseQueryString();
		Object.each(r, function(item, key){
			if (key == 'view' && r[key] == r['section']) {
			} else {
				s = ' ';
				title += s + '/' + s + item;
			}
		});
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
		
		var order = []; var prefix_str; var suffix;
		if (data['section'] == 'begin') {
			order = ['login', 'help', 'faq'];
			prefix_str = '#section=begin';
		}
		if (data['section'] == 'home') {
			order = ['home', ,'users','query', 'import', 'export'];
			prefix_str = '#section=home';
		}
		if (data['section'] == 'database') {
			order = ['overview', 'query','import','export'];
			prefix_str = '#section=database';
			suffix = ['&database=']
		}
		if (data['section'] == 'table') {
			order = ['browse', 'structure', 'insert', 'search', 'query', 'import', 'export'];
			prefix_str = '#section=table';
			suffix = ['&database=','&table='];
		}
		
		var aggregate_links = new Elements();
		order.each(function(item, key){
			elmt = links[item];
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
	
	generatesidebar: function(data) {
        var endOfTree = function(item, ula, db, schema){
            schema = schema || false;
            item.each(function(row){
                var a_icon = new Element('a', {'class':'expand','href':'#'});
                var eli = new Element('li',{'class':'tbl '+db});
                var tbl_a = new Element('a',{text:row[0],'style':'display:block;overflow:hidden',
                    href:"#section=table&view=browse&database="+db+"&table="+row[0]})
                if (schema)
                    tbl_a.href += '&schema=' + schema;
                ula.adopt(eli.adopt(a_icon, tbl_a));
            });
            return ula;
        };
        
        var updateSchemaName = function(sch){
            if (sch == 'information_schema')
                return '<strong>Catalog: </strong>' + sch;
            else if(sch == 'pg_catalog')
                return '<strong>View: </strong>' + sch;
            else 
                return '<strong>Schema: </strong>' + sch;
        };
        
		var links = new Elements();
		var eula = new Element('ul',{id:'db-tree','class':'collapse'});
		if (data['section'] == 'begin'){
			
		} else if (data['section'] == 'home' || data['section'] =='database' || data['section'] == 'table') {
			dbs_tbls = JSON.decode( shortXHR({'commonQuery':'describe_databases'}) );
			Object.each(dbs_tbls, function(db_data,db){
				var ela = new Element('li',{'class':'db '+db})
				var db_a = new Element('a',{'text':db, 'href':"#section=database&view=overview&database="+db});
				var tree_a = new Element('a', {'class':'expand','href':'#'});
				var ula = new Element('ul',{});
                if (typeOf(db_data) == 'object') {
                    var arr_uli = new Elements();
                    Object.each(db_data, function(schema_data,schema){
                        var ulala = new Element('ul',{'class':'collapse',
                            'style': 'display:none'});
                        lili = new Element('li',{'class':'schema collapse '+schema}).adopt(
                            new Element('a',{'class':'expand','href':'#'}), 
                            new Element('span',{}).set('html',updateSchemaName(schema)),
                            ulala = endOfTree(schema_data, ulala, db, schema )
                        )
                        arr_uli.include(lili);
                    });
                    eula.adopt( ela.adopt(tree_a, db_a,
                        new Element('ul',{'class':'collapse'}).adopt(arr_uli)
                    ) );
                } else {
                    ula = endOfTree(db_data, ula, db);
                    eula.adopt( ela.adopt(tree_a, db_a, ula) );                
                }

			});
			
			
		} else if (data['section'] == 'database'){
			
		} else if (data['section'] == 'table'){
			
		}

		new Element('div.sidebar').replaces($('sidebar')).id='sidebar';
        var gnlnks = new Element('ul',{});
        ['home', 'query'].each(function(lnk){
            gnlnks.adopt(new Element('li').adopt( ( new Element('a',
                {'href':location.protocol+'//'+location.host+location.pathname+'#section=home&view='+lnk,
                'text': lnk})) )
            );
        });
        $('sidebar').adopt(new Element('h6',{'text':'Quick Links'}),
            gnlnks,new Element('h6',{'text':'databases'}), eula);
		new Collapse($('db-tree'));
	},
    
    
	updateOptions: function(obj) {
		this.options.extend(obj)
	},
	
    
	generateView: function(data){
        self = this;
		x = new XHR(Object.merge({'method':'get',
            'onSuccess': function(text,xml){
                var viewData = {'text' : text,'xml' : xml};
                if (!data['section']) {
                    nav.state.empty()
                    nav.set({'section': 'home','view': 'home'});
                } else if (data['section'] == 'home') {
                    $('tt-content').set('html', viewData['text']);
                    // further individual page processing
                    if ( data['view'] == 'users') {
                        self.updateUserView();
                    } else {
                        self.completeForm();
                    }
                } else if (data['section'] == 'database'){
                    $('tt-content').set('html', viewData['text']);
                    if (data['view'] == 'overview') {
                        self.completeOverview();
                    }
                }
                runXHRJavascript();
            }
        },data)
        ).send()
	},
	
    
    completeOverview: function(){
        console.log('completeOverviewView()!');
        this.loadTable('table_rpr', 'representation')
        // varchar and set formats
        var updateSelectNeedsValues = function(){
            $$('#tt_form .compact-form select.needs-values').each(function(item){
                item.addEvent('change', function(e){
                    if (e.target.value == 'set' || e.target.value == 'enum')
                        e.target.getParent('table').getElements('.values-needed').removeClass('hidden');
                    else
                        e.target.getParent('table').getElements('.values-needed').addClass('hidden');
                });
            });
        }
        
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
                            var temp_name = sel.name.split('_');
                            sel.name = temp_name[0] +'_'+ String(form_count);
                            sel.id = 'id_'+sel.name; var cl = ''
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

	updateUserView: function(){
		// xhr request users table and load it
		this.loadTable('user_rpr','representation');
		this.loadTableOptions('user')
		console.log('updateUserView() called!');
	
		// hide some elmts
		var sbls_1 = []; var sbls_2 = [];
		var p1 = $$('.hide_1').getParent().getParent().getParent().getParent().getParent();
		p1.each(function(item,key){
			sbls_1.include(item.getSiblings()[0]);
		});
		var p2 = $$('.hide_2').getParent().getParent().getParent().getParent().getParent();
		p2.each(function(item,key){
			sbls_2.include(item.getSiblings()[0]);
			sbls_2.include(item.getSiblings()[1]);
		});
		hideAll(sbls_1); hideAll(sbls_2);
		$$('.addevnt').addEvent('change', function(e){
			jj = (e.target);
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
	
    loadTable: function(query, type){
        console.log('loadTable() called!')
        // xhr request for table list
        var x = new XHR({'query':query, 'type':type,
            'schema': this.options.navObj.database, 'method': 'get',
            'onSuccess': function(text,xml){
                self.startPageLoad();
                if (JSON.validate(text)) {
                    jsan = JSON.decode(text)

                    this.data_table = create_data_table(jsan['columns'], jsan['rows'], 'sql-container')
                } else {
                    $('sql-container').set('text','!! invalid JSON data !!');
                }
                self.endPageLoad();
            }
        }).send()
                
	},
    
    
	loadTableOptions: function(opt_type){
		var actions = function(e){ // basic router
			var whereToEdit = generate_where( data_table.toElement().id, e) ;
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
			} else { console.log('nothing to work on!')}
		}

        var do_action = function(e){
            console.log('do_action()');
            var whereToEdit = generate_where( data_table.toElement().id, e) ;
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
                var actionSpinner = new Spinner(data_table)
                var x = new XHR({'url':request_url,
                    'onRequest':function(){
                        actionSpinner.show(true);
                    },
                	'onSuccess':function(){
                		resp = JSON.decode(this.response.text);
                		if (resp.status == 'failed') {
                			showDialog(fail_msgs[e.target.id], resp.msg, {});
                		} else {
                			reloadPage();
                		}
                	},
                    'onComplete': function(){
                        actionSpinner.hide();
                    }
                }).post({'whereToEdit':whereToEdit});
            }
        }

		// opt_type = user || table || data
		console.log('loadTableOptions() called!');
		var diva = new Element('div#table-options');
		var pipi = new Element('p').adopt(new Element('span',{'text':'Select: '}));
        
		var or = ['all', 'none']; var evnts = [true, false]
		or.each(function(item, key){
			var i = new Element('a',{'text':'select '+item,'id':'select_'+item,
			'events': {
					click: function(){ set_all_tr_state(data_table, evnts[key]) }
				} 
			});
			pipi.adopt(i);
		});
		pipi.adopt(new Element('span',{'text':'With Selected: '}));
		if (opt_type == 'user')
            or = ['delete']
        else if (opt_type == 'table')
            or = ['empty', 'drop']
		or.each(function(item, key){
			var a = new Element('a',{'text':item,'id':'action_'+item,
				'events': {
					click: actions
				}
			})
			pipi.adopt(a);
		});
		diva.adopt( pipi ).inject( $('sql-container'), 'top');
	},
    
    
	completeForm : function(){
        form_name = 'tt_form';
		var form = $(form_name);
		var undisplayed_result = $('undisplayed_result');
		//validation
		var form_validator = new Form.Validator.Inline(form, {
            'evaluateFieldsOnBlur':false, 'evaluateFieldsOnChange': false}
        );
        // add new vaildation
        form_validator.add('select_requires', {
            errorMsg: function(el){
                var stmt = '';
                el.get('class').split(' ').each(function(item){
                    if (item.contains('select_requires:') && assets['stmt'] != item)
                        stmt = item;
                });
                updateAssets({'stmt':stmt})
                var ar_t = assets['stmt'].split(':');
                return 'This field requires '+ar_t[1].split('_')[0]+' field';
            },
            test: function(el){
                var stmt = '';
                el.get('class').split(' ').each(function(item){
                    if (item.contains('select_requires:') && assets['stmt'] != item)
                        stmt = item;
                });
                updateAssets({'stmt':stmt})
                var ar_t = assets['stmt'].split(':'); var ex_vals = ar_t[2].split('|');
                if (ex_vals.contains(el.value)) {
                    if ($('id_'+ar_t[1]).value )
                        return true
                    else
                        return false
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
                        resp = JSON.decode( result_holder.childNodes[0].nodeValue)
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
                    )
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
            options.url += 'query=' + options.query
            if (options.type)
                options.url += '&type=' + options.type
            if (options.schema)
                options.url += '&schema=' + options.schema
        }
		else {
			if (options.section)
				options.url += 'section=' + options.section;
			if (options.view)
				options.url += '&view=' + options.view;
			if (options.db)
				options.url += '&db=' + options.db
			if (options.table)
				options.url += '&table=' + options.table
		}
		// append ajax validation key
		options.url += '&ajaxKey=' + ajaxKey;
		this.parent(options);
		
		if (options && options.showLoader != false) {
			show('header-load');
            ajaxSpinner.show(true);
			
			this.addEvent("onSuccess", function() {
				hide('header-load');
                ajaxSpinner.hide();
			});
			
			this.addEvent("onFailure", function(xhr) {
				var msg = 'An unexpected error was encountered. Please reload the page and try again.';
				if (xhr.status == 500 && xhr.statusText == "UNKNOWN STATUS CODE") msg = xhr.response;
				hide('header-load');
                ajaxSpinner.hide();
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
	op = new Hash(data)
	op.extend({'method': 'get', 'async': false, 'timeout': 10000, 'showLoader':false})
	x = new XHR(op).send();
	
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


