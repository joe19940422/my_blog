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
#from newsapi import NewsApiClient
from googletrans import Translator
from django.core.mail import send_mail
from botocore.exceptions import BotoCoreError, ClientError
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
from decimal import Decimal


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

    for city in queryset:
        labels.append(city.name)
        data.append(city.population)

    return render(request, 'blog/pie_chart.html', {
        'labels': labels,
        'data': data,
    })


def visitor_chart(request):
    labels = []
    data = []
    # select count(DISTINCT ip), v.country_code  from visitor v group by v.country_code
    queryset = Visitor.objects.exclude(country_code__isnull=True).values("country_code").annotate(Count=Count("ip", distinct=True)).order_by("-Count")
    """
    <QuerySet [{'country_code': 'TW', 'Count': 1}, {'country_code': 'NL', 'Count': 1}, {'country_code': '', 'Count': 1}, {'country_code': 'UA', 'Count': 1}, {'country_code': 'RU', 'Count': 1}, {'country_code': 'DE', 'Count': 2}]>
    """
    for result in queryset:
        labels.append(result['country_code'])
        data.append(result['Count'])

    return render(request, 'blog/visitor_chart.html', {
        'labels': labels,
        'data': data,
    })


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

    return render(request, 'blog/rsvp.html', {
        'queryset': queryset
    })


def wedding_show(request):
    return render(request, 'wedding/picture.html', {
    })

def taiwan_show(request):
    return render(request, 'blog/picture.html', {
    })


import pandas as pd
import awswrangler as wr
from django.shortcuts import render
from django.http import JsonResponse
import json

def ranking_view(request):
    try:
        # Replace with your S3 bucket and key
        bucket = 'snowflake-flight'
        key = 'mart/arrival_country_ranking/data_0_0_0.snappy.parquet'
        s3_path = f's3://{bucket}/{key}'

        # Read Parquet data using awswrangler
        df = wr.s3.read_parquet(s3_path)

        # Rename columns for clarity
        df.columns = ['country', 'flight_date', 'cnt']

        # Convert flight_date to datetime if needed
        df['flight_date'] = pd.to_datetime(df['flight_date'])

        # Example: Rank countries by total count for a specific date (or the latest date)
        latest_date = df['flight_date'].max()
        filtered_df = df[df['flight_date'] == latest_date].drop_duplicates()

        ranked_df = filtered_df.sort_values(by='cnt', ascending=False)
        ranked_df = ranked_df.head(12)
        # Prepare data for chart
        chart_data = {
            'labels': ranked_df['country'].tolist(),
            'values': [float(val) for val in ranked_df['cnt'].tolist()],  # Convert Decimal to float
        }
        print(chart_data)
        """
        {'labels': ['Japan', 'Japan', 'Australia', 'Australia', 'Russia', 'Russia', 'Philippines', 'Philippines', 'New Zealand', 'New Zealand', 'South Korea', 'South Korea', 'India', 'India', 'Taiwan', 'Taiwan', 'Vietnam', 'Vietnam', 'Malaysia', 'Malaysia', 'Hong Kong', 'Hong Kong', 'Singapore', 'Singapore', 'Thailand', 'Thailand', 'Kenya', 'Kenya', 'United Arab Emirates', 'United Arab Emirates', 'Morocco', 'Morocco', 'Germany', 'Azerbaijan', 'Azerbaijan', 'Germany', 'Iraq', 'Iraq'], 'values': [Decimal('113'), Decimal('113'), Decimal('81'), Decimal('81'), Decimal('39'), Decimal('39'), Decimal('33'), Decimal('33'), Decimal('28'), Decimal('28'), Decimal('26'), Decimal('26'), Decimal('22'), Decimal('22'), Decimal('20'), Decimal('20'), Decimal('19'), Decimal('19'), Decimal('18'), Decimal('18'), Decimal('11'), Decimal('11'), Decimal('10'), Decimal('10'), Decimal('9'), Decimal('9'), Decimal('8'), Decimal('8'), Decimal('7'), Decimal('7'), Decimal('3'), Decimal('3'), Decimal('2'), Decimal('2'), Decimal('2'), Decimal('2'), Decimal('1'), Decimal('1')]}

        """
        ranked_data = ranked_df.to_dict('records')
        # If you want to return json data to your frontend.
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(chart_data)

        return render(request, 'blog/ranking_template.html', {'chart_data': json.dumps(chart_data),'ranked_data': ranked_data, 'latest_date': latest_date})

    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'blog/error_template.html', {'error_message': str(e)})