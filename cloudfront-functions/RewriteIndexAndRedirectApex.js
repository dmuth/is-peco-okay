function handler(event) {
    
    var request = event.request;
    var host = request.headers.host.value;
    var uri = request.uri;
    var redirectHost = "www.ispecookay.com";

    //
    // If we're going to the apex domain ,redirect
    //
    if (host === "ispecookay.com") {
        var response = {
            statusCode: 301,
            statusDescription: "Moved Permanently",
            headers: {
                location: {
                    value: "https://" + redirectHost + request.uri
                }
            }
        };
        return response;
    }

    // Check whether the URI is missing a file name.
    if (uri.endsWith('/')) {
        request.uri += 'index.html';
        
    } else if (!uri.includes('.')) {
        // Check whether the URI is missing a file extension.
        request.uri += '/index.html';
    }

    // Return the request
    return request;
    
}

