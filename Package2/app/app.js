angular
    .module('app', ['ngRoute', 'ui.bootstrap'])
    .run(['$rootScope','$location', '$routeParams', function($rootScope, $location, $routeParams) {
        $rootScope.$on('$routeChangeSuccess', function(e, current, pre) {
            console.log('Current route: ' + $location.path());
        });
    }])
    .config(['$routeProvider', '$locationProvider', function($routeProvider, $locationProvider) {
        $routeProvider
            // Routes views
            .when('/', {
                templateUrl: 'app/components/architect/architectView.html',
                controller: 'architectCtrl'
            })
            
            .otherwise({
                redirectTo: '/'
            });
        
        $locationProvider.html5Mode(true);
    }])
    .directive('header', function() {
        return {
            restrict: 'E',
            templateUrl: 'app/shared/header/headerView.html',
            controller: 'sharedHeaderCtrl'
        }
    })
    .directive('footer', function() {
        return {
            restrict: 'E',
            templateUrl: 'app/shared/footer/footerView.html',
            controller: 'sharedFooterCtrl'
        }
    });