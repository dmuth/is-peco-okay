

/**
* Fetch current PECO status from endpoint and update the DOM.
*/
function fetchCurrent() {

    return new Promise((resolve) => {

    //const url = `${window.api_endpoint_base}/peco`;
    const url = `${window.api_endpoint_base}/peco/recent?num=20`;

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

        //
        // Sort the elements in ascending order by time and update our graph.
        //
        data["recent"].reverse();
        updateGraph(data["recent"]);

        // Tell our caller to move onto the next function.
        resolve();

    }).catch(error => {
        // Handle errors
        console.error(`Error fetching ${url}: ${error}`);
        //document.getElementById("peco-status-loading").classList.add("hidden");
        document.getElementById("peco-status-error").classList.remove("hidden");
        document.getElementById("peco-status-error").classList.remove("display-none");
        //document.getElementById("peco-status-recent-loading").classList.add("hidden");
        document.getElementById("peco-status-recent-error").classList.remove("hidden");
        document.getElementById("peco-status-recent-error").classList.remove("display-none");

    }); // End of fetchWithTimeout()

    }); // End of promise()

} // End of fetchCurrent()


/**
* Update the color of cells in a specific class, based on their status.
*/
function updateStatusColor(status, class_name) {

    row_class = ""
    if (status == "green") {
        row_class = "peco-row-green";
    } else if (status == "yellow") {
        row_class = "peco-row-yellow";
    } else if (status == "red") {
        row_class = "peco-row-red";
    }

    if (row_class) {
        var elements = document.querySelectorAll(class_name);
        elements.forEach( (e) => {
            e.classList.add(row_class);
        });
    }

} // End of updateStatusColor()

/**
* Update our current dashboard.
*/
function updateDashboardCurrent(data) {

    //
    // Grab our data
    //
    var display = {};
    display["customers"] = Debug.get("customers", 
        parseInt(data["customers"]).toLocaleString());
    display["customers_outages"] = Debug.get("customers.outages", 
        parseInt(data["customers_outages"])).toLocaleString();
    display["outages"] = Debug.get("total_outages", 
        parseInt(data["outages"])).toLocaleString();
    display["customers_active_percent"] = Debug.get("customers.active_percent", 
        data["customers_active_percent"] + "%");
    var datetime = new Date(data["PecoDateTime"]);
    display["date"] = Debug.get("date",
        formatDate(data["PecoDateTime"]) + "&nbsp;" + formatTime(data["PecoDateTime"]));

    // Nice
    if (display["customers_outages"] == 69 || display["customers_outages"] == 420) {
        display["customers_outages"] += " (Nice)";
    }

    // Nice
    if (display["outages"] == 69 || display["outages"] == 420) {
        display["outages"] += " (Nice)";
    }

    //
    // Get our current status code and set the cell color accordingly.
    //
    updateStatusColor(Debug.get("status", data["status"]), ".peco-current-outages");

    // Update values and fade them in.
    document.getElementById("peco-total-customers-value").innerHTML = display["customers"];
    document.getElementById("peco-outages-value").innerHTML = display["customers_outages"];
    document.getElementById("peco-total-outages-value").innerHTML = display["outages"];
    document.getElementById("peco-customers-online-value").innerHTML = display["customers_active_percent"];
    document.getElementById("peco-time-value-date").innerHTML = display["date"];

    var element = document.getElementById("peco-status");
    document.getElementById("peco-status-loading").classList.add("display-none");
    fadeIn(element, .05, 50);

} // End of updateDashboardCurrent()


/**
* Update our trends.
*/
function updateDashboardTrends(data) {

    if (data["1hour"]) {

        num = Debug.get("trend.1hour.num", parseInt(data["1hour"]["num"])).toLocaleString();
        direction = Debug.get("trend.1hour.direction", data["1hour"]["direction"]);

        e = document.getElementById("peco-customers-trend-1-hour-value")
        e.innerHTML = num;

        if (direction == "down") {
            e.innerHTML += " ↘"
        } else if (direction == "up") {
            e.innerHTML += " ↗"
        } else {
            e.innerHTML += " →"
        }

        updateStatusColor(Debug.get("trend.1hour.status", 
            data["1hour"]["status"]), ".peco-trend-1-hour");

    }

    if (data["3hour"]) {

        num = Debug.get("trend.3hour.num", parseInt(data["3hour"]["num"])).toLocaleString();
        direction = Debug.get("trend.3hour.direction", data["3hour"]["direction"]);

        e = document.getElementById("peco-customers-trend-3-hour-value")
        e.innerHTML = num

        if (direction == "down") {
            e.innerHTML += " ↘"
        } else if (direction == "up") {
            e.innerHTML += " ↗"
        } else {
            e.innerHTML += " →"
        }

        updateStatusColor(Debug.get("trend.3hour.status", 
            data["3hour"]["status"]), ".peco-trend-3-hour");

    }

    if (data["24hour"]) {

        num = Debug.get("trend.24hour.num", parseInt(data["24hour"]["num"])).toLocaleString();
        direction = Debug.get("trend.24hour.direction", data["24hour"]["direction"]);

        e = document.getElementById("peco-customers-trend-24-hour-value")
        e.innerHTML = num

        if (direction == "down") {
            e.innerHTML += " ↘"
        } else if (direction == "up") {
            e.innerHTML += " ↗"
        } else {
            e.innerHTML += " →"
        }

        updateStatusColor(Debug.get("trend.24hour.status", 
            data["24hour"]["status"]), ".peco-trend-24-hour");

    }

} // End of updateDashboardTrends()


/**
* Update our dashboard with data that we got from the API call.
*/
function updateDashboard(data) {

    updateDashboardCurrent(data["current"]);
    updateDashboardTrends(data["trends"]);

} // End of updateDashboard()


