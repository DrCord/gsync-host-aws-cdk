
# Creating EC2 Instance with a given .pem keyfile

This is a sample project for Python development with CDK.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
(.venv) $ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
(.venv) $ cdk synth
```

If your VPC is created outside your CDK app, you can use `Vpc.fromLookup()`.
The CDK CLI will search for the specified VPC in the the stack’s region and account,
and import the subnet configuration.

To import an existing VPC, you should specify the following environment variables.

```
(.venv) $ export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
(.venv) $ export CDK_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
```

If you pass context variable such as `vcp_name=<your vpc name>` (e.g. `vpc_name='VPCSyncProject'`), you can use a VPC other than 'default'.


## Context variables

Used with the cdk commands `deploy` and `synth`.

required context variables:
- ec2_bastion_key_pair_name
- ec2_private_key_pair_name
- bucket_name

optional context variables:
- vpc_name

<pre>
(.venv) $ cdk synth -c ec2_bastion_key_pair_name="<i>your-ec2-bastion-key-pair-name(exclude .pem extension)</i>" -c ec2_private_key_pair_name="<i>your-ec2-private-key-pair-name(exclude .pem extension)</i>" -c bucket_name="<i>your-bucket-name</i>" --all
</pre>

Use `cdk deploy` command to create the stack shown above.

<pre>
(.venv) $ cdk deploy -c ec2_bastion_key_pair_name="<i>your-ec2-bastion-key-pair-name(exclude .pem extension)</i>" -c ec2_private_key_pair_name="<i>your-ec2-private-key-pair-name(exclude .pem extension)</i>" -c bucket_name="<i>your-bucket-name</i>" --all
</pre>

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Clean Up

Delete the CloudFormation stack by running the below command.

```
(.venv) $ cdk destroy --force --all
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!


## extras

The `--require-approval never` addition to `cdk deploy` skips the security changes prompts, which allows your stack creation to proceed fully through without needing input.