/**
* This Javascript is for our main page.
*/

console.log("Our environment: {{ .env }}");

//
// This will be substituted in by Hugo with the dev or prod base URL.
//
window.api_endpoint_base = "{{ .apiEndpointBase }}";


/**
* Fade in an element.
*
* element - The element to fade in.
* increment - How much to fade in each interval. (Should be less than 1)
* interval - Our interval in milliseconds.
*
*/
function fadeIn(element, increment, interval) {

    var opacity = 0;
    element.style.opacity = opacity;
    element.classList.remove("hidden");

    var interval_id = setInterval(function() {

        opacity += increment;
        element.style.opacity = opacity;

        if (opacity >= 1) {
            clearInterval(interval_id);
        }
        
    }, interval);

} // End of fadeIn()


/**
* Wrapper for fetch() that includes a timeout.
*
* url - The URL to fetch
* timeout - Timeout in milliseconds.  Defaults to 5000.
*
*/
function fetchWithTimeout(url, timeout = 5000) {

    //return(null); // Debugging
    return (Promise.race([
        fetch(url),
            new Promise((_, reject) => {
                setTimeout(() => reject(new Error(`Timeout after ${timeout} ms.`)), timeout)
            })
    ]));

} // End of fetchWithTimeout()


/**
* Format our timestamp.
*/
function formatDate(datetime) {

    var datetime = new Date(datetime);
    var retval = new Intl.DateTimeFormat('en-US', {
        month: "short",
        day: "numeric",
        year: "numeric",
        }).format(datetime);

    return(retval);

} // End of formatDate()


/**
* Format our timestamp.
*/
function formatTime(datetime) {

    var datetime = new Date(datetime);
    var retval = new Intl.DateTimeFormat('en-US', {
        hour: "numeric",
        minute: "numeric",
        second: "numeric",
        timeZoneName: "short"
        }).format(datetime);

    return(retval);

} // End of formatTime()


//
// Main entrypoint.
//
fetchCurrent().then(result => {
    return(fetchRecent());

}).catch(error => {
    console.log(`Caught top-level error: ${error}`);

});



