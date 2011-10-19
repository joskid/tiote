var pg; var nav;
var pageLoadSpinner; var ajaxSpinner;
var assets = new Hash({'xhrCount': 0});


window.addEvent('domready', function() {
    // spinners 
    pageLoadSpinner = new Spinner(document.body, {'message':'Page Loading...'});
    ajaxSpinner = new Spinner(document.body, {'message': 'loading data...'});
    
	nav = new Navigation();
	
	nav.addEvent('navigationChanged', function(navObject){
		// do page initialization here
        loginState = checkLoginState();
		console.log('navigationChanged event fired');
		if (loginState) {
			if (Cookie.read('TT_NEXT')){
				navObject = Cookie.read('TT_NEXT').parseQueryString(false, true);
				console.log( Cookie.read('TT_NEXT'))
				location.hash = '#' + Cookie.read('TT_NEXT');
				Cookie.dispose('TT_NEXT');
			}
		} else {
			console.log('not authenticated!');
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
    $('sidebar').getChildren().destroy();
    $('tt-content').getChildren().destroy();
}

// A single tiote page
Page = new Class({
		
	options: new Hash(),
	
	initialize: function(obj) {
        this.startPageLoad();
		console.log('new Page() object created');
		data = obj;
		this.updateOptions({'navObj': data, 'hash': location.hash});
		var menuData = new Hash({'section': data['section']});
		var sidebarData = new Hash({'section': data['section']});
		this.setTitle('here');
		this.generateTopMenu(menuData);
		self = this; 
		if (Cookie.read('dont_touch')) {
			console.log('The page returned contains errors!')
			Cookie.dispose('dont_touch')
		} else {
            clearPage();
            this.generatesidebar(sidebarData);
			this.getViewData(data); 
		}
        this.endPageLoad();
	},
	
    startPageLoad: function() {
        console.log('startPageLoad()!')
        pageLoadSpinner.show(true);
    },
    
    endPageLoad: function() {
        console.log('endPageLoad()!')
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
	
	getViewData: function(data){
		op = new Hash({'method': 'get', 'onSuccess': this.loadView});
		op.extend(data);
		x = new XHR(op).send()
	},
	
    generateTopMenu: function(data){
		var links = new Hash();
		l = ['query', 'import', 'export', 'insert', 'structure', 'overview', 'browse', 'update', 'search', 'home'];
		l.append(['login', 'help', 'faq', 'users',]);
		l.each(function(item){
			links[item] = new Element('a', {'text': item});
		});
		
		var order = []; var prefix_str; var suffix_str;
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
			suffix_str = '&table=';
		}
		if (data['section'] == 'table') {
			order = ['browse', 'structure', 'insert', 'search', 'query', 'import', 'export'];
			prefix_str = '#section=table';
			suffix_str = '&database=&table=';
		}
		
		var aggregate_links = new Elements();
		order.each(function(item, key){
			elmt = links[item];
			elmt.href = prefix_str + '&view=' + elmt.text;
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
		var links = new Elements();
		var eula = new Element('ul',{id:'db-tree','class':'collapse'});
		if (data['section'] == 'begin'){
			
		} else if (data['section'] == 'home') {
			dbs_tbls = JSON.decode( shortXHR({'commonQuery':'describe_databases'}) );
			Object.each(dbs_tbls, function(item,key){
				var ela = new Element('li',{'class':'dbs'})
				var db_a = new Element('a',{'text':key, 'href':"#section=database&view=overview&database="+key});
				var tree_a = new Element('a', {'class':'expand','href':'#'});
				var ula = new Element('ul',{});
				item.each(function(row){
					var a_icon = new Element('a', {'class':'expand','href':'#'});
					var eli = new Element('li',{'class':'tbls'});
					var tbl_a = new Element('a',{text:row[0],href:"#section=table&view=browse&table="+row[0]})
					ula.adopt(eli.adopt(a_icon, tbl_a));
				});
				eula.adopt( ela.adopt(tree_a, db_a, ula) );
			});
			
			
		} else if (data['section'] == 'database'){
			
		} else if (data['section'] == 'table'){
			
		}

		new Element('div.sidebar').replaces($('sidebar')).id='sidebar';
		var hh4 = new Element('h4',{'text':'databases'});
		hh4.inject($('sidebar'));
		eula.inject($('sidebar'));
		new Collapse($('db-tree'));
	},
    
    
	updateOptions: function(obj) {
		this.options.extend(obj)
	},
	
    
	loadView: function(text, xml) {
		// self = Page
		// this = xhr instance
		console.log('loadView() called!');
		self.generateView =  function(viewData, data) {
			console.log('generateView() called!');
			if(!data['section']) {
				nav.state.empty()
				nav.set({
					'section' : 'home',
					'view' : 'home'
				});
			}
			if (data['section'] == 'begin') {
				$('tt-content').set('html', viewData['text']);
			}
			if(data['section'] == 'home') {
				$('tt-content').set('html', viewData['text']);
				// further individual page processing
				if ( data['view'] == 'users') {
					self.updateUserView();
				}
			}
            runXHRJavascript();
			
		}
		
		xhrData = {'text' : text,'xml' : xml};
		self.generateView(xhrData, self.options.navObj); 
		

	},
	

	updateUserView: function(){
		// xhr request users table and load it
		var x = new XHR({'query':'user_list','type':'representation',
			'onSuccess': this.loadTable,'method':'get'}).send();
		
		this.loadTableOptions('minimal')
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
	
    loadTable: function(text,xml){
		console.log('loadTable() called!')
        self.startPageLoad();
		if (JSON.validate(text)) {
			jsan = JSON.decode(text)
            
			this.data_table = create_data_table(jsan['columns'], jsan['rows'], 'sql-container')
		} else {
			$('sql-container').set('text','!! invalid JSON data !!');
		}
        self.endPageLoad();
	},
    
	loadTableOptions: function(opt_type){
		var actions = function(e){ // basic router
			var whereToEdit = generate_where( data_table.toElement().id, e) ;
			if ( whereToEdit ) {
				var msg = 'Are you sure you want to ';
				if (e.target.id == 'action_edit') msg += 'edit ';
				else if (e.target.id == 'action_delete') msg += 'delete ';
				msg += ' selected rows?';
                var confirmDiag = new SimpleModal({'btn_ok': 'Yes',
                    'overlayClick': false, 'draggable':false
                });
                confirmDiag.show({
                    'model': 'confirm',
                    'callback': function(){
                        if (e.target.id == 'action_edit' ) return action_edit(e);
						else if (e.target.id == 'action_delete') return action_delete(e);
                        this.hide();
                    },
                    'title': 'Confirm Action!',
                    'contents': msg
                });
			} else { console.log('nothing to work on!')}
		}
		var action_delete = function(e){
			var whereToEdit = generate_where( data_table.toElement().id, e) ;
            if ( whereToEdit ) {
                var request_url = generate_ajax_url(true,{});
                request_url += '&update=delete';
                console.log(request_url);
                var x = new XHR({'url':request_url,
                	'onSuccess':function(){
                		resp = JSON.decode(this.response.text);
                		if (resp.status == 'failed') {
                			showDialog('User Deletion failed!', resp.msg, {});
                		} else {
                			reloadPage();
                		}
                	} }).post({'whereToEdit':whereToEdit});
            }
		}
		var action_edit = function(e){
			var whereToEdit = generate_where( data_table.toElement().id, e) ;
            if ( whereToEdit ){
                var request_url = generate_ajax_url(true,{});
                request_url += '&update=edit';
                var x = new XHR({'url':request_url,'onSuccess':this.loadTable }).post({'whereToEdit':whereToEdit});
            }
		}
		// opt_type = minimal || structure or browser || full
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
		if (opt_type == 'minimal')
            or = ['edit','delete']
        else
            or = []
		or.each(function(item, key){
			var a = new Element('a',{'text':item,'id':'action_'+item,
				'events': {
					click: actions
				}
			})
			pipi.adopt(a);
		});
		diva.adopt( pipi );
		diva.inject( $('sql-container'), 'top');
	},
    
	
	completeForm : function(){
		var form = $('tt_form');
		var undisplayed_result = $('undisplayed_result');
		//validation
		new Form.Validator.Inline(form);
		// generate the form submission url
		var request_url = generate_ajax_url(true);
		// integrate ajax
		var xx = new Form.Request(form,undisplayed_result,{
			requestOptions:{
				'spinnerTarget': form,
				'header': {
					'X-CSRFToken': Cookie.read('csrftoken')
				},
				'url': request_url,
                onSuccess: function(text, xml){
                	var result_holder = $('undisplayed_result');
                	resp = JSON.decode( result_holder.childNodes[0].nodeValue)
                	if (resp.status == 'failed') {
                		showDialog('Error!', resp.msg, {});
                	} else { reloadPage(); }
                }
                
			}
		})
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
                var SM = new SimpleModal({'draggable':false,'overlayClick':false});
                SM.show({
                    'title': 'Error!',
                    'contents': msg
                });
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
	op.extend({'method': 'get', 'async': false, 'timeout': 5000, 'showLoader':false})
	var x = new XHR(op).send();
	
	if (x.isSuccess() ) {
		return x.response.text;
	} else {
		return '!! request failed !!';
	}
}

function longXHR(data){
	op = new Hash(data)
	op.extend({'method': 'get', 'async': false, 'timeout': 10000, 'showLoader':true})
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


