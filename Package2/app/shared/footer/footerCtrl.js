angular
    .module('app')
    .controller('sharedFooterCtrl',
		[
			'$scope', '$location',
			sharedFooterCtrl
		]);

function sharedFooterCtrl($scope, $location) {
    // Add a route changer function that works regardless of underlying server
    $scope.go = function (path) {
        $location.path(path);
    };
};