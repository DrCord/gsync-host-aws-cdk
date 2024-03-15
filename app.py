#!/usr/bin/env python3

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  Ec2BastionWithPemKeyStack,
  Ec2PrivateWithPemKeyStack
)


def private_instance_user_data_script() -> str:
    """
    https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html#user-data-shell-scripts
    user_data script on startup to install goodsync:
    []
    - updates packages via yum
    - installs the 'libxcrypt-compat' package via yum (needed to fix missing dependency in linux for goodsync installation to proceed)
    - downloads GoodSync command line (GSync) via curl
    - installs GSync
    """

    return """
    #!/bin/bash
    yum update -y
    yum install -y libxcrypt-compat
    curl -o goodsync-linux-x86_64-release.run https://www.goodsync.com/download/goodsync-linux-x86_64-release.run
    chmod +x goodsync-linux-x86_64-release.run
    ./goodsync-linux-x86_64-release.run
    """


def main() -> None:

    AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION'))

    app = cdk.App()

    project_prefix = app.node.try_get_context("project_prefix")
    project_name = app.node.try_get_context("project_name")
    project_name_start = f'{project_prefix}-{project_name}'

    # vpc stack
    vpc_stack = VpcStack(app, f'{project_name_start}-VpcStack',
        env=AWS_ENV
    )

    # bastion host stack
    ec2_bastion_host_stack = Ec2BastionWithPemKeyStack(app, f'{project_name_start}-BastionHostStack',
        vpc_stack.vpc,
        env=AWS_ENV
    )

    # private host stack
    ec2_private_host_stack = Ec2PrivateWithPemKeyStack(app, f'{project_name_start}-PrivateHostStack',
        vpc_stack.vpc,
        ec2_bastion_host_stack.security_group.security_group_id,
        env=AWS_ENV,
    )
    # bootstrap instance via user_data post-initialize script
    ec2_private_host_stack.host.add_user_data(private_instance_user_data_script())


    # stack dependencies
    # bastion -> vpc
    ec2_bastion_host_stack.add_dependency(vpc_stack)
    # private -> bastion -> vpc
    ec2_private_host_stack.add_dependency(vpc_stack)
    ec2_private_host_stack.add_dependency(ec2_bastion_host_stack)

    app.synth()

if __name__ == "__main__":
    main()