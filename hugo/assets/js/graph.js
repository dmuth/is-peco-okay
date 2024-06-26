

/**
* Format our date and time for the graph.
*/
function formatDateTimeGraph(datetime) {

    var datetime = new Date(datetime);
    var retval = new Intl.DateTimeFormat('en-US', {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "numeric",
        }).format(datetime);

    return(retval);

} // End of formatDateTimeGraph()


/**
* Turn our data into a data structure for our graph.
*/
function updateGraphProcessData(data_in) {

    var data = {
        labels: [],
        datasets: [
            {
            label: "Customers Impacted",
            data: [],
            borderColor: "blue",
            borderWidth: 3,
            pointStyle: "circle",
            pointRadius: 3,
            pointBorderColor: "blue",
            pointBackgroundColor: "blue",
            yAxisID: 'y',
            },
            {
            label: "Outages",
            data: [],
            borderColor: "red",
            borderWidth: 3,
            pointStyle: "circle",
            pointRadius: 3,
            pointBorderColor: "red",
            pointBackgroundColor: "red",
            yAxisID: 'y2',
            },
            ],
        }

    data_in.forEach( (value, key) => {
        
        var datetime = `${formatDateTimeGraph(value["PecoDateTime"])}`;
        data["labels"].push(datetime);
        //data["labels"].push(value["datetime"]); // Debugging
        data["datasets"][0]["data"].push(value["customers_outages"]);
        data["datasets"][1]["data"].push(value["outages"]);
        //data["datasets"][0]["data"].push(10); // Debugging
        //data["datasets"][1]["data"].push(210); // Debugging

        });

    return(data);

} // End of updateGraphProcessData()


/**
* Get our options for the graph.
*/
function updateGraphGetOptions(data) {

    var options = {
        scales: {
            y: {
                title: {
                    display: true,
                    text: "Customers Impacted"
                    },
                    ticks: {
                        // Don't show decimal points if we have a very small range.
                        precision: 0
                    },
                    position: "left",
                },
            y2: {
                title: {
                    display: true,
                    text: "Outages"
                    },
                    ticks: {
                        // Don't show decimal points if we have a very small range.
                        precision: 0
                    },
                    position: "right",
                },
            x: {
                ticks: {
                    maxTicksLimit: 24
                    },
                },
            },
        plugins: {
            legend: {
                display: true,
                position: "bottom",
                }
            }
        }

    //
    // If we have a relatively flat line and therefore a low difference between 
    // min and max values, add in some suggested minimums and maximums so there
    // are more than 1 or 2 tickmarks on the y-axis.
    //
    var min = Math.min(...data["datasets"][0]["data"]);
    var max = Math.max(...data["datasets"][0]["data"]);
    var diff = max - min;
    var min_diff = 10;

    if (diff < min_diff) {

        suggestedMin = min - 5;
        if (suggestedMin < 0) {
            suggestedMin = 0;
        }

        options.scales.y.suggestedMin = suggestedMin;
        options.scales.y.suggestedMax = max + 5;

    }

    return(options);

} // End of updateGraphGetOptions()


/**
* Return a callback that will update our graph.
*/
function updateGraphCallbackFactory(data, options) {

    return(function() {

    //
    // We're saving the chart as a global, as we'll need to call destroy() on it
    // whenever we resize the window.
    //
    var canvas = document.getElementById("peco-status-recent-graph").getContext("2d");
    window.chart = new Chart(canvas, {
        type: "line",
        data: data,
        options: options,
        });

    var element = document.getElementById("peco-status-recent");
    document.getElementById("peco-status-recent-loading").classList.add("display-none");
    fadeIn(element, .05, 50);

    });

} // End of updateGraphCallbackFactory()


/**
* Return a callback that is fired whenever the screen is resized.
*/
function handleResizeCallbackFactory(updateGraphCallback) {

    return(function() {

    var date = new Date();
    console.log(`${formatDate(date)} ${formatTime(date)}: Window resized, regenerating graph...`);
    window.chart.destroy();
    updateGraphCallback();

    });

} // End of handleResizeCallbackFactory()


/**
* Update our graph.
*/
function updateGraph(data_in) {

    var data = updateGraphProcessData(data_in);
    //console.log("DATA", JSON.stringify(data, null, 2)); // Debugging

    var options = updateGraphGetOptions(data);

    //
    // Get a closure to update our graph, call it, then pass the closure
    // into our handler for screen resizing.
    //
    updateGraphCallback = updateGraphCallbackFactory(data, options);
    updateGraphCallback();

    handleResizeCallback = handleResizeCallbackFactory(updateGraphCallback);
    window.addEventListener('resize', handleResizeCallback);

} // End of updateGraph()



