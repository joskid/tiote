/* Navigation.js

Copyright (c) 2010 Jay Carlson

Description:
A MooTools Class to manage AJAX application states using the URL hash.

Usage:
1) initialize your navigation class:
   
   var mynav = new Navigation();

2) Attach a "navigationChanged" event listener to the Navigation object:

  mynav.addEvent("navigationChanged", function(navObject){
	// insert your application logic to process the navObject here										   
  });
  
3) Wire your UI elements (buttons) to update the navigation bar, instead of being wired to the application logic directly:

   $('someLink').addEvent('click', function() {
       mynav.set("page","index.php"); // sets the page key to the value of "index.php"
   });

4) enjoy!


------------------------
Function Reference:
------------------------

Navigation Method: constructor
Syntax:
  var myNav = new Navigation([options]);
Arguments:
  1. options - (object, optional) An objet with the options for the navigation. See below.
Options:
  interval - (number: defaults to 200) The number of miliseconds between function calls for polling method. Note that newer browsers implement an event-based model that doesn't require polling.



Navigation Method: set
 - add or update key(s) with value(s).
Syntax:
  myNav.set(key, value);
Arguments:
  1. key - (mixed) The key you wish to create or update. If only one argument is provided and it is an object, it will be used as a key/value pair.
  2. value - (string) The value associated with the key when called with two arguments.
Examples:
  myNav.set('page','index.php') // creates or updates the 'page' key with the value of 'index.php'
  myNav.set({'page':'index.php','sort':'desc'}); // creates or updates both the 'page' and the 'sort' keys.
  


Navigation Method: unset
 - remove key(s)
Syntax:
  myNav.unset(keys);
Arguments:
  1. keys - (mixed) a string or array or object of keys to remove from the hash and navigation object.
Examples:
  myNav.unset('page'); // removes the 'page' key/value pair.
  myNav.unset(['viewMode','photoID']); // removes the 'viewMode' and 'photoID' key/value pairs.
  


Navigation Method: clearAndSet
 - clear the entire hash, and set key(s) with value(s)
Syntax:
  myNav.clearAndSet(key, value);
Arguments:
  1. key - (mixed) The key you wish to create or update. If only one argument is provided and it is an object, it will be used as a key/value pair.
  2. value - (string) The value associated with the key when called with two arguments.
Examples:
  //  example hash before: #story=47381&viewMode=full&displayPhoto=false
  myNav.clearAndSet(viewMode, normal); // hash after: #viewMode=normal


*/

var Navigation = new Class({
	Implements: [Options, Events],
	options: {
		interval: 200
		
	},
	state: null,
	oldState: null,
	oldLocation: "",
	initialize: function(options) {
		this.setOptions(options);
		this.oldState = new Hash();
		this.state = new Hash();
		if("onhashchange" in window) {
			window.onhashchange = this.agent.bind(this);
			this.agent();
		} else {
			var navigationChangeTimer = setInterval(this.agent.bind(this), this.options.interval);
		}
	},
	
	agent: function() {
		if ( Cookie.read('_nav_dnt_fire') ) {
			Cookie.dispose('_nav_dnt_fire');
			return;
		}
		if(this.oldLocation.length < 1 || this.oldLocation != window.location.hash.substr(1, window.location.hash.length-1)) { //only update if the location changed
			if (this.oldLocation != "") {
				this.oldState.empty();
				this.oldState.extend(this.oldLocation.parseQueryString(false, true));
			}
			this.oldLocation = window.location.hash.substr(1, window.location.hash.length-1);
			this.state.empty();
			this.state.extend(this.oldLocation.parseQueryString(false, true));
			this.fireEvent("navigationChanged", [this.state, this.oldState]);
		}	
	},
	updateLocation: function() {
		window.location.hash = this.state.toQueryString().cleanQueryString();	
	},
	set: function(key, value, dnt_fire_event) {
		dnt_fire_event = dnt_fire_event || false;
		if (dnt_fire_event)
			Cookie.write('_nav_dnt_fire', true);
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
