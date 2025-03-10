# -*- coding: utf-8 -*-

import requests
import json

def login(base_url, username, password) -> dict:
    session = requests.Session()
    session.auth = (username, password)
    headers = {'Content-Type': 'application/json'}
    base_api_url = f"{base_url}/rest/api"
    try:
        user_url = f"{base_api_url}/user/current"
        response = session.get(user_url, headers=headers)
        if response.status_code != 200:
            return {"success": False, "message": f"登录失败，错误代码: {response.status_code}", "details": response.text}
    except requests.RequestException as e:
        return {"success": False, "message": "请求失败", "details": str(e)}
    return {"success": True, "message": "登录成功", "session": session}

def get_page_content(base_url, username, password, pageId) -> dict:
    session = login(base_url, username, password)
    if not session["success"]:
        return session
    session = session["session"]
    headers = {'Content-Type': 'application/json'}
    try:
        search_url = f"{base_url}/content/{pageId}?expand=body.storage"
        response = session.get(search_url, headers=headers)
        if response.status_code == 200:
            res_json = response.json()
            results = res_json['body']['storage']['value']
            title = res_json['title']
            return {"results": results, "title": title}
        else:
            results = f"搜索失败，错误代码: {response.status_code}"
            title = "获取文档异常！"
        return {"results": results, "title": title}
    except requests.RequestException as e:
        return {"success": False, "message": "请求失败", "details": str(e)}
