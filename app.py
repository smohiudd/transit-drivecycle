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
            vpc=vpc
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
            execution_role=exec_role
        )

        api_container = api_task_definition.add_container(
            "api-container",
            image = ecs.ContainerImage.from_asset(
                    directory="./drivecycleapi"
                ),
            logging = ecs.LogDrivers.aws_logs(
                stream_prefix="drivecycleapi",
                log_retention=logs.RetentionDays.ONE_WEEK
                )
        )

        api_container.add_port_mappings(
            ecs.PortMapping(container_port=81)
        )

        api_fargate_service = ecs.FargateService(
            self,
            "api-fargate",
            cluster=cluster,
            task_definition=api_task_definition
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
                )
        )

        valhalla_container.add_port_mappings(
            ecs.PortMapping(container_port=8002)
        )

        valhalla_fargate_service = ecs.FargateService(
            self,
            "valhalla-fargate",
            cluster=cluster,
            task_definition=valhalla_task_definition
        )

        #Frontend

        frontend_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "frontend",
            cluster=cluster,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(
                    directory="./frontend"
                ),
                execution_role=exec_role
            ),
            cpu=256,
            memory_limit_mib=512,
        )

        # api_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
        #     self, "FargateService",
        #     cluster=cluster,
        #     task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
        #         image=ecs.ContainerImage.from_registry("httpd"),
        #         command=["/bin/sh -c \"echo '<html> <head> <title>Amazon ECS Sample App</title> <style>body {margin-top: 40px; background-color: #333;} </style> </head><body> <div style=color:white;text-align:center> <h1>Amazon ECS Sample App</h1> <h2>Congratulations!</h2> <p>Your application is now running on a container in Amazon ECS.</p> </div></body></html>' >  /usr/local/apache2/htdocs/index.html && httpd-foreground\""]
        #     )
        # )

        # api_fargate_service.service.connections.security_groups[0].add_ingress_rule(
        #     peer = ec2.Peer.ipv4(vpc.vpc_cidr_block),
        #     connection = ec2.Port.tcp(80),
        #     description="Allow http inbound from VPC"
        # )

        CfnOutput(
            self, "LoadBalancerDNS",
            value=frontend_fargate_service.load_balancer.load_balancer_dns_name
        )

app = App()
DrivecycleFargate(app, "transit-drivecycle")
app.synth()
