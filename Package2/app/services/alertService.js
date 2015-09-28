angular
    .module('app')
    .factory('alertService', alertService);
    
function alertService() {
    /* Keeps track of all observers */
    var observerCallbacks = [];
    
    /* Registers a new observer for this service */
    this.registerObserver = function(userCallback) {
        observerCallbacks.push(userCallback);
    };
    
    /* Deregister an existing observer from this service */
    this.deregisterObserver = function(userCallback) {
        for( var i = observerCallbacks.length - 1; i >= 0; i-- )
            if( observerCallbacks[i] === userCallback )
                observerCallbacks.splice(i, 1);
    }
    
    /* Updates observers when a service state changes */
    var notifyObservers = function() {
        angular.forEach(observerCallbacks, function(callback) {
            callback();
        });
    }
    
    this.raiseAlert = function(err) {
        this.alert = err;
        notifyObservers();
    }
    
    this.clearAlerts = function() {
        delete this.alert;
        notifyObservers();
    }
    
    return this;
}