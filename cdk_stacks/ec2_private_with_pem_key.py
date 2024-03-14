#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam
)
from constructs import Construct


class Ec2PrivateWithPemKeyStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, bastion_security_group_id, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    EC2_PRIVATE_KEY_PAIR_NAME = self.node.try_get_context("ec2_private_key_pair_name")
    ec2_key_pair = aws_ec2.KeyPair.from_key_pair_attributes(self, 'EC2KeyPair',
      key_pair_name=EC2_PRIVATE_KEY_PAIR_NAME
    )

    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceClass.html
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceSize.html#aws_cdk.aws_ec2.InstanceSize
    ec2_instance_type = aws_ec2.InstanceType.of(
      aws_ec2.InstanceClass.BURSTABLE3,
      aws_ec2.InstanceSize.MICRO
    )

    sg_private_host = aws_ec2.SecurityGroup(self, "PrivateHostSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for private host',
      security_group_name=f'private-host-sg-{self.stack_name}'
    )
    cdk.Tags.of(sg_private_host).add('Name', 'private-host-sg')

    # only allow access from bastion server via SSH
    sg_private_host.add_ingress_rule(
      peer=aws_ec2.Peer.security_group_id(bastion_security_group_id),
      connection=aws_ec2.Port.tcp(22),
      description='SSH access from bastion host'
    )

    # commands for instance userdata
    multipart_user_data = aws_ec2.MultipartUserData()
    commands_user_data = aws_ec2.UserData.for_linux()
    multipart_user_data.add_user_data_part(commands_user_data, aws_ec2.MultipartBody.SHELL_SCRIPT, True)

    commands_user_data.add_commands("sudo yum update -y")
    commands_user_data.add_commands("sudo yum install -y libxcrypt-compat")
    commands_user_data.add_commands("curl -o goodsync-linux-x86_64-release.run https://www.goodsync.com/download/goodsync-linux-x86_64-release.run")
    commands_user_data.add_commands("sudo ./goodsync-linux-x86_64-release.run")

    private_host = aws_ec2.Instance(self, "PrivateHost",
      vpc=vpc,
      instance_type=ec2_instance_type,
      machine_image=aws_ec2.MachineImage.latest_amazon_linux2023(),
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      security_group=sg_private_host,
      key_pair=ec2_key_pair,
      user_data=commands_user_data
    )

    # bucket to access in s3
    BUCKET_NAME = self.node.try_get_context("bucket_name")

    # IAM policies attached to instance that allow s3 access to bucket objects
    private_host.add_to_role_policy(aws_iam.PolicyStatement(
        effect=aws_iam.Effect.ALLOW,
        actions=[
            's3:ListBucket'
        ],
        resources=[
            f'arn:aws:s3:::{BUCKET_NAME}',
        ],
    ))
    private_host.add_to_role_policy(aws_iam.PolicyStatement(
        effect=aws_iam.Effect.ALLOW,
        actions=[
            's3:GetObject'
        ],
        resources=[
            f'arn:aws:s3:::{BUCKET_NAME}/*',
        ],
    ))

    cdk.CfnOutput(self, 'PrivateHostId',
      value=private_host.instance_id,
      export_name=f'{self.stack_name}-PrivateHostId')
    
    cdk.CfnOutput(self, 'PrivateHostSecurityGroupId',
      value=sg_private_host.security_group_id,
      export_name=f'{self.stack_name}-PrivateHostSecurityGroupId')

    cdk.CfnOutput(self, 'PrivateHostPrivateIP',
      value=private_host.instance_private_ip,
      export_name=f'{self.stack_name}-PrivateHostPrivateIP')
