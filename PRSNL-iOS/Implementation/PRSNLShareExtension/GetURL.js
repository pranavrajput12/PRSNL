var GetURL = function() {};

GetURL.prototype = {
    run: function(arguments) {
        // Extract the page URL and title
        var url = document.URL;
        var title = document.title;
        
        // Try to extract selected text
        var selectedText = "";
        if (window.getSelection) {
            selectedText = window.getSelection().toString();
        }
        
        // Try to extract meta description
        var description = "";
        var metaTags = document.getElementsByTagName('meta');
        for (var i = 0; i < metaTags.length; i++) {
            if (metaTags[i].getAttribute('name') === 'description') {
                description = metaTags[i].getAttribute('content');
                break;
            }
        }
        
        // Pass the data back to the extension
        arguments.completionFunction({
            "URL": url,
            "title": title,
            "selectedText": selectedText,
            "description": description
        });
    },
    
    finalize: function(arguments) {
        // Cleanup if needed
    }
};

// Register the extension
var ExtensionPreprocessingJS = new GetURL;