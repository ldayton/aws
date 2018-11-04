#!/usr/bin/env python3

import argparse
import boto3
import collections
import json
import os
import sys
import time

class Aws(object):

    def __init__(self, env):
        self.env = env
        self.client = boto3.client(
            service_name = 'ec2',
            region_name = env.AwsRegion,
            aws_access_key_id = env.AwsAccessKey,
            aws_secret_access_key = env.AwsSecretKey
        )
        self.resource = boto3.resource(
            service_name = 'ec2',
            region_name = env.AwsRegion,
            aws_access_key_id = env.AwsAccessKey,
            aws_secret_access_key = env.AwsSecretKey
        )

    def upload_key(self, name, path):
        with open(path) as file:
            material = file.read()
        info = self.resource.import_key_pair(KeyName=name, PublicKeyMaterial=material)
        infoDict = collections.OrderedDict()
        infoDict['Name'] = info.key_name
        infoDict['Fingerprint'] = info.key_fingerprint
        return infoDict

    def latest_ubuntu(self):
        response = self.client.describe_images(
            Owners=['099720109477'],
            Filters=[
                {
                    'Name': 'name',
                    'Values': ['ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-*']
                },
                {
                    'Name': 'architecture',
                    'Values': ['x86_64']
                },
                {
                    'Name': 'root-device-type',
                    'Values': ['ebs']
                },
                {
                    'Name': 'virtualization-type',
                    'Values': ['hvm']
                }
            ],
        )
        images = response['Images']
        return self._images_to_response_dict(images)

    def latest_centos(self):
        response = self.client.describe_images(
            Owners=['679593333241'],
            Filters=[
                {
                    'Name': 'name',
                    'Values': ['CentOS Linux 7 x86_64 HVM EBS *']
                },
                {
                    'Name': 'architecture',
                    'Values': ['x86_64']
                },
                {
                    'Name': 'root-device-type',
                    'Values': ['ebs']
                },
                {
                    'Name': 'virtualization-type',
                    'Values': ['hvm']
                }
            ]
        )
        images = response['Images']
        return self._images_to_response_dict(images)

    def _images_to_response_dict(self, images):
        from dateutil.parser import parse
        for image in images:
            image['datetime'] = parse(image['CreationDate'])
        images = sorted(images, key=lambda image: image['datetime'])
        latest = images[-1]
        dict = collections.OrderedDict()
        dict['Name'] = latest['Name']
        dict['Description'] = latest['Description']
        dict['CreationDate'] = latest['CreationDate']
        dict['Region'] = self.env.AwsRegion
        dict['ImageId'] = latest['ImageId']
        return dict

    def list_instances(self):
        instance_dicts = []
        for instance in self.resource.instances.all():
            if instance.state['Name'] != 'terminated':
                instance_dicts.append(self.instance_dict(instance.id))
        return(instance_dicts)

    def kill_instance(self, instance_id):
        instance = self.resource.Instance(instance_id)
        instance.terminate()
        return self.instance_dict(instance_id, abbreviate=True)

    def create_instance(self, name, wait_for_ip=False):
        instances = self.resource.create_instances(
            ImageId = self.env.AwsAmi,
            InstanceType = self.env.AwsInstanceType,
            KeyName = self.env.AwsKeyName,
            SecurityGroupIds = self.env.AwsSecurityGroups,
            SubnetId = self.env.AwsSubnet,
            TagSpecifications = [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': name
                        }
                    ]
                }
            ],
            MinCount=1,
            MaxCount=1
        )
        instance = instances[0]
        instance.wait_until_exists()
        if wait_for_ip:
            self._wait_for_ip(instance)
        return self.instance_dict(instance.id)

    def stop_instance(self, instance_id):
        instance = self.resource.Instance(instance_id)
        instance.stop()
        return self.instance_dict(instance.id)

    def reboot_instance(self, instance_id, wait_for_ip=False):
        instance = self.resource.Instance(instance_id)
        instance.reboot()
        if wait_for_ip:
            self._wait_for_ip(instance)
        return self.instance_dict(instance.id)

    def start_instance(self, instance_id, wait_for_ip=False):
        instance = self.resource.Instance(instance_id)
        instance.start()
        instance.wait_until_exists()
        if wait_for_ip:
            self._wait_for_ip(instance)
        return self.instance_dict(instance.id)

    def _wait_for_ip(self, instance):
        while True:
            if instance.public_ip_address != None:
                break
            else:
                time.sleep(1)
                instance.reload()

    def instance_dict(self, instance_id, abbreviate=False):
        instance = self.resource.Instance(instance_id)
        name = ''
        if instance.tags != None:
            for tag in instance.tags:
                if tag['Key'] == 'Name':
                    name = tag['Value']
        dict = collections.OrderedDict()
        dict['Name'] = name
        dict['State'] = instance.state['Name']
        dict['InstanceId'] = instance.id
        if not abbreviate:
            dict['InstanceType'] = instance.instance_type
            dict['PublicIp'] = instance.public_ip_address
            dict['PrivateIp'] = instance.private_ip_address
            dict['AvailabilityZone'] = instance.placement['AvailabilityZone']
            dict['VpcId'] = instance.vpc.id if instance.vpc != None else None
            dict['SubnetId'] = instance.subnet_id
        return dict

class AwsEnv(object):

    def __init__(self, *, AwsAccessKey, AwsSecretKey, AwsKeyName, AwsRegion,
                AwsAmi, AwsSubnet, AwsVpc, AwsSecurityGroups, AwsInstanceType):
        self.AwsAccessKey = AwsAccessKey
        self.AwsSecretKey = AwsSecretKey
        self.AwsKeyName = AwsKeyName
        self.AwsRegion = AwsRegion
        self.AwsAmi = AwsAmi
        self.AwsSubnet = AwsSubnet
        self.AwsVpc = AwsVpc
        self.AwsSecurityGroups = AwsSecurityGroups
        self.AwsInstanceType = AwsInstanceType


class Main(object):

    def __init__(self):
        self.indent = 4

    def main(self, *, Command, Args):
        env = self.default_env()
        if Args['region'] != None:
            env.AwsRegion = Args['region']
        if Command == 'latest-ubuntu':
            aws = Aws(env)
            res = aws.latest_ubuntu()
            print(json.dumps(res, indent=self.indent))
        elif Command == 'latest-centos':
            aws = Aws(env)
            res = aws.latest_centos()
            print(json.dumps(res, indent=self.indent))
        elif Command == 'list-instances':
            aws = Aws(env)
            res = aws.list_instances()
            print(json.dumps(res, indent=self.indent))
        elif Command == 'kill-instance':
            aws = Aws(env)
            res = aws.kill_instance(Args['instance_id'])
            print(json.dumps(res, indent=self.indent))
        elif Command == 'stop-instance':
            aws = Aws(env)
            res = aws.stop_instance(Args['instance_id'])
            print(json.dumps(res, indent=self.indent))
        elif Command == 'reboot-instance':
            aws = Aws(env)
            res = aws.reboot_instance(Args['instance_id'])
            print(json.dumps(res, indent=self.indent))
        elif Command == 'start-instance':
            aws = Aws(env)
            res = aws.start_instance(Args['instance_id'])
            print(json.dumps(res, indent=self.indent))
        elif Command == 'upload-key':
            aws = Aws(env)
            res = aws.upload_key(Args['name'], Args['path'])
            print(json.dumps(res, indent=self.indent))
        elif Command == 'create-instance':
            if Args['key'] != None:
                env.AwsKeyName = Args['key']
            # if Args['vpc'] != None:
            #     env.AwsVpc = Args['vpc']
            if Args['instance_type'] != None:
                env.AwsInstanceType = Args['instance_type']
            if Args['security_groups'] != None:
                env.AwsSecurityGroups = Args['security_groups'].split(',')
            if Args['ami'] != None:
                env.AwsAmi = Args['ami']
            if Args['subnet'] != None:
                env.AwsSubnet = Args['subnet']
            aws = Aws(env)
            wait = Args['wait']
            res = aws.create_instance(Args['name'], wait_for_ip=wait)
            print(json.dumps(res, indent=self.indent))

    def default_env(self):
        aws_region = os.environ['AWS_DEFAULT_REGION']
        aws_ami = os.environ['AWS_DEFAULT_AMI']
        aws_vpc = os.environ['AWS_DEFAULT_VPC']
        aws_security_groups = os.environ['AWS_DEFAULT_SECURITY_GROUPS'].split(',')
        aws_key_name = os.environ['AWS_DEFAULT_KEY_NAME']
        aws_instance_type = os.environ['AWS_DEFAULT_INSTANCE_TYPE']
        aws_subnet_id = os.environ['AWS_DEFAULT_SUBNET']
        env = AwsEnv(
            AwsAccessKey = os.environ['AWS_ACCESS_KEY_ID'],
            AwsSecretKey = os.environ['AWS_SECRET_ACCESS_KEY'],
            AwsKeyName = aws_key_name,
            AwsRegion = aws_region,
            AwsAmi = aws_ami,
            AwsSubnet = aws_subnet_id,
            AwsVpc = aws_vpc,
            AwsSecurityGroups = aws_security_groups,
            AwsInstanceType = aws_instance_type
        )
        return env

class CliParser(object):

    def parse(self):
        argparser = argparse.ArgumentParser()
        subparsers = argparser.add_subparsers()
        latest_ubuntu_parser = subparsers.add_parser('latest-ubuntu')
        latest_centos_parser = subparsers.add_parser('latest-centos')
        list_instances_parser = subparsers.add_parser('list-instances')
        create_instance_parser = subparsers.add_parser('create-instance')
        kill_instance_parser = subparsers.add_parser('kill-instance')
        start_instance_parser = subparsers.add_parser('start-instance')
        reboot_instance_parser = subparsers.add_parser('reboot-instance')
        stop_instance_parser = subparsers.add_parser('stop-instance')
        upload_key_parser = subparsers.add_parser('upload-key')
        all_parsers = [
            latest_centos_parser, latest_ubuntu_parser, list_instances_parser,
            create_instance_parser, kill_instance_parser, upload_key_parser,
            stop_instance_parser, start_instance_parser, reboot_instance_parser
        ]
        for parser in all_parsers:
            parser.add_argument('--region', help='AWS region')
        # create_instance_parser.add_argument('--vpc', help='ID of VPC to use')
        create_instance_parser.add_argument('--wait', action='store_true', help='wait for instance to have public IP')
        create_instance_parser.add_argument('--subnet', help='ID of subnet to use')
        create_instance_parser.add_argument('--key', help='name of key to use')
        create_instance_parser.add_argument('--instance-type', help="instance type, such as 'm5.xlarge'")
        create_instance_parser.add_argument('--security-groups', help="IDs of security groups to apply, comma-separated")
        create_instance_parser.add_argument('name', help="a name for the instance")
        create_instance_parser.add_argument('--ami', help="AMI ID to use")
        kill_instance_parser.add_argument('instance_id', help="ID of instance to terminate")
        stop_instance_parser.add_argument('instance_id', help="ID of instance to stop")
        start_instance_parser.add_argument('instance_id', help="ID of instance to start")
        start_instance_parser.add_argument('--wait', action='store_true', help='wait for instance to have public IP')
        reboot_instance_parser.add_argument('instance_id', help="ID of instance to reboot")
        reboot_instance_parser.add_argument('--wait', action='store_true', help='wait for instance to have public IP')
        upload_key_parser.add_argument('name', help='name of key to create')
        upload_key_parser.add_argument('path', help='path to public key file')
        args = argparser.parse_args()
        if len(sys.argv) == 1:
            argparser.print_help()
            sys.exit(1)
        return vars(args)

if __name__ == '__main__':
    args = CliParser().parse()
    Main().main(Command=sys.argv[1], Args=args)
