from aws_cdk import App, CfnOutput, Duration, Stack
from aws_cdk import aws_autoscaling as autoscaling
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr_assets as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_route53, aws_route53_targets
from constructs import Construct


class DrivecycleFargate(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc(self, "vpc", max_azs=2)

        cluster = ecs.Cluster(
            self,
            "Ec2Cluster",
            vpc=vpc,
            default_cloud_map_namespace=ecs.CloudMapNamespaceOptions(
                name="local", use_for_service_connect=True, vpc=vpc
            ),
        )

        exec_role = iam.Role.from_role_name(
            self, "exec-role", role_name="ecsTaskExecutionRole"
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
            image=ecs.ContainerImage.from_asset(directory="./drivecycleapi"),
            port_mappings=[ecs.PortMapping(container_port=81, name="api")],
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="drivecycleapi", log_retention=logs.RetentionDays.ONE_WEEK
            ),
            # health_check = ecs.HealthCheck(
            #     command=["CMD-SHELL", "curl -f http://localhost:81/health || exit 1"],
            #     start_period=Duration.minutes(1)
            # )
        )

        api_fargate_service = ecs.FargateService(
            self,
            "api-fargate",
            cluster=cluster,
            task_definition=api_task_definition,
            service_connect_configuration=ecs.ServiceConnectProps(
                services=[
                    ecs.ServiceConnectService(
                        port_mapping_name="api", dns_name="drivecycleapi", port=81
                    )
                ]
            ),
        )

        # Valhalla

        valhalla_task_definition = ecs.FargateTaskDefinition(
            self,
            "valhalla-definition",
            cpu=256,
            memory_limit_mib=512,
            execution_role=exec_role,
        )

        valhalla_container = valhalla_task_definition.add_container(
            "valhalla-container",
            image=ecs.ContainerImage.from_asset(directory="./valhalla"),
            port_mappings=[ecs.PortMapping(container_port=8002, name="valhalla")],
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="valhalla", log_retention=logs.RetentionDays.ONE_WEEK
            ),
            # health_check=ecs.HealthCheck(
            #     command=["CMD-SHELL", "curl -f http://localhost:8002/status || exit 1"],
            #     start_period=Duration.minutes(1),
            # ),
        )

        valhalla_fargate_service = ecs.FargateService(
            self,
            "valhalla-fargate",
            cluster=cluster,
            task_definition=valhalla_task_definition,
            service_connect_configuration=ecs.ServiceConnectProps(
                services=[
                    ecs.ServiceConnectService(
                        port_mapping_name="valhalla", dns_name="valhalla", port=8002
                    )
                ]
            ),
        )

        # Frontend

        frontend_task_definition = ecs.FargateTaskDefinition(
            self,
            "frontend-definition",
            cpu=256,
            memory_limit_mib=512,
            execution_role=exec_role,
        )

        frontend_container = frontend_task_definition.add_container(
            "frontend-container",
            image=ecs.ContainerImage.from_asset(directory="./frontend"),
            port_mappings=[ecs.PortMapping(container_port=80)],
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="frontend", log_retention=logs.RetentionDays.ONE_WEEK
            ),
        )

        frontend_fargate_service = ecs.FargateService(
            self,
            "frontend-fargate",
            cluster=cluster,
            task_definition=frontend_task_definition,
            service_connect_configuration=ecs.ServiceConnectProps(services=[]),
        )

        # Security Group Ingress
        api_fargate_service.connections.allow_from(
            frontend_fargate_service,
            port_range=ec2.Port.tcp(81),
            description="from frontend to api",
        )

        valhalla_fargate_service.connections.allow_from(
            api_fargate_service,
            port_range=ec2.Port.tcp(8002),
            description="from api to valhalla",
        )

        # Load Balancer
        lb = elbv2.ApplicationLoadBalancer(self, "LB", vpc=vpc, internet_facing=True)

        listener = lb.add_listener(
            "API Listener", port=80, protocol=elbv2.ApplicationProtocol.HTTP
        )

        target_group = listener.add_targets(
            "API Target",
            port=80,
            targets=[frontend_fargate_service],
            protocol=elbv2.ApplicationProtocol.HTTP,
        )

        listener.connections.allow_default_port_from_any_ipv4("open to world")

        # Route53

        hosted_zone = aws_route53.HostedZone.from_hosted_zone_attributes(
            self,
            "hosted-zone",
            hosted_zone_id="Z0306137T7P1M1OKL12B",
            zone_name="transit-drivecycle.com",
        )

        aws_route53.ARecord(
            self,
            "dev-dns-record",
            zone=hosted_zone,
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.LoadBalancerTarget(lb)
            ),
            record_name="dev",
        )

        CfnOutput(self, "LoadBalancerDNS", value=lb.load_balancer_dns_name)

        CfnOutput(
            self,
            "transit-dveicycle",
            value=f"http://dev.transit-drivecycle.com",
        )


app = App()
DrivecycleFargate(app, "transit-drivecycle")
app.synth()
