var bunyan = require('bunyan');
var express = require('express');

// TODO: Have this log back to Cloudify
var log = bunyan.createLogger({name: 'Joscor'});
log.info('Logging initialized');

var app = express();

// Get the port from the Cloudify deployment
var APP_PORT = process.env.APP_PORT || 6969;

// Cloudify will test for HTTP:200 to check for life
app.get('/', function(req, res) {
    res.send('Hello world!');
});

// Spin up the API server
var server = app.listen(APP_PORT, function() {
    log.info("Application started", {
        address: server.address()
    });
});
