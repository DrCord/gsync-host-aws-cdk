#!/usr/bin/env python3

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2
)

from constructs import Construct


class Ec2BastionWithPemKeyStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    self.vpc = vpc

    self.ec2_keypair_get()
    
    self.ec2_instance_type_get()

    # security group
    self.security_group_create()
    self.security_group_allow_ssh_access()
    
    self.host_bastion_create()

    self.cfn_output_set()

  def cfn_output_set(self) -> None:
    # cloudformation exports
    cdk.CfnOutput(self, 'BastionHostId',
      value=self.host.instance_id,
      export_name=f'{self.stack_name}-BastionHostId')
    
    cdk.CfnOutput(self, 'BastionHostSecurityGroup',
      value=self.security_group.security_group_id,
      export_name=f'{self.stack_name}-BastionHostSecurityGroupId')

    cdk.CfnOutput(self, 'BastionHostPublicDNSName',
      value=self.host.instance_public_dns_name,
      export_name=f'{self.stack_name}-BastionHostPublicDNSName')
    
  def ec2_keypair_get(self) -> None:
    EC2_BASTION_KEY_PAIR_NAME = self.node.try_get_context("ec2_bastion_key_pair_name")
    self.ec2_key_pair = aws_ec2.KeyPair.from_key_pair_attributes(self, 'EC2KeyPair',
      key_pair_name=EC2_BASTION_KEY_PAIR_NAME
    )

  def ec2_instance_type_get(self) -> None:
    # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceClass.html
    # https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceSize.html#aws_cdk.aws_ec2.InstanceSize
    self.ec2_instance_type = aws_ec2.InstanceType.of(
      aws_ec2.InstanceClass.BURSTABLE3,
      aws_ec2.InstanceSize.NANO
    )

  def security_group_create(self) -> None:
    self.security_group = aws_ec2.SecurityGroup(self, f'{self.stack_name}-BastionHostSG',
      vpc=self.vpc,
      allow_all_outbound=True,
      description='security group for bastion host',
      security_group_name=f'{self.stack_name}-bastion-host-sg'
    )
    cdk.Tags.of(self.security_group).add('Name', f'{self.stack_name}-bastion-host-sg')

  def security_group_allow_ssh_access(self) -> None:
    # TODO: Should restrict IP range allowed to ssh access
    # Do we know who is going to be connecting? maybe from corporate VPN IP range?
    self.security_group.add_ingress_rule(
      peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(22),
      description='SSH access from any IP!'
    )

  def host_bastion_create(self) -> None:
    self.host = aws_ec2.Instance(self, f'{self.stack_name}-BastionHost',
      vpc=self.vpc,
      instance_type=self.ec2_instance_type,
      machine_image=aws_ec2.MachineImage.latest_amazon_linux2023(),
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC),
      security_group=self.security_group,
      key_pair=self.ec2_key_pair
    )
