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


# class News():
#     def __init__(self, page, country='', language='', translate='zh-tw'):
#         self.page = page
#         self.country = country
#         self.language = language
#         self.translate = translate
#
#     @classmethod
#     def new(cls,request):
#         newsapi = NewsApiClient(api_key="0aaf327d9eed48e2adb87d10f7946650")
#         if cls.page == 'bbc':
#             topheadlines = newsapi.get_top_headlines(sources='al-jazeera-english')
#         else:
#             topheadlines = newsapi.get_top_headlines(country=cls.country, language=cls.language)
#         articles = topheadlines['articles']
#
#         desc = []
#         news = []
#         img = []
#         publishedAt = []
#         author = []
#         for i in range(len(articles)):
#             myarticles = articles[i]
#
#             news.append(myarticles['title'])
#             if cls.page in ['bbc','taiwan']:
#                 desc.append(myarticles['description'])
#             else:
#                 result = translator.translate(myarticles['description'], dest='zh-tw').text
#                 desc.append(result)
#             img.append(myarticles['urlToImage'])
#             publishedAt.append(myarticles['publishedAt'])
#             author.append(myarticles['author'])
#         mylist = zip(news, desc, publishedAt, author, img)
#         print(request)
#         return render(request, cls.page+'html', context={"mylist": mylist})
#
#
# China = News(page='china',country='cn',language='zh')
# bbc = News(page='bbc')
# taiwan = News(page='taiwan',country='cn',language='zh-tw')
# dutch = News(page='dutch',country='cn',language='nl')


def China(request):
    newsapi = NewsApiClient(api_key="0aaf327d9eed48e2adb87d10f7946650")
    topheadlines = newsapi.get_top_headlines(country='cn',language='zh')

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
    mylist = zip(news, desc,publishedAt,author, img)
    print(request)
    return render(request, 'bbc.html', context={"mylist": mylist})


def taiwan(request):
    newsapi = NewsApiClient(api_key="0aaf327d9eed48e2adb87d10f7946650")
    topheadlines = newsapi.get_top_headlines(country='tw',language='zh')

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
    mylist = zip(news,desc,publishedAt,author,img)
    return render(request, 'taiwan.html', context={"mylist":mylist})


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
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    for result in queryset:
        labels.append(result['country_code'])
        data.append(result['Count'])
    demo ={
        'labels': labels,
        'data': data,
    }
    print(demo)
    return render(request, 'blog/visitor_chart.html', {
        'labels': labels,
        'data': data,
    })

from .forms import ContactForm


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'blog/success.html')
    form = ContactForm()
    result = Contact.objects.filter(event_type='2').count()

    context = {'form': form, 'num': 30-result}
    return render(request, 'blog/contact.html', context)

