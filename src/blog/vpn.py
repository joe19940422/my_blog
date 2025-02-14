import boto3
import json

from ipware import get_client_ip
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from botocore.exceptions import BotoCoreError, ClientError
from datetime import datetime, timedelta
from django.core.mail import EmailMessage


html_content = """
<html>
<head>
    <title>Redirecting</title>
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #f0f0f0;
            font-family: Arial, sans-serif;
        }
        .container {
            text-align: center;
            padding: 20px;
            background-color: #ffffff;
            border: 1px solid #cccccc;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }
        .container p {
            font-size: 1.5em;
            color: #333333;
        }
    </style>
    <script type="text/javascript">
        // Redirect to the specified URL after a delay
        setTimeout(function() {
            window.location.href = "http://pengfeiqiao.com/blog/aws/";
        }, 16000); // 16000 milliseconds = 16 seconds

        // Countdown timer
        var countdown = 16;
        function updateCountdown() {
            if (countdown > 0) {
                countdown--;
                document.getElementById('countdown').innerHTML = countdown;
            }
        }
        setInterval(updateCountdown, 1000); // Update countdown every second
    </script>
</head>
<body>
    <div class="container">
        <p>請稍候 <span id="countdown">16</span> 秒，我們將進入主頁，請在 2 分鐘後下載您的配置.</p>
    </div>
</body>
</html>
"""


html_content_vpn_already_started = """
    <html>
    <head>
        <title>Redirecting</title>
        <script type="text/javascript">
            // Redirect to Google after a delay
            setTimeout(function() {
                window.location.href = "http://pengfeiqiao.com/blog/aws/";
            }, 4000); // 8000 milliseconds = 8 seconds
        </script>
    </head>
    <body>
        <p>嘿 伺服器已經啟動了你不需要啟動，我們將進入主頁，請下載您的配置.</p>
    </body>
    </html>
    """

html_content_vpn_not_already = """
    <html>
    <head>
        <title>Redirecting</title>
        <script type="text/javascript">
            // Redirect to Google after a delay
            setTimeout(function() {
                window.location.href = "http://pengfeiqiao.com/blog/aws/";
            }, 4000); // 8000 milliseconds = 8 seconds
        </script>
    </head>
    <body>
        <p>嘿 嘿，伺服器仍在啟動，您需要稍等一下 我們將進入主頁，請再試一次 下載您的配置.</p>
    </body>
    </html>
    """

info_vpn_account = {
    "taiwan": {
        "region_name": "ap-northeast-1",
        "security_group_ids": "sg-027ae28d7aac002e8",
        "AvailabilityZone": "ap-northeast-1-tpe-1a",
        "InstanceType": "t3.medium",
        "subnet_id": "subnet-04ff9ea4548f3fe7b",
        "key_name": "taipei",
        "ImageId":'ami-0a290015b99140cd1'
    },
    "hk": {
        "region_name": "ap-east-1",
        "security_group_ids": "sg-03c8eb17866a1469a",
        "AvailabilityZone": "ap-east-1a",
        "InstanceType": "t3.micro",
        "subnet_id": "subnet-0080560f56d07ff8f",
        "key_name": "hk",
        "ImageId":'ami-01c19c4912400a3fd'
    },
    "us": {
        "region_name": "us-west-1",
        "security_group_ids": "sg-04f745ad7ffe47069",
        "AvailabilityZone": "us-west-1b",
        "InstanceType": "t2.micro",
        "subnet_id": "subnet-0a44dee48c84db504",
        "key_name": "us",
        "ImageId":'ami-07d2649d67dbe8900'
    },
    "jp": {
        "region_name": "ap-northeast-1",
        "security_group_ids": "sg-027ae28d7aac002e8",
        "AvailabilityZone": "ap-northeast-1a",
        "InstanceType": "t2.micro",
        "subnet_id": "subnet-00e2fedb920d4edfc",
        "key_name": "taipei",
        "ImageId":'ami-0a290015b99140cd1'
    },
}

def create_vpn(country):
    vpn_ec2 = boto3.client('ec2', region_name=info_vpn_account[country]["region_name"])

    BlockDeviceMappings = [
        {
            'DeviceName': '/dev/sda1',
            'Ebs': {
                'DeleteOnTermination': True,
                'VolumeSize': 8,
                'VolumeType': 'gp2'
            }
        },
    ]

    user_data = f'''#!/bin/bash
    wget https://raw.githubusercontent.com/joe19940422/vpn_project/refs/heads/main/wireguard.sh
    bash wireguard.sh
    cp /root/fei_taiwan.conf /home/ubuntu/
    mv /home/ubuntu/fei_taiwan.conf /home/ubuntu/fei_{country}.conf
    chown ubuntu:ubuntu /home/ubuntu/fei_{country}.conf
    chmod 777 /home/ubuntu/fei_{country}.conf
    # /root/fei_taiwan/conf
    '''
    placement = {
        'AvailabilityZone': info_vpn_account[country]["AvailabilityZone"]
    }

    # Create the EC2 instance
    response = vpn_ec2.run_instances(
        BlockDeviceMappings=BlockDeviceMappings,
        ImageId=info_vpn_account[country]["ImageId"],
        InstanceType=info_vpn_account[country]["InstanceType"],
        KeyName=info_vpn_account[country]["key_name"],
        MinCount=1,
        MaxCount=1,
        UserData=user_data,
        Placement=placement,
        SubnetId=info_vpn_account[country]["subnet_id"],
        SecurityGroupIds=[info_vpn_account[country]["security_group_ids"]],

    )
    print(response)

def start_vpn(country, request):
    client_ip, _ = get_client_ip(request)
    if client_ip:
        # Define a cache key based on the client's IP address
        cache_key = f'rate_limit_{client_ip}'
        print(client_ip)

        # Check if the IP address is rate-limited
        if not cache.get(cache_key):
            # Set a cache value to indicate that the IP address is rate-limited
            cache.set(cache_key, True, 100)  # 100 seconds (1.2 minute)

            create_vpn(country=country)

            send_mail(
                f'VPN({country}): is Staring ',
                f'VPN({country}): is Staring ip is {client_ip}',
                'joe19940422@gmail.com',
                ['joe19940422@gmail.com'],  # List of recipient emails
                fail_silently=False,
            )
            return HttpResponse(html_content)
        else:
            return HttpResponseForbidden(
                "Hey fei !!! You can click the 'Start' button only once within one minute. After clicking the 'Start' button, please wait for 2 minutes as the server needs time to start !!! Rate limit exceeded.")
    else:
        return HttpResponseForbidden("Unable to determine client IP address.")

def delete_vpn(country, request):
    vpn_ec2 = boto3.client('ec2', region_name=info_vpn_account[country]["region_name"])
    client_ip, _ = get_client_ip(request)
    if client_ip:
        # Define a cache key based on the client's IP address
        cache_key = f'rate_limit_{client_ip}'
        print(client_ip)

        # Check if the IP address is rate-limited
        if not cache.get(cache_key):
            # Set a cache value to indicate that the IP address is rate-limited
            cache.set(cache_key, True, 100)  # 100 seconds (1.2 minute)

            def delete_vpn_instances(instances):
                try:
                    instance_ids = [instance['InstanceId'] for instance in instances]
                    response = vpn_ec2.terminate_instances(InstanceIds=instance_ids)
                    print(f"Deleting {len(instance_ids)} running instances...")
                except Exception as e:
                    print(f"Error deleting instances: {e}")

            # Get all running instances
            running_instances = get_running_instances(country=country)
            print(running_instances)
            if running_instances is not None:
                # stop_instances(running_instances)
                delete_vpn_instances(running_instances)
            else:
                print("No running instances found.")

            return HttpResponse(html_content)
        else:
            return HttpResponseForbidden(
                "Hey fei !!! You can click the 'Start' button only once within one minute. After clicking the 'Start' button, please wait for 2 minutes as the server needs time to start !!! Rate limit exceeded.")
    else:
        return HttpResponseForbidden("Unable to determine client IP address.")

def get_running_instances(country):
    vpn_ec2 = boto3.client('ec2', region_name=info_vpn_account[country]["region_name"])
    try:
        response = vpn_ec2.describe_instances(Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']}
        ])
        reservations = response['Reservations']
        instances = []
        for reservation in reservations:
            instances.extend(reservation['Instances'])
        return instances
    except Exception as e:
        print(f"Error getting running instances: {e}")
        return None

def get_country_ip(country):
    running_instances = get_running_instances(country)
    country_ip = running_instances[0]['PublicIpAddress'] if running_instances != [] else 'no ip'
    return country_ip


def download_vpn(country, request):
    import paramiko
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    country_ip = get_country_ip(country)
    print(country_ip)
    from socket import gaierror
    try:
        ssh_client.connect(hostname=country_ip, username='ubuntu', key_filename=f'/home/ubuntu/{country}.pem')
    except (gaierror, paramiko.ssh_exception.NoValidConnectionsError) as e:
        if str(e).startswith('[Errno -2] Name or service not known'):
            return HttpResponseForbidden("Unable to vpn Name or service not known.")
        else:
            return HttpResponseForbidden("Unable to vpn.")
    sftp_client = ssh_client.open_sftp()
    local_path = f'/home/ubuntu/fei_{country}.conf'
    try:
        sftp_client.get(f'/home/ubuntu/fei_{country}.conf', local_path)
    except FileNotFoundError:
        return HttpResponseForbidden("vpn not installed you need to wait few mins and try again !!!")
    sftp_client.close()
    ssh_client.close()

    print("File downloaded successfully!")
    timestamp = datetime.now().strftime('%y%m%d-%H-%M-%S')
    with open(local_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/conf')
        filename = f"{local_path.split('/')[-1].replace('.conf', '')}-{timestamp}.conf"
        print(filename)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


def start_regina_vpn_common(request, regina_ec2_client, regina_instance_status, regina_instance_id,  delay):
    if regina_instance_status != 'not running':
        return HttpResponse(html_content_vpn_already_started)
    ## schedule a job to stop vpn server
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/034847449190/my-vpn'
    message_body = {
        'instance_id': regina_instance_id,
        'start_time': timezone.now().isoformat(),
        'total_delay': delay  # 1 hours in seconds
    }
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_body),
        DelaySeconds=900
    )
    client_ip, _ = get_client_ip(request)
    if client_ip:
        # Define a cache key based on the client's IP address
        cache_key = f'rate_limit_{client_ip}'
        print(client_ip)

        # Check if the IP address is rate-limited
        if not cache.get(cache_key):
            # Set a cache value to indicate that the IP address is rate-limited
            cache.set(cache_key, True, 100)  # 100 seconds (1.2 minute)
            send_mail(
                f'VPN(regina): is Staring {delay/3600} h ',
                f'VPN(regina): is Staring ip is {client_ip}',
                'joe19940422@gmail.com',
                ['joe19940422@gmail.com'],  # List of recipient emails
                fail_silently=False,
            )

            # Start the instance
            regina_ec2_client.start_instances(InstanceIds=[regina_instance_id])
            regina_instance_status = 'starting'

            return HttpResponse(html_content)
        else:
            return HttpResponseForbidden(
                "Hey regina !!! You can click the 'Start' button only once within one minute. After clicking the 'Start' button, please wait for 2 minutes as the server needs time to start !!! Rate limit exceeded.")
    else:
        return HttpResponseForbidden("Unable to determine client IP address.")

def aws_page(request):
    regina_ec2_client = boto3.client('ec2', region_name='ap-southeast-1')
    regina_instance_id = 'i-073e0b3347292a1ac'
    regina_response = regina_ec2_client.describe_instance_status(
        InstanceIds=[regina_instance_id]
    )

    try:  # Extract the instance status
        regina_instance_status = regina_response['InstanceStatuses'][0]['InstanceState']['Name']
    except (BotoCoreError, ClientError, IndexError) as e:
        # Handle any errors that occur during API call or instance status retrieval
        regina_instance_status = 'not running'

    try:
        regina_response = regina_ec2_client.describe_instances(
            InstanceIds=[regina_instance_id]
        )
        if 'PublicIpAddress' in regina_response['Reservations'][0]['Instances'][0]:
            regina_instance_ip = regina_response['Reservations'][0]['Instances'][0]['PublicIpAddress']
        else:
            regina_instance_ip = 'Not assigned'
    except (BotoCoreError, ClientError, IndexError) as e:
        # Handle any errors that occur during API call or IP retrieval
        regina_instance_ip = 'unknown'

    taiwan_ip = get_country_ip(country='taiwan')
    us_ip = get_country_ip(country='us')
    hk_ip = get_country_ip(country='hk')

    now = datetime.now()
    first_day_next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
    last_day_current_month = first_day_next_month - timedelta(days=1)
    first_day = now.replace(day=1).strftime('%Y-%m-%d')
    last_day = last_day_current_month.strftime('%Y-%m-%d')
    today = datetime.now().date().strftime('%Y-%m-%d')

    openvpn_amount = 6 * 1.25


    if request.method == 'POST':
        if 'start_regina_vpn' in request.POST:
            client_ip, _ = get_client_ip(request)
            if client_ip:
                # Define a cache key based on the client's IP address
                cache_key = f'rate_limit_{client_ip}'
                print(client_ip)

                # Check if the IP address is rate-limited
                if not cache.get(cache_key):
                    # Set a cache value to indicate that the IP address is rate-limited
                    cache.set(cache_key, True, 100)  # 100 seconds (1.2 minute)
                    send_mail(
                        'VPN(regina): is Staring',
                        f'VPN(regina): is Staring ip is {client_ip}',
                        'joe19940422@gmail.com',
                        ['joe19940422@gmail.com'],  # List of recipient emails
                        fail_silently=False,
                    )

                    month = datetime.now().date().strftime('%m')
                    day = datetime.now().date().strftime('%d')
                    if (month != '02' and day == '30') or (month == '02' and day == '28'):
                        subject = 'Bill for *** Service'
                        message = f"Dear Regina from {first_day} to {today}, your *** bill costs {openvpn_amount} $"
                        from_email = 'joe19940422@gmail.com'
                        recipient_list = ['1738524677@qq.com']

                        send_mail(
                            subject,
                            message,
                            from_email,
                            recipient_list,
                            fail_silently=False,
                        )

                    # Start the instance
                    regina_ec2_client.start_instances(InstanceIds=[regina_instance_id])
                    regina_instance_status = 'starting'

                    return HttpResponse(html_content)
                else:
                    return HttpResponseForbidden(
                        "Hey regina !!! You can click the 'Start' button only once within one minute. After clicking the 'Start' button, please wait for 2 minutes as the server needs time to start !!! Rate limit exceeded.")
            else:
                return HttpResponseForbidden("Unable to determine client IP address.")
        elif 'stop_regina_vpn' in request.POST:
            client_ip, _ = get_client_ip(request)
            # Stop the instance
            send_mail(
                'VPN(regina): is Stoping',
                f'VPN(regina): is Stoping ip: {client_ip}',
                'joe19940422@gmail.com',
                ['joe19940422@gmail.com'],  # List of recipient emails
                fail_silently=False,
            )
            regina_ec2_client.stop_instances(InstanceIds=[regina_instance_id])
            regina_instance_status = 'stopping'
            return HttpResponse(html_content)

        if 'download_config_email' in request.POST:
            if regina_instance_ip == 'Not assigned':
                return HttpResponse(html_content_vpn_not_already)
            timestamp = datetime.now().strftime('%y%m%d-%H-%M-%S')
            new_file_path = f'/root/regina-{timestamp}.ovpn'
            config_file_path = '/root/regina.ovpn'
            with open(config_file_path, 'r') as file:
                lines = file.readlines()

            for line in lines:
                if line.startswith('# OVPN_ACCESS_SERVER_PROFILE='):
                    # Extract the IP address from the line
                    parts = line.split('@')
                    if len(parts) == 2:
                        ip_address = parts[1].strip()
                        break  # Stop searching once IP address is found

            with open(config_file_path, 'r') as file:
                config_content = file.read()

            updated_config_content = config_content.replace(ip_address, regina_instance_ip)
            with open(new_file_path, 'w') as file:
                file.write(updated_config_content)

            email = EmailMessage(
                'VPN(regina): new config !',
                f'VPN(regina): new config  Please download this file and open it with openvpn ! ',
                'joe19940422@gmail.com',
                ['joe19940422@gmail.com', '1738524677@qq.com', '949936589@qq.com'],  # List of recipient emails
            )
            email.attach_file(new_file_path)
            email.send()

        if 'download_config_local' in request.POST:
            if regina_instance_ip == 'Not assigned':
                return HttpResponse(html_content_vpn_not_already)
            timestamp = datetime.now().strftime('%y%m%d-%H-%M-%S')
            new_file_path = f'/root/regina-{timestamp}.ovpn'
            config_file_path = '/root/regina.ovpn'
            with open(config_file_path, 'r') as file:
                lines = file.readlines()

            for line in lines:
                if line.startswith('# OVPN_ACCESS_SERVER_PROFILE='):
                    # Extract the IP address from the line
                    parts = line.split('@')
                    if len(parts) == 2:
                        ip_address = parts[1].strip()
                        break  # Stop searching once IP address is found

            with open(config_file_path, 'r') as file:
                config_content = file.read()

            updated_config_content = config_content.replace(ip_address, regina_instance_ip)
            with open(new_file_path, 'w') as file:
                file.write(updated_config_content)

            with open(new_file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='application/ovpn')
                response['Content-Disposition'] = f'attachment; filename={new_file_path.split("/")[-1]}'
                return response

        delay_map = {
            'start_regina_vpn_one_hour': 3600,
            'start_regina_vpn_two_hour': 7200,
            'start_regina_vpn_three_hour': 10800,
            'start_regina_vpn_four_hour': 14400,
            'start_regina_vpn_six_hour':  21600
        }

        if request.POST:
            for button_name, delay in delay_map.items():
                if button_name in request.POST:
                    return start_regina_vpn_common(request, regina_ec2_client, regina_instance_status,
                                                   regina_instance_id, delay=delay)


        if 'start_taiwan_vpn' in request.POST:
            start_vpn(country='taiwan', request=request)

        if 'start_us_vpn' in request.POST:
            start_vpn(country='us', request=request)

        if 'start_hk_vpn' in request.POST:
            start_vpn(country='hk', request=request)

        if 'delete_taiwan_vpn' in request.POST:
            delete_vpn(country='taiwan', request=request)

        if 'delete_us_vpn' in request.POST:
            delete_vpn(country='us', request=request)

        if 'delete_hk_vpn' in request.POST:
            delete_vpn(country='hk', request=request)
        #todo
        if 'download_taiwan_config' in request.POST:
            download_vpn(country='taiwan', request=request)

        if 'download_us_config' in request.POST:
            download_vpn(country='us', request=request)

        if 'download_hk_config' in request.POST:
            download_vpn(country='hk', request=request)

    return render(request, 'blog/aws.html',
                  {
                   'regina_instance_status': regina_instance_status,
                   'regina_instance_ip': regina_instance_ip,
                   'taiwan_ip': taiwan_ip,
                   "hk_ip": hk_ip,
                   "us_ip": us_ip
                   })