#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

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

    EC2_BASTION_KEY_PAIR_NAME = self.node.try_get_context("ec2_bastion_key_pair_name")
    ec2_key_pair = aws_ec2.KeyPair.from_key_pair_attributes(self, 'EC2KeyPair',
      key_pair_name=EC2_BASTION_KEY_PAIR_NAME
    )

    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceClass.html
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceSize.html#aws_cdk.aws_ec2.InstanceSize
    ec2_instance_type = aws_ec2.InstanceType.of(
      aws_ec2.InstanceClass.BURSTABLE3,
      aws_ec2.InstanceSize.MICRO
    )

    self.sg_bastion_host = aws_ec2.SecurityGroup(self, "BastionHostSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for bastion host',
      security_group_name=f'bastion-host-sg-{self.stack_name}'
    )
    cdk.Tags.of(self.sg_bastion_host).add('Name', 'bastion-host-sg')

    #TODO: SHOULD restrict IP range allowed to ssh access - not sure what this means in this context?
    self.sg_bastion_host.add_ingress_rule(
      peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(22),
      description='SSH access from anywhere'
    )

    self.bastion_host = aws_ec2.Instance(self, "BastionHost",
      vpc=vpc,
      instance_type=ec2_instance_type,
      machine_image=aws_ec2.MachineImage.latest_amazon_linux2023(),
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC),
      security_group=self.sg_bastion_host,
      key_pair=ec2_key_pair
    )


    cdk.CfnOutput(self, 'BastionHostId',
      value=self.bastion_host.instance_id,
      export_name=f'{self.stack_name}-BastionHostId')
    
    cdk.CfnOutput(self, 'BastionHostSecurityGroup',
      value=self.sg_bastion_host.security_group_id,
      export_name=f'{self.stack_name}-BastionHostSecurityGroupId')

    cdk.CfnOutput(self, 'BastionHostPublicDNSName',
      value=self.bastion_host.instance_public_dns_name,
      export_name=f'{self.stack_name}-BastionHostPublicDNSName')
