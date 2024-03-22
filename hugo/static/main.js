/**
* This Javascript is for our main page.
*/


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
function formatDateTime(datetime) {

    var datetime = new Date(datetime);
    var retval = new Intl.DateTimeFormat('en-US', {
        weekday: "short",
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "numeric",
        second: "numeric",
        timeZoneName: "short"
        }).format(datetime);

    return(retval);

} // End of formatDateTime()


/**
* Fetch current PECO status from endpoint and update the DOM.
*/
function fetchCurrent() {

    return new Promise((resolve) => {

    const url = "https://kxdox4xv7g.execute-api.us-east-1.amazonaws.com/peco";

    fetchWithTimeout(url).then(response => {

        if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.status}`);
        }
        return(response.json());

    }).then(data => {
        //
        // Update current status data with what we fetched.
        //
        var datetime = new Date(data["datetime"]);
        document.getElementById("peco-total-customers-value").innerHTML = 
            parseInt(data["customers"]).toLocaleString();
        document.getElementById("peco-outages-value").innerHTML = 
            parseInt(data["customers_outages"]).toLocaleString();
        document.getElementById("peco-total-outages-value").innerHTML = 
            parseInt(data["outages"]).toLocaleString();
        document.getElementById("peco-customers-online-value").innerHTML = 
            data["customers_active_percent"] + "%";
        document.getElementById("peco-time-value").innerHTML = formatDateTime(data["datetime"]);

        var element = document.getElementById("peco-status");
        document.getElementById("peco-status-loading").classList.add("display-none");
        fadeIn(element, .05, 50);

        // Tell our caller to move onto the next function.
        resolve();

    }).catch(error => {
        // Handle errors
        console.error(`Error fetching ${url}: ${error}`);
        document.getElementById("peco-status-loading").classList.add("hidden");
        document.getElementById("peco-status-error").classList.remove("hidden");
        document.getElementById("peco-status-error").classList.remove("display-none");

    }); // End of fetchWithTimeout()

    }); // End of promise()

} // End of fetchCurrent()


/**
* Fetch recent statuses from PECO and update the DOM.
*/
async function fetchRecent() {

    return new Promise((resolve) => {

    const url = "https://kxdox4xv7g.execute-api.us-east-1.amazonaws.com/peco/recent";

    fetchWithTimeout(url).then(response => {
        if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.status}`);
        }
        return(response.json());

    }).then(data => {
        //
        // Update our list with the recent statuses.
        //
        const list = document.getElementById("peco-status-recent-details");

        list.innerHTML = "";

        data.forEach( (element, index) => {

            const item = document.createElement("li");
            var datetime = formatDateTime(element["datetime"]);
            var outages = parseInt(element["customers_outages"]).toLocaleString();
            var active = element["customers_active_percent"];
            item.textContent = `${datetime}: ${outages} outages, ${active}% online.`;
            list.appendChild(item);

        });
        
        var element = document.getElementById("peco-status-recent");
        document.getElementById("peco-status-recent-loading").classList.add("display-none");
        fadeIn(element, .05, 50);

        // Tell our caller to move onto the next function.
        resolve();

    }).catch(error => {
        // Handle errors
        console.error(`Error fetching ${url}: ${error}`);
        document.getElementById("peco-status-recent-loading").classList.add("hidden");
        document.getElementById("peco-status-recent-error").classList.remove("hidden");
        document.getElementById("peco-status-recent-error").classList.remove("display-none");

    }); // End of fetchWithTimeout()

    }); // End of promise()

} // End of fetchRecent()


fetchCurrent().then(result => {
    return(fetchRecent());

}).catch(error => {
    console.log(`Caught top-level error: ${error}`);

});


