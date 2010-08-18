// The main code file of your application

// Use the basic Akshell library
require('ak', '0.3').setup();


// The index page handler
var IndexHandler = Handler.subclass(
  {
    get: function (request) {
      return render(
        'index.html',
        {
          header: 'Hello world!'
        });
    }
  });


// The URL -> handler mapping
exports.root = new URLMap(
  IndexHandler, 'index');
