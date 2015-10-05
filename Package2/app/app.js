angular
    .module('app', ['ngRoute', 'cloudifyjs', 'ui.bootstrap'])
    .run(['$rootScope','$location', '$routeParams', function($rootScope, $location, $routeParams) {
        $rootScope.$on('$routeChangeSuccess', function(e, current, pre) {
            console.log('Current route: ' + $location.path());
        });
    }])
    .config(['$routeProvider', '$locationProvider', '$httpProvider', function($routeProvider, $locationProvider, $httpProvider) {
        $httpProvider.defaults.useXDomain = true;
        delete $httpProvider.defaults.headers.common['X-Requested-With'];

        $routeProvider
            // Routes views
            .when('/', {
                templateUrl: 'app/components/overview/overviewView.html',
                controller: 'overviewCtrl'
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