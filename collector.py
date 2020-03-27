import os
import json
import shelve

import requests as r
import pandas as pd


session = False
URL = "https://app.finchina.com/finchinaAPP/getMonitorInfo2.action"
path = os.path.dirname(__file__)


def login():
    login_url = "https://app.finchina.com/finchinaAPP/login.action"
    head = {"Accept": "*/*", "Accept-Encoding": "gzip;q=1.0, compress;q=0.5",
            "Accept-Language": "zh-Hans-CN;q=1.0, en-CN;q=0.9", "Connection": "keep-alive", "Content-Length": "182",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8", "Host": "app.finchina.com",
            "User-Agent": "FCPublicOpinionSystem/4.6.0 (news.finchina.com; build:607; iOS 13.4.0) Alamofire/4.7.2",
            "client": "finchina", "system": "v4.6.0.607,13.4,iOS,iPhone,iPhone,iPhone11,2"}
    with shelve.open('data') as f:
        payload = f[os.path.join(path, 'login_payload')]
    resp = r.post(login_url, data=payload, headers=head)
    data = check_err(resp)
    token = data['token']
    dump_token(token)
    return token


def dump_token(token):
    with shelve.open(os.path.join(path, 'data')) as f:
        f['token'] = token


def load_token():
    with shelve.open(os.path.join(path,'data')) as f:
        token = f.get('token', None)
    return token


def validate_token():
    try:
        token = load_token()
        get('1011383628', token)
    except ConnectionRefusedError:
        token = login()
    finally:
        global session
        session = True
    return token


def check_err(resp):
    err = resp.status_code  # 检查网络请求
    if err != 200:
        raise ConnectionError(f"访问企业预警通网站错误，错误码为{err}")
    data = resp.text
    data = json.loads(data)
    err = data['returncode']
    if err != 0:
        raise ConnectionRefusedError(data['info'])
    data = data['data']
    return data


def get(company_id, token, page=1):
    """通过公司ID获取负面消息"""
    skip = (page - 1)*15
    payload = {
        'grouptype': 'company',
        'importance': 'onlynegative',
        'itemArr': company_id,
        'option': 'history',
        'skip': skip,
        'type': 'allNews'
    }
    head = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip;q=1.0, compress;q=0.5',
        'Accept-Language': 'zh-Hans-CN;q=1.0, en-CN;q=0.9',
        'Connection': 'keep-alive',
        'Host': 'app.finchina.com',
        'User-Agent': 'FCPublicOpinionSystem/4.6.0 (news.finchina.com; build:607; iOS 13.4.0) Alamofire/4.7.2',
        'client': 'finchina',
        'system': 'v4.6.0.607,13.4,iOS,iPhone,iPhone,iPhone11,2',
        'token': token
    }

    resp = r.get(URL, params=payload, headers=head)
    data = check_err(resp)
    return data


def advance_get(company_id, page=1):
    global session
    if not session:
        token = validate_token()
    else:
        token = load_token()
    data = get(company_id, token, page)
    return data


def news_url(news_id):
    url = f"https://app.finchina.com/finchinaAPP/newsDetail.html?type=news&id={news_id}"
    return url


def format_negative_news(company_id, page=1):
    data = advance_get(company_id, page)
    data = [
        {'risk': x['risk'], 'title': x['title'], 'source': x['source'], 'date': x['date'], 'url': news_url(x['id'])}
        for x in data
    ]
    data = pd.DataFrame(data)
    return data


def format_negative_news_many(company_id, pages=3):
    data = pd.DataFrame()
    for page in range(1, pages+1):
        d = format_negative_news(company_id, page)
        data = data.append(d)
    return data
