angular
    .module('app')
    .controller('sharedFooterCtrl',
		[
			'$scope', '$location', 'alertService', 
			sharedFooterCtrl
		]);

function sharedFooterCtrl($scope, $location, alertService) {
    // Add a route changer function that works regardless of underlying server
    $scope.go = function (path) {
        $location.path(path);
    };
};