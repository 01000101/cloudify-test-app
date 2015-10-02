angular
    .module('app')
    .controller('sharedHeaderCtrl',
		[
			'$scope', '$window', '$location',
			'alertService', 
			sharedHeaderCtrl
		]);

function sharedHeaderCtrl($scope, $window, $location) {
    // Get the current route for menu active/inactive classes
    $scope.currentPath = $location.path();
    
    // Add a route changer function that works regardless of underlying server
    $scope.go = function (path) {
        $location.path(path);
    };
};