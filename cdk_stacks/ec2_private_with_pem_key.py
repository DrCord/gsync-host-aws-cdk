#!/usr/bin/env python3

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam
)

from aws_cdk.aws_ec2 import IKeyPair

from constructs import Construct


class Ec2PrivateWithPemKeyStack(Stack):

  def cfn_output_set(self) -> None:
    # cloudformation exports
    cdk.CfnOutput(self, 'PrivateHostId',
      value=self.host.instance_id,
      export_name=f'{self.stack_name}-PrivateHostId')
    
    cdk.CfnOutput(self, 'PrivateHostSecurityGroupId',
      value=self.security_group.security_group_id,
      export_name=f'{self.stack_name}-PrivateHostSecurityGroupId')

    cdk.CfnOutput(self, 'PrivateHostPrivateIP',
      value=self.host.instance_private_ip,
      export_name=f'{self.stack_name}-PrivateHostPrivateIP')
    
  def ec2_keypair_get(self) -> None:
    EC2_PRIVATE_KEY_PAIR_NAME = self.node.try_get_context("ec2_private_key_pair_name")
    self.ec2_key_pair = aws_ec2.KeyPair.from_key_pair_attributes(self, 'EC2KeyPair',
      key_pair_name=EC2_PRIVATE_KEY_PAIR_NAME
    )
  
  def security_group_create(self) -> None:
    self.security_group = aws_ec2.SecurityGroup(self, f'{self.stack_name}-PrivateHostSG',
      vpc=self.vpc,
      allow_all_outbound=True,
      description='security group for private host',
      security_group_name=f'{self.stack_name}-private-host-sg'
    )
    cdk.Tags.of(self.security_group).add('Name', f'{self.stack_name}-private-host-sg')

  def security_group_allow_bastion_access(self) -> None:
    # only allow access from bastion server via SSH
    self.security_group.add_ingress_rule(
      peer=aws_ec2.Peer.security_group_id(self.bastion_security_group_id),
      connection=aws_ec2.Port.tcp(22),
      description='SSH access from bastion host'
    )

  def host_private_create(self) -> None:
    # private host instance
    self.host = aws_ec2.Instance(self, f'{self.stack_name}-PrivateHost',
      vpc=self.vpc,
      instance_type=self.ec2_instance_type,
      machine_image=aws_ec2.MachineImage.latest_amazon_linux2023(),
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      security_group=self.security_group,
      key_pair=self.ec2_key_pair
    )

  def ec2_instance_type_get(self) -> None:
    # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceClass.html
    # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceSize.html#aws_cdk.aws_ec2.InstanceSize
    self.ec2_instance_type = aws_ec2.InstanceType.of(
      aws_ec2.InstanceClass.BURSTABLE3,
      aws_ec2.InstanceSize.MICRO
    )

  def bucket_name_get(self) -> None:
    # s3 bucket to sync from context
    self.bucket_name = self.node.try_get_context('bucket_name')

  def host_add_s3_access_policies(self) -> None:
    # IAM policies attached to instance role that allow s3 access to bucket objects
    self.host.add_to_role_policy(aws_iam.PolicyStatement(
        effect=aws_iam.Effect.ALLOW,
        actions=[
            's3:ListBucket'
        ],
        resources=[
            f'arn:aws:s3:::{self.bucket_name}',
        ],
    ))
    self.host.add_to_role_policy(aws_iam.PolicyStatement(
        effect=aws_iam.Effect.ALLOW,
        actions=[
            's3:GetObject'
        ],
        resources=[
            f'arn:aws:s3:::{self.bucket_name}/*',
        ],
    ))

  def __init__(self, scope: Construct, construct_id: str, vpc, bastion_security_group_id, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    self.vpc = vpc
    self.bastion_security_group_id = bastion_security_group_id

    self.ec2_keypair_get()

    self.ec2_instance_type_get()

    self.bucket_name_get()

    # security group
    self.security_group_create()
    self.security_group_allow_bastion_access()
    
    self.host_private_create()
    self.host_add_s3_access_policies()    

    self.cfn_output_set()
