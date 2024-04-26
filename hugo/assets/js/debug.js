

//
// This is intended to be a static "class" (or what passes for such in Javascript...)
// that can be used to override certain values via GET data when being run on localhost.
//
Debug = {

    //
    // Is this enabled?
    //
    enabled: false,

    //
    // Story our search params object-wide.
    //
    searchParams: null,

    //
    // If we're running on localhost, enable this functionality, and grab GET method data.
    //
    init: function() {

        if (window.location.hostname != "localhost") {
            return(null);
        }

        var queryString = window.location.search;
        this.searchParams = new URLSearchParams(queryString);

        debug_enabled = this.searchParams.get("debug");
        if (debug_enabled == "0") {
            debug_enabled = false;
        }

        if (!debug_enabled) {
            console.log("We're running on localhost, but the 'debug' flag is not set in GET data, not enabling debug mode...");
            return(false);
        }

        this.enabled = true;

    },

    //
    // Wrapper function to check GET method data and override our default
    // value if there is a match for the key.
    //
    get: function(key, value) {

        if (!this.enabled) {
            return(value);
        }

        if (this.searchParams.has(key)) {
            value = this.searchParams.get(key);
            console.log(`DEBUG: Key '${key}' found in query string, returning value '${value}'...`);
            return(value);
        }

        console.log(`DEBUG: No match for key '${key}' in query string, returning default value '${value}'...`);
        return(value);

    }

}

Debug.init();


