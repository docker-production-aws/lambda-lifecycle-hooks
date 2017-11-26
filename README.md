# Docker in Production using AWS EC2 Lifecycle Hooks Lambda Function

This repository defines a Lamdba function called `lifecycleHooks`, which is included with the Pluralsight course [Docker in Production using Amazon Web Services](https://app.pluralsight.com/library/courses/docker-production-using-amazon-web-services/table-of-contents).

This function processes EC2 Auto Scaling Lifecycle Hooks generating for EC2 Auto Scaling groups that operate ECS clusters, and specifically ensures ECS container instances that are about to be terminated are drained of all running containers before signalling the EC2 Auto Scaling service to proceed with instance termination.

## Branches

This repository contains two branches:

- [`master`](https://github.com/docker-production-aws/lambda-lifecycle-hooks/tree/master) - represents the initial starting state of the repository as viewed in the course.  Specifically this is an empty repository that you are instructed to create in the module **Managing ECS Infrastructure Lifecycle**.

- [`final`](https://github.com/docker-production-aws/lambda-lifecycle-hooks/tree/final) - represents the final state of the repository after completing all configuration tasks as described in the course material.

> The `final` branch is provided as a convenience in the case you get stuck, or want to avoid manually typing out large configuration files.  In most cases however, you should attempt to configure this repository by following the course material.

To clone this repository and checkout a branch you can simply use the following commands:

```
$ git clone https://github.com/docker-production-aws/lambda-lifecycle-hooks.git
...
...
$ git checkout final
Switched to branch 'final'
$ git checkout master
Switched to branch 'master'
```

## Errata

No known issues.

## Further Reading

- [EC2 Auto Scaling Lifecycle](http://docs.aws.amazon.com/autoscaling/latest/userguide/AutoScalingGroupLifecycle.html)
- [EC2 Auto Scaling Lifecycle Hooks](http://docs.aws.amazon.com/autoscaling/latest/userguide/lifecycle-hooks.html)
- [ECS Container Instance Draining](http://docs.aws.amazon.com/AmazonECS/latest/developerguide/container-instance-draining.html)

## Build Instructions

To complete the build process you need the following tools installed:

- Python 2.7
- PIP package manager
- [AWS CLI](https://aws.amazon.com/cli/)

Any dependencies need to defined in `src/requirements.txt`.  Note that you do not need to include `boto3`, as this is provided by AWS for Python Lambda functions.

To build the function and its dependencies:

`make build`

This will create the necessary dependencies in the `src` folder and create a ZIP package in the `build` folder.  This file is suitable for upload to the AWS Lambda service to create a Lambda function.

```
$ make build
=> Building lifecycleHooks.zip...
...
...
updating: requirements.txt (stored 0%)
updating: setup.cfg (stored 0%)
updating: lifecycleHooks.py (deflated 63%)
=> Built build/lifecycleHooks.zip
```

### Function Naming

The default name for this function is `lifecycleHooks` and the corresponding ZIP package that is generated is called `lifecycleHooks.zip`.

If you want to change the function name, you can either update the `FUNCTION_NAME` setting in the `Makefile` or alternatively configure an environment variable of the same name to override the default function name.

## Publishing the Function

When you publish the function, you are simply copying the built ZIP package to an S3 bucket.  Before you can do this, you must ensure you have created the S3 bucket and your environment is configured correctly with appropriate AWS credentials and/or profiles.

To specify the S3 bucket that the function should be published to, you can either configure the `S3_BUCKET` setting in the `Makefile` or alternatively configure an environment variable of the same name to override the default S3 bucket name.

> [Versioning](http://docs.aws.amazon.com/AmazonS3/latest/dev/Versioning.html) should be enabled on the S3 bucket

To deploy the built ZIP package:

`make publish`

This will upload the built ZIP package to the configured S3 bucket.

> When a new or updated package is published, the S3 object version will be displayed.

### Publish Example

```
$ make publish
...
...
=> Built build/lifecycleHooks.zip
=> Publishing lifecycleHooks.zip to s3://123456789012-cfn-lambda...
=> Published to S3 URL: https://s3.amazonaws.com/123456789012-cfn-lambda/lifecycleHooks.zip
=> S3 Object Version: gyujkgVKoH.NVeeuLYTi_7n_NUburwa4
```