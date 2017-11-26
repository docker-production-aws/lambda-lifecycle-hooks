import sys, os
parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'vendor')
sys.path.append(vendor_dir)

import logging, datetime, json, time
import boto3
from functools import partial

# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(os.environ.get('LOG_LEVEL','INFO'))
def format_json(data):
  return json.dumps(data, default=lambda d: d.isoformat() if isinstance(d, datetime.datetime) else str(d))

# AWS clients
autoscaling = boto3.client('autoscaling')
ecs = boto3.client('ecs')
sns = boto3.client('sns')

# Environment variables
ecs_cluster = os.environ.get('ECS_CLUSTER')

# Returns fully paginated response
def paginated_response(func, result_key, next_token=None):
  args=dict()
  if next_token:
    args['NextToken'] = next_token
  response = func(**args)
  result = response.get(result_key)
  next_token = response.get('NextToken')
  if not next_token:
    return result
  return result + self.paginated_response(func, result_key, next_token)

# Locate ECS container instance for a given EC2 instance id
def find_ecs_instance(cluster, ec2_instance):
  func = partial(ecs.list_container_instances, cluster=cluster)
  ecs_instance_arns = paginated_response(func, 'containerInstanceArns')
  ecs_instances = ecs.describe_container_instances(
      cluster=cluster,
      containerInstances=ecs_instance_arns
  )['containerInstances']
  return next((
    instance['containerInstanceArn'] for instance in ecs_instances
    if instance['ec2InstanceId'] == ec2_instance
  ), None)

# Lambda handler function
def handler(event, context):
  log.info("Received event: %s" % format_json(event))
  # Process SNS message
  for r in event.get('Records'):
    try:
      message = json.loads(r['Sns']['Message'])
      transition, hook = message['LifecycleTransition'], message['LifecycleHookName']
      if transition != 'autoscaling:EC2_INSTANCE_TERMINATING':
        log.info("Ignoring lifecycle transition %s" % transition)
        return
      group, ec2_instance = message['AutoScalingGroupName'], message['EC2InstanceId']
      # Get ECS container instance ARN
      ecs_instance = find_ecs_instance(ecs_cluster, ec2_instance)
      if ecs_instance is None:
        raise ValueError('Could not locate ECS instance')
      # Drain instances
      log.info("Draining ECS container instance %s" % ecs_instance)
      ecs.update_container_instances_state(
        cluster=ecs_cluster,
        containerInstances=[ecs_instance],
        status='DRAINING'
      )
      # Check task count every 5 seconds
      count = 1
      while count > 0 and context.get_remaining_time_in_millis() > 10000:
        status = ecs.describe_container_instances(
          cluster=ecs_cluster,
          containerInstances=[ecs_instance]
        )['containerInstances'][0]
        log.info("Received status for container instance %s: %s" % (ecs_instance, format_json(status)))
        count = status['runningTasksCount']
        log.info("Sleeping for 5 seconds...")
        time.sleep(5)
      if count == 0:
        log.info("Successfully drained tasks - sending continue signal...")
        autoscaling.complete_lifecycle_action(
          LifecycleHookName=hook,
          AutoScalingGroupName=group,
          InstanceId=ec2_instance,
          LifecycleActionResult='CONTINUE'
        )
      else:
        log.info("Function timed out - republishing SNS message")
        sns.publish(TopicArn=r['Sns']['TopicArn'], Message=r['Sns']['Message'])
    except Exception as e:
      log.error("Exception was raised: %s" % e)
      # Abandon hook
      autoscaling.complete_lifecycle_action(
        LifecycleHookName=hook,
        AutoScalingGroupName=group,
        InstanceId=ec2_instance,
        LifecycleActionResult='ABANDON'
      )