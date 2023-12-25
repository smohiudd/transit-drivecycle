from aws_cdk import (
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as  elbv2,
    aws_ecr_assets as ecr,
    aws_iam as  iam,
    aws_logs as logs,
    App, CfnOutput, Stack
)
from constructs import Construct

class DrivecycleFargate(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc(
            self, 
            "vpc",
            max_azs=2
        )

        cluster = ecs.Cluster(
            self, 
            'Ec2Cluster',
            vpc=vpc,
            default_cloud_map_namespace=ecs.CloudMapNamespaceOptions(
                name="local",
                use_for_service_connect=True,
                vpc=vpc
            )
        )

        exec_role = iam.Role.from_role_name(
            self,
            "exec-role",
            role_name="ecsTaskExecutionRole"
        )

        # API 

        api_task_definition = ecs.FargateTaskDefinition(
            self,
            "api-definition",
            cpu=256,
            memory_limit_mib=512,
            execution_role=exec_role,
        )

        api_container = api_task_definition.add_container(
            "api-container",
            image = ecs.ContainerImage.from_asset(
                    directory="./drivecycleapi"
                ),
            logging = ecs.LogDrivers.aws_logs(
                stream_prefix="drivecycleapi",
                log_retention=logs.RetentionDays.ONE_WEEK
                ),
            health_check = ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost:81 || exit 1"],
                start_period=Duration.minutes(2)
            )
        )

        api_container.add_port_mappings(
            ecs.PortMapping(
                container_port=81,
                name="api"
            )
        )

        api_fargate_service = ecs.FargateService(
            self,
            "api-fargate",
            cluster=cluster,
            task_definition=api_task_definition,
            service_connect_configuration=ecs.ServiceConnectProps(
                services=[ecs.ServiceConnectService(
                    port_mapping_name="api",
                    dns_name="drivecycleapi",
                    port=81
                )
            ])
        )

        #Valhalla

        valhalla_task_definition = ecs.FargateTaskDefinition(
            self,
            "valhalla-definition",
            cpu=256,
            memory_limit_mib=512,
            execution_role=exec_role
        )

        valhalla_container = valhalla_task_definition.add_container(
            "valhalla-container",
            image = ecs.ContainerImage.from_asset(
                    directory="./valhalla"
                ),
            logging = ecs.LogDrivers.aws_logs(
                stream_prefix="valhalla",
                log_retention=logs.RetentionDays.ONE_WEEK
                ),
            health_check = ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost:8002/status || exit 1"],
                start_period=Duration.minutes(2)
            )
        )

        valhalla_container.add_port_mappings(
            ecs.PortMapping(
                container_port=8002,
                name="valhalla"
            )
        )

        valhalla_fargate_service = ecs.FargateService(
            self,
            "valhalla-fargate",
            cluster=cluster,
            task_definition=valhalla_task_definition,
            service_connect_configuration=ecs.ServiceConnectProps(
                services=[ecs.ServiceConnectService(
                    port_mapping_name="valhalla",
                    dns_name="valhalla",
                    port=8002
                )
            ])        
        )

        #Frontend

        frontend_task_definition = ecs.FargateTaskDefinition(
            self,
            "frontend-definition",
            cpu=256,
            memory_limit_mib=512,
            execution_role=exec_role
        )

        frontend_container = frontend_task_definition.add_container(
            "frontend-container",
            image = ecs.ContainerImage.from_asset(
                    directory="./frontend"
                ),
            logging = ecs.LogDrivers.aws_logs(
                stream_prefix="frontend",
                log_retention=logs.RetentionDays.ONE_WEEK
                )
        )

        frontend_container.add_port_mappings(
            ecs.PortMapping(
                container_port=80
            )
        )

        frontend_fargate_service = ecs.FargateService(
            self,
            "frontend-fargate",
            cluster=cluster,
            task_definition=frontend_task_definition,
            service_connect_configuration=ecs.ServiceConnectProps(
                services=[])        
        )


        # Security Group Ingress
        api_fargate_service.connections.allow_from(
            frontend_fargate_service,
            port_range=ec2.Port.tcp(81),
            description="from frontend to api"
        )

        valhalla_fargate_service.connections.allow_from(
            api_fargate_service,
            port_range=ec2.Port.tcp(8002),
            description="from api to valhalla"
        )

        # Container Dependencies
        
        frontend_container.add_container_dependencies(
            ecs.ContainerDependency(
                container=api_container,
                condition=ecs.ContainerDependencyCondition.HEALTHY
            )
        )

        api_container.add_container_dependencies(
            ecs.ContainerDependency(
                container=valhalla_container,
                condition=ecs.ContainerDependencyCondition.HEALTHY
            )
        )

        # frontend_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
        #     self, "frontend",
        #     cluster=cluster,
        #     task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
        #         image=ecs.ContainerImage.from_asset(
        #             directory="./frontend"
        #         ),
        #         execution_role=exec_role
        #     ),
        #     cpu=256,
        #     memory_limit_mib=512,
        # )

        lb = elbv2.ApplicationLoadBalancer(
            self,
            "LB",
            vpc=vpc,
            internet_facing=True
        )
        
        listener = lb.add_listener(
            "API Listener",
            port=80, 
            protocol=elbv2.ApplicationProtocol.HTTP
            )
            
        target_group = listener.add_targets(
            "API Target", 
            port=80, 
            targets=[frontend_fargate_service],
            protocol=elbv2.ApplicationProtocol.HTTP
        )

        listener.connections.allow_default_port_from_any_ipv4("open to world")

        CfnOutput(
            self, "LoadBalancerDNS",
            value=lb.load_balancer_dns_name
        )

app = App()
DrivecycleFargate(app, "transit-drivecycle")
app.synth()
