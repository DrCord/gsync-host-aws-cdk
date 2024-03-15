#!/usr/bin/env python3

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
)

from constructs import Construct


class VpcStack(Stack):

  def cfn_output_set(self) -> None:
    # cloudformation exports
    cdk.CfnOutput(self, 'VPCId', value=self.vpc.vpc_id,
      export_name='{}-VPCId'.format(self.stack_name))
    
  def vpc_create(self) -> None:
    self.vpc = aws_ec2.Vpc(self, f'{self.stack_name}-VPC',
      ip_addresses=aws_ec2.IpAddresses.cidr("10.0.0.0/16"),
      max_azs=1,

      # 'subnetConfiguration' specifies the "subnet groups" to create.
      # every subnet group will have a subnet for each AZ
      subnet_configuration=[
        {
          "cidrMask": 20,
          "name": "Public",
          "subnetType": aws_ec2.SubnetType.PUBLIC,
        },
        {
          "cidrMask": 20,
          "name": "Private",
          "subnetType": aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
        }
      ],
      gateway_endpoints={
        "S3": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.S3
        )
      }
    )

  def vpc_get(self) -> None:
    vpc_name = self.node.try_get_context('existing_vpc_name')
    self.vpc = aws_ec2.Vpc.from_lookup(self, self.node.try_get_context('existing_vpc_name'),
      is_default=True,
      vpc_name=vpc_name
    )

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)
  
    # use existing vpc?
    if self.node.try_get_context('use_existing_vpc'):
      self.vpc_get()
    else: # do not use existing vpc
      self.vpc_create()

    self.cfn_output_set()