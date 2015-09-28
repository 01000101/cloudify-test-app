angular
    .module('app')
    .controller('sharedHeaderCtrl',
		[
			'$scope', '$window', '$location',
			'alertService', 
			sharedHeaderCtrl
		]);

function sharedHeaderCtrl($scope, $window, $location,
						  alertService, authService,
						  FIREBASE_URI, $firebaseObject) {
    alertService.registerObserver(function(){
        $scope.alert = alertService.alert;
    });

    // Get the current route for menu active/inactive classes
    $scope.currentPath = $location.path();
    
    $scope.clearErrors = function() {
        alertService.clearAlerts();
    };
    
    // Add a route changer function that works regardless of underlying server
    $scope.go = function (path) {
        $location.path(path);
    };
};