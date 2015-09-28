angular
    .module('app')
    .controller('architectCtrl',
		[
			'$scope', '$http', 'alertService', 
			architectCtrl
		]);

function architectCtrl($scope, $http, alertService) {
    $scope.types = [];
    
    console.log('Loading Cloudify Core types');
    $http.get('assets/yaml/dist/cloudify-core.json')
        .then(function(res) {
            $scope.types.push({
                name: "Cloudify Core",
                id: "cloudify-core",
                data: res.data
            });
            
            for( var type in res.data.node_types ) {
                console.log(' (node_type) ' + type + ': ', res.data.node_types[type])
            }
        }).catch(function(e) {
           console.log('Error: ', e); 
        });
    
    console.log('Loading Custom types');
    $http.get('assets/yaml/dist/blueprint.json')
        .then(function(res) {
            $scope.types.push({
                name: "Custom Types",
                id: "custom-types",
                data: res.data
            });
            
            for( var type in res.data.node_types ) {
                console.log(' (node_type) ' + type + ': ', res.data.node_types[type])
            }
        }).catch(function(e) {
           console.log('Error: ', e); 
        });
        
    $scope.selectNodeType = function(key, node_type) {
        $scope.activeNodeTypeName = key;
        $scope.activeNodeType = YAML.stringify(node_type, 128, 4);
        /*$scope.activeNodeType = node_type;*/
    };
}