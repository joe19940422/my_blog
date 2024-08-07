# -*- coding: utf-8 -*-
# Create your views here.

import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django_blog.util import PageInfo
from blog.models import Article, Comment, City, Visitor, Contact
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from newsapi import NewsApiClient
from googletrans import Translator
from django.core.mail import send_mail
from botocore.exceptions import BotoCoreError, ClientError
from datetime import datetime, timedelta


translator = Translator()


def get_page(request):
    page_number = request.GET.get("page")
    return 1 if not page_number or not page_number.isdigit() else int(page_number)


def index(request):
    _blog_list = Article.objects.all().order_by('-date_time')[0:5]
    _blog_hot = Article.objects.all().order_by('-view')[0:6]
    return render(request, 'blog/index.html', {"blog_list": _blog_list, "blog_hot": _blog_hot})


def blog_list(request):
    """
    列表
    :param request:
    :return:
    """
    page_number = get_page(request)
    blog_count = Article.objects.count()
    page_info = PageInfo(page_number, blog_count)
    _blog_list = Article.objects.all()[page_info.index_start: page_info.index_end]
    return render(request, 'blog/list.html', {"blog_list": _blog_list, "page_info": page_info})


def category(request, name):
    """
    分类
    :param request:
    :param name:
    :return:
    """
    page_number = get_page(request)
    blog_count = Article.objects.filter(category__name=name).count()
    page_info = PageInfo(page_number, blog_count)
    _blog_list = Article.objects.filter(category__name=name)[page_info.index_start: page_info.index_end]
    return render(request, 'blog/category.html', {"blog_list": _blog_list, "page_info": page_info,
                                                  "category": name})


def tag(request, name):
    """
    标签
    :param request:
    :param name
    :return:
    """
    page_number = get_page(request)
    blog_count = Article.objects.filter(tag__tag_name=name).count()
    page_info = PageInfo(page_number, blog_count)
    _blog_list = Article.objects.filter(tag__tag_name=name)[page_info.index_start: page_info.index_end]
    return render(request, 'blog/tag.html', {"blog_list": _blog_list,
                                             "tag": name,
                                             "page_info": page_info})


def archive(request):
    """
    文章归档
    :param request:
    :return:
    """
    _blog_list = Article.objects.values("id", "title", "date_time").order_by('-date_time')
    archive_dict = {}
    for blog in _blog_list:
        pub_month = blog.get("date_time").strftime("%Y-%m-")
        if pub_month in archive_dict:
            archive_dict[pub_month].append(blog)
        else:
            archive_dict[pub_month] = [blog]
    data = sorted([{"date": _[0], "blogs": _[1]} for _ in archive_dict.items()], key=lambda item: item["date"],
                  reverse=True)
    return render(request, 'blog/archive.html', {"data": data})


def message(request):
    return render(request, 'blog/message_board.html', {"source_id": "message"})


@csrf_exempt
def get_comment(request):
    """
    接收畅言的评论回推， post方式回推
    :param request:
    :return:
    """
    arg = request.POST
    data = arg.get('data')
    data = json.loads(data)
    title = data.get('title')
    url = data.get('url')
    source_id = data.get('sourceid')
    if source_id not in ['message']:
        article = Article.objects.get(pk=source_id)
        article.commenced()
    comments = data.get('comments')[0]
    content = comments.get('content')
    user = comments.get('user').get('nickname')
    Comment(title=title, source_id=source_id, user_name=user, url=url, comment=content).save()
    return JsonResponse({"status": "ok"})


def detail(request, pk):
    """
    博文详情
    :param request:
    :param pk:
    :return:
    """
    blog = get_object_or_404(Article, pk=pk)
    blog.viewed()
    return render(request, 'blog/detail.html', {"blog": blog})


def search(request):
    """
    搜索
    :param request:
    :return:
    """
    key = request.GET['key']
    page_number = get_page(request)
    blog_count = Article.objects.filter(title__icontains=key).count()
    page_info = PageInfo(page_number, blog_count)
    _blog_list = Article.objects.filter(title__icontains=key)[page_info.index_start: page_info.index_end]
    return render(request, 'blog/search.html', {"blog_list": _blog_list, "pages": page_info, "key": key})


def page_not_found_error(request, exception):
    return render(request, "404.html", status=404)


def page_error(request):
    return render(request, "404.html", status=500)


def China(request):
    newsapi = NewsApiClient(api_key="0aaf327d9eed48e2adb87d10f7946650")
    topheadlines = newsapi.get_top_headlines(country='cn', language='zh')

    articles = topheadlines['articles']

    desc = []
    news = []
    img = []
    publishedAt = []
    author = []
    for i in range(len(articles)):
        myarticles = articles[i]

        news.append(myarticles['title'])
        desc.append(myarticles['description'])
        #result = translator.translate(myarticles['description'], dest='zh-tw').text
        desc.append(myarticles['description'])
        img.append(myarticles['urlToImage'])
        publishedAt.append(myarticles['publishedAt'])
        author.append(myarticles['author'])
    mylist = zip(news,desc,publishedAt,author,img)
    return render(request, 'china.html', context={"mylist":mylist})


def bbc(request):
    newsapi = NewsApiClient(api_key="0aaf327d9eed48e2adb87d10f7946650")
    topheadlines = newsapi.get_top_headlines(sources='al-jazeera-english')

    articles = topheadlines['articles']

    desc = []
    news = []
    img = []
    publishedAt = []
    author = []

    for i in range(len(articles)):
        myarticles = articles[i]

        news.append(myarticles['title'])
        desc.append(myarticles['description'])
        img.append(myarticles['urlToImage'])
        publishedAt.append(myarticles['publishedAt'])
        author.append(myarticles['author'])
    mylist = zip(news, desc, publishedAt, author, img)
    print(request)
    return render(request, 'bbc.html', context={"mylist": mylist})


def taiwan(request):
    newsapi = NewsApiClient(api_key="0aaf327d9eed48e2adb87d10f7946650")
    topheadlines = newsapi.get_top_headlines(country='tw', language='zh')

    articles = topheadlines['articles']

    desc = []
    news = []
    img = []
    publishedAt = []
    author = []
    for i in range(len(articles)):
        myarticles = articles[i]

        news.append(myarticles['title'])
        desc.append(myarticles['description'])
        img.append(myarticles['urlToImage'])
        publishedAt.append(myarticles['publishedAt'])
        author.append(myarticles['author'])
    mylist = zip(news, desc, publishedAt, author, img)
    return render(request, 'taiwan.html', context={"mylist": mylist})


def dutch(request):
    newsapi = NewsApiClient(api_key="0aaf327d9eed48e2adb87d10f7946650")
    topheadlines = newsapi.get_top_headlines(country='nl', language='nl')

    articles = topheadlines['articles']

    desc = []
    news = []
    img = []
    publishedAt = []
    author = []
    for i in range(len(articles)):
        myarticles = articles[i]

        news.append(myarticles['title'])
        desc.append(myarticles['description'])
        #result = translator.translate(myarticles['description'], dest='zh-tw').text
        img.append(myarticles['urlToImage'])
        publishedAt.append(myarticles['publishedAt'])
        author.append(myarticles['author'])
    mylist = zip(news, desc, publishedAt, author, img)
    return render(request, 'dutch.html', context={"mylist":mylist})


def aboutme(request):
    return render(request, 'aboutme/Home.html')


def pie_chart(request):
    labels = []
    data = []

    queryset = City.objects.order_by('-population')[:5]
    print(queryset)
    """
    <QuerySet [<City: City object (1)>, <City: City object (2)>, <City: City object (3)>, <City: City object (4)>, <City: City object (5)>]>
    """
    print(type(queryset))
    for city in queryset:
        labels.append(city.name)
        data.append(city.population)
    demo = {
        'labels': labels,
        'data': data,
    }
    print(demo)
    return render(request, 'blog/pie_chart.html', {
        'labels': labels,
        'data': data,
    })


def visitor_chart(request):
    labels = []
    data = []
    # select count(DISTINCT ip), v.country_code  from visitor v group by v.country_code
    queryset = Visitor.objects.exclude(country_code__isnull=True).values("country_code").annotate(Count=Count("ip", distinct=True)).order_by("-Count")
    print(queryset)
    print(type(queryset))
    """
    <QuerySet [{'country_code': 'TW', 'Count': 1}, {'country_code': 'NL', 'Count': 1}, {'country_code': '', 'Count': 1}, {'country_code': 'UA', 'Count': 1}, {'country_code': 'RU', 'Count': 1}, {'country_code': 'DE', 'Count': 2}]>
    """
    for result in queryset:
        labels.append(result['country_code'])
        data.append(result['Count'])
    demo = {
        'labels': labels,
        'data': data,
    }
    print(demo)
    return render(request, 'blog/visitor_chart.html', {
        'labels': labels,
        'data': data,
    })


from boto3.dynamodb.conditions import Key
from decimal import Decimal


def get_currency_data():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'CurrencyExchangeRates'

    table = dynamodb.Table(table_name)

    # response = table.query(
    #     KeyConditionExpression=Key('currency_code').eq('USD') & Key('timestamp').gt(0),
    #     ProjectionExpression='currency_code, exchange_rate'  # Specify attributes to retrieve
    # )
    response = table.scan()
    items = response['Items']
    # Sort items by 'exchange_rate' using a lambda function
    items_sorted = sorted(items, key=lambda x: Decimal(x['exchange_rate']))
    labels = []
    data = []
    tms = []
    for item in items_sorted:
        labels.append(item['currency_code'])
        data.append(float(item['exchange_rate']))  # Convert exchange_rate to float
        tms.append(item['timestamp'])

    table2 = dynamodb.Table('CurrencyExchangeRates2')

    response = table2.scan(FilterExpression=Key('currency_code').eq('EUR'))
    items = response['Items']
    for item in items:
        rates_sorted = sorted(item['rates'], key=lambda x: x['timestamp'])
        item['rates'] = rates_sorted
    parse_data = items[0]['rates']
    labels2 = []
    data2 = []
    for item in parse_data:
        labels2.append(item['timestamp'].split('.')[0])
        data2.append(float(item['rate']))
    return labels, data, tms, items_sorted, labels2, data2


def currency_chart(request):
    # Get currency data from AWS DynamoDB
    labels, data, tms, items_sorted, labels2, data2 = get_currency_data()
    print(labels)
    print(data)
    return render(request, 'blog/currency_chart.html', {
        'labels': labels,
        'data': data,
        'tms': tms[0],
        'items_sorted': items_sorted,
        'labels2': labels2,
        'data2': data2
    })


def get_weather_data(city_name):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'weather'

    table = dynamodb.Table(table_name)
    response = table.scan(FilterExpression=Key('name').eq(city_name))
    items = response['Items']
    print(items)
    if not items:
        return None, None, None, None, None, None, None, None, None
    # Sort items by 'exchange_rate' using a lambda function
    items_sorted = sorted(items, key=lambda x: x['dt'],reverse=True)[0]
    visibility = items_sorted['visibility']
    lon = items_sorted['coord']['lon']
    lat = items_sorted['coord']['lat']
    wind = items_sorted['wind']
    name = items_sorted['name']
    sys = items_sorted['sys']
    main = items_sorted['main']
    weather_time = items_sorted['tms']
    insert_dynamdb_time = items_sorted['insert_time']

    return visibility, lon, lat, wind, name, sys, main, weather_time, insert_dynamdb_time


def weather(request):
    city_name = request.GET.get('city', 'Rotterdam')  # Default to Rotterdam
    # Get weather data from AWS DynamoDB
    visibility, lon, lat, wind, name, sys, main, weather_time, insert_dynamdb_time = get_weather_data(city_name)

    return render(request, 'blog/weather.html', {
        'visibility': visibility,
        'lon': lon,
        'lat': lat,
        'wind': wind,
        'name': name,
        'sys': sys,
        'main': main,
        'weather_time': weather_time,
        'insert_dynamdb_time': insert_dynamdb_time,
        'cities': ['Rotterdam', 'Taipei']  # List of cities
    })


from .forms import ContactForm


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            guest_num = form.cleaned_data['guest_num']
            event_type = form.cleaned_data['event_type']
            """
            ("1", "party/feest"),
            ("2", "ceremony/ceremonie"),
            ("3", "ceremony and party/ ceremonie en feest"),
            ("4", "Can't join/ Kan niet meedoen"),
            """
            form.save()
            if event_type == '1':
                event = 'party'
            if event_type == '2':
                event = 'ceremony'
            if event_type == '3':
                event = 'ceremony and party'
            if event_type == '4':
                event = 'Cant join'
            send_mail(
                'New Contact Form Submission',
                f'Name: {name}\nEmail: {email}\nMessage: {message}\nGuest_num: {guest_num}\nEvent_type:{event}',
                'joe19940422@gmail.com',
                ['joe19940422@gmail.com'],  # List of recipient emails
                fail_silently=False,
            )
            send_mail(
                'New Contact Form Submission',
                f'Name: {name}\nEmail: {email}\nMessage: {message}\nGuest_num: {guest_num}\nEvent_type:{event}',
                'lisannedoff@hotmail.com',
                ['lisannedoff@hotmail.com'],  # List of recipient emails
                fail_silently=False,
            )
            send_mail(
                'Thank you for your reply[Automatic reply]',
                f'Dear {name},\n\nThank you for your message.\n\nBest regards,\nPengfei and Lisanne',
                'joe19940422@gmail.com',
                [email],  # Use the extracted email address as the recipient
                fail_silently=False,
            )

            return render(request, 'blog/success.html')
    else:
        form = ContactForm()
    result = Contact.objects.filter(event_type='2').count()

    context = {'form': form, 'num': 400-result}
    return render(request, 'blog/contact.html', context)


def rsvp(request):

    queryset = Contact.objects.all()
    print(queryset)

    return render(request, 'blog/rsvp.html', {
        'queryset': queryset
    })

import boto3


from ipware import get_client_ip
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseForbidden


html_content = """
    <html>
    <head>
        <title>Redirecting</title>
        <script type="text/javascript">
            // Redirect to Google after a delay
            setTimeout(function() {
                window.location.href = "http://pengfeiqiao.com/blog/aws/";
            }, 8000); // 8000 milliseconds = 8 seconds
        </script>
    </head>
    <body>
        <p>請稍候 8 秒，我們將進入主頁，請在 2 分鐘後下載您的配置.</p>
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
def aws_page(request):
    # Initialize Boto3 client
    ec2_client = boto3.client('ec2', region_name='us-east-1')

    # Retrieve instance status
    # instance_id = 'i-07360808c3dc6fed2'
    # response = ec2_client.describe_instance_status(
    #     InstanceIds=[instance_id]
    # )
    #
    # # Extract the instance status
    # try:  # Extract the instance status
    #     instance_status = response['InstanceStatuses'][0]['InstanceState']['Name']
    # except (BotoCoreError, ClientError, IndexError) as e:
    #     # Handle any errors that occur during API call or instance status retrieval
    #     instance_status = 'not running'
    # if request.method == 'POST':
    #     if 'start_instance' in request.POST:
    #         send_mail(
    #             'EC2: is Staring',
    #             f'EC2: is Staring',
    #             'joe19940422@gmail.com',
    #             ['joe19940422@gmail.com'],  # List of recipient emails
    #             fail_silently=False,
    #         )
    #         # Start the instance
    #         ec2_client.start_instances(InstanceIds=[instance_id])
    #         instance_status = 'starting'
    #
    #     elif 'stop_instance' in request.POST:
    #         # Stop the instance
    #         send_mail(
    #             'EC2: is Stoping',
    #             f'EC2: is Stoping',
    #             'joe19940422@gmail.com',
    #             ['joe19940422@gmail.com'],  # List of recipient emails
    #             fail_silently=False,
    #         )
    #         ec2_client.stop_instances(InstanceIds=[instance_id])
    #         instance_status = 'stopping'
    #
    # try:
    #     response = ec2_client.describe_instances(
    #         InstanceIds=[instance_id]
    #     )
    #     if 'PublicIpAddress' in response['Reservations'][0]['Instances'][0]:
    #         instance_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
    #     else:
    #         instance_ip = 'Not assigned'
    # except (BotoCoreError, ClientError, IndexError) as e:
    #     # Handle any errors that occur during API call or IP retrieval
    #     instance_ip = 'unknown'

    ##########################################################################
    ##########################################################################
    ##########################################################################
    ##########################################################################
    ##########################################################################
    ##########################################################################
    vpn_ec2_client = boto3.client('ec2', region_name='ap-northeast-1')

    # Retrieve instance status
    vpn_instance_id = 'i-02b099b8eaecb4288'
    vpn_response = vpn_ec2_client.describe_instance_status(
        InstanceIds=[vpn_instance_id]
    )

    # Extract the instance status
    try:  # Extract the instance status
        vpn_instance_status = vpn_response['InstanceStatuses'][0]['InstanceState']['Name']
    except (BotoCoreError, ClientError, IndexError) as e:
        # Handle any errors that occur during API call or instance status retrieval
        vpn_instance_status = 'not running'
    if request.method == 'POST':
        if 'start_vpn' in request.POST:
            send_mail(
                'VPN: is Staring',
                f'VPN: is Staring',
                'joe19940422@gmail.com',
                ['joe19940422@gmail.com'],  # List of recipient emails
                fail_silently=False,
            )
            # Start the instance
            vpn_ec2_client.start_instances(InstanceIds=[vpn_instance_id])
            vpn_instance_status = 'starting'

        elif 'stop_vpn' in request.POST:
            # Stop the instance
            send_mail(
                'VPN: is Stoping',
                f'VPN: is Stoping',
                'joe19940422@gmail.com',
                ['joe19940422@gmail.com'],  # List of recipient emails
                fail_silently=False,
            )
            vpn_ec2_client.stop_instances(InstanceIds=[vpn_instance_id])
            vpn_instance_status = 'stopping'

    try:
        vpn_response = vpn_ec2_client.describe_instances(
            InstanceIds=[vpn_instance_id]
        )
        if 'PublicIpAddress' in vpn_response['Reservations'][0]['Instances'][0]:
            vpn_instance_ip = vpn_response['Reservations'][0]['Instances'][0]['PublicIpAddress']
        else:
            vpn_instance_ip = 'Not assigned'
    except (BotoCoreError, ClientError, IndexError) as e:
        # Handle any errors that occur during API call or IP retrieval
        vpn_instance_ip = 'unknown'
    ###################################################################################
    ###################################################################################
    #regina vpn
    regina_ec2_client = boto3.client('ec2', region_name='ap-southeast-1')

    # Retrieve instance status
    regina_instance_id = 'i-073e0b3347292a1ac'
    regina_response = regina_ec2_client.describe_instance_status(
        InstanceIds=[regina_instance_id]
    )

    bill_client = boto3.client('ce', region_name='ap-southeast-1',
                               )
    now = datetime.now()
    first_day_next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
    last_day_current_month = first_day_next_month - timedelta(days=1)
    first_day = now.replace(day=1).strftime('%Y-%m-%d')
    last_day = last_day_current_month.strftime('%Y-%m-%d')
    today = datetime.now().date().strftime('%Y-%m-%d')
    time_period = {
        'Start': first_day,
        'End': last_day
    }
    # response = bill_client.get_cost_and_usage(
    #     TimePeriod=time_period,
    #     Granularity='MONTHLY',
    #     Metrics=['BlendedCost'],
    #     Filter={
    #         'Dimensions': {
    #             "Key": "REGION", "Values": ["ap-southeast-1"]
    #         }
    #     }
    # )
    openvpn_amount = 6 * 1.25
    #openvpn_amount = float(response['ResultsByTime'][0]['Total']['BlendedCost']['Amount']) * 1.25
    # Extract the instance status
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
                    return HttpResponseForbidden("Hey regina !!! You can click the 'Start' button only once within one minute. After clicking the 'Start' button, please wait for 2 minutes as the server needs time to start !!! Rate limit exceeded.")
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
        if 'download_config' in request.POST:
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
            with open(config_file_path, 'w') as file:
                file.write(updated_config_content)
            from django.core.mail import EmailMessage
            email = EmailMessage(
                'VPN(regina): new config !',
                f'VPN(regina): new config  Please download this file and open it with openvpn ! ',
                'joe19940422@gmail.com',
                ['joe19940422@gmail.com', '1738524677@qq.com', '949936589@qq.com'],  # List of recipient emails
            )
            email.attach_file(config_file_path)
            email.send()

        if 'start_regina_vpn_one_hour' in request.POST:
            if regina_instance_status != 'not running':
                return HttpResponse(html_content_vpn_already_started)
            ## schedule a job to stop vpn server
            from django.utils import timezone
            sqs = boto3.client('sqs', region_name='us-east-1')
            queue_url = 'https://sqs.us-east-1.amazonaws.com/034847449190/my-vpn'
            message_body = {
                'instance_id': regina_instance_id,
                'start_time': timezone.now().isoformat(),
                'total_delay': 3600  # 1 hours in seconds
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
                        'VPN(regina): is Staring 1 hour ',
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

        if 'start_regina_vpn_two_hour' in request.POST:
            ## schedule a job to stop vpn server
            from django.utils import timezone
            sqs = boto3.client('sqs', region_name='us-east-1')
            queue_url = 'https://sqs.us-east-1.amazonaws.com/034847449190/my-vpn'
            message_body = {
                'instance_id': regina_instance_id,
                'start_time': timezone.now().isoformat(),
                'total_delay': 7200  # 2 hours in seconds
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
                        'VPN(regina): is Staring 2 hour ',
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

        if 'start_regina_vpn_three_hour' in request.POST:
            ## schedule a job to stop vpn server
            from django.utils import timezone
            sqs = boto3.client('sqs', region_name='us-east-1')
            queue_url = 'https://sqs.us-east-1.amazonaws.com/034847449190/my-vpn'
            message_body = {
                'instance_id': regina_instance_id,
                'start_time': timezone.now().isoformat(),
                'total_delay': 10800  # 3 hours in seconds
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
                        'VPN(regina): is Staring 3 hour ',
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

        if 'start_regina_vpn_four_hour' in request.POST:
            ## schedule a job to stop vpn server
            from django.utils import timezone
            sqs = boto3.client('sqs', region_name='us-east-1')
            queue_url = 'https://sqs.us-east-1.amazonaws.com/034847449190/my-vpn'
            message_body = {
                'instance_id': regina_instance_id,
                'start_time': timezone.now().isoformat(),
                'total_delay': 14400  # 4 hours in seconds
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
                        'VPN(regina): is Staring 4 hour ',
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

    return render(request, 'blog/aws.html',
                  {
                   'vpn_instance_status': vpn_instance_status,
                   'vpn_instance_ip': vpn_instance_ip,
                   'regina_instance_status': regina_instance_status,
                   'regina_instance_ip': regina_instance_ip,
                   'openvpn_amount': openvpn_amount,
                   'first_day': first_day,
                   'today': today
                   })


def wedding_show(request):
    return render(request, 'wedding/picture.html', {
    })




