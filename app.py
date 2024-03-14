#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  Ec2BastionWithPemKeyStack,
  Ec2PrivateWithPemKeyStack
)


AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

vpc_stack = VpcStack(app, 'Ec2WithPemKeyVpcStack',
  env=AWS_ENV
)

ec2_bastion_stack = Ec2BastionWithPemKeyStack(app, 'Ec2BastionWithPemKeyStack',
  vpc_stack.vpc,
  env=AWS_ENV
)

ec2_private_stack = Ec2PrivateWithPemKeyStack(app, 'Ec2PrivateWithPemKeyStack',
  vpc_stack.vpc,
  ec2_bastion_stack.sg_bastion_host.security_group_id,
  env=AWS_ENV,
)

ec2_bastion_stack.add_dependency(vpc_stack)

ec2_private_stack.add_dependency(vpc_stack)
ec2_private_stack.add_dependency(ec2_bastion_stack)

app.synth()

