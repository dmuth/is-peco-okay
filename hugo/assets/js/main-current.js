

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
        updateDashboard(data);

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
* Debugging code to update our data to a certain percentage value for testing.
* All other values are replaced with sample values.
*/
function updateDashboardDebug(data, percent) {

    data["customers"] = "SAMPLE";
    data["customers_outages"] = "SAMPLE";
    data["outages"] = "SAMPLE";
    data["customers_active_percent"] = "SAMPLE";
    data["customers_active_percent"] = percent;
    data["date"] = "SAMPLE";

    return(data);

}

/**
* Update our dashboard with data that we got from the API call.
*/
function updateDashboard(data) {

    //
    // Grab our data
    //
    var display = {};
    display["customers"] = parseInt(data["customers"]).toLocaleString();
    display["customers_outages"] = parseInt(data["customers_outages"]).toLocaleString();
    display["outages"] = parseInt(data["outages"]).toLocaleString();
    display["customers_active_percent"] = data["customers_active_percent"];
    var datetime = new Date(data["datetime"]);
    display["date"] = formatDate(data["datetime"]) + "&nbsp;" + formatTime(data["datetime"]);

    // Possibly debug data
    //display = updateDashboardDebug(display, 99.01);
    //display = updateDashboardDebug(display, 98.99);
    //display = updateDashboardDebug(display, 94.99);

    //
    // Adjust colors if more than 1% of 5% of customers are without power.
    //
    if (display["customers_active_percent"] < 95) {
        var elements = document.querySelectorAll(".peco-row");
        elements.forEach( (e) => {
            e.classList.add("peco-row-red");
        });

    } else if (display["customers_active_percent"] < 99) {
        var elements = document.querySelectorAll(".peco-row");
        elements.forEach( (e) => {
            e.classList.add("peco-row-yellow");
        });
        
    }

    // Update values and fade them in.
    document.getElementById("peco-total-customers-value").innerHTML = display["customers"];
    document.getElementById("peco-outages-value").innerHTML = display["customers_outages"];
    document.getElementById("peco-total-outages-value").innerHTML = display["outages"];
    document.getElementById("peco-customers-online-value").innerHTML = display["customers_active_percent"] + "%";
    document.getElementById("peco-time-value-date").innerHTML = display["date"];

    var element = document.getElementById("peco-status");
    document.getElementById("peco-status-loading").classList.add("display-none");
    fadeIn(element, .05, 50);

} // End of updateDashboard()


