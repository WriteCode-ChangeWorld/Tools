# coding=utf-8
import os
import re
import Kit
import json
import time
import Config
import urllib3
import pymysql
import requests
from requests import utils
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    config = Config.get_config()
    print("[INFO]", "Start at", Kit.str_time())

    # Check environment
    cache_path = config['BASE']['cache_path']
    os.makedirs(cache_path, exist_ok=True)
    if Kit.env_check(cache_path) is False:
        print("[ERR]", "Chrome driver run environment not found")
        return exit(1)

    # User login
    cookies = login(config)

    # Fetch archives
    session = requests.Session()
    cookies_jar = requests.utils.cookiejar_from_dict(cookies)
    session.cookies = cookies_jar
    session.headers = {"User-Agent": config['BASE']['user_agent']}

    conn = Kit.mysql_conn(config, "MYSQL")
    cursor = conn.cursor()

    for pid in range(189900, 1, -1):
        sql = "SELECT COUNT(*) FROM `cangku` WHERE `id`=%s"
        cursor.execute(sql, pid)
        count = int(cursor.fetchone()[0])
        if count == 1:
            continue

        for i in range(3):
            try:
                fetch_info(config, conn, session, pid)
                break
            except Exception as e:
                error_record(conn, pid, 000)
                Kit.print_red("RE{}".format(i))
                print(e)


def login(config):
    print("[INFO]", "Opening website")
    cache_path = config['BASE']['cache_path']
    browser = Kit.run_browser(cache_path, config['BASE']['headless'])
    browser.implicitly_wait(10)
    browser.get("https://cangku.io/login")
    form_group = browser.find_elements_by_class_name("form-group")
    form_group[0].find_element_by_tag_name("input").send_keys(config['USER']['username'])
    form_group[1].find_element_by_tag_name("input").send_keys(config['USER']['password'])
    browser.find_element_by_class_name("btn-danger").click()
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "global-announce")))
    cookies = {}
    for item in browser.get_cookies():
        cookies[item["name"]] = item["value"]

    browser.quit()
    return cookies


def fetch_info(config, conn, session, pid):
    # Fetch info data
    print("[INFO]", "Fetch page {}...".format(pid), end="")
    params = {"include": "user,tags,categories,favorited,upvoted"}
    res = session.get("https://cangku.io/api/v1/post/info?id={}".format(pid), params=params,
                      proxies=config["PROXY"], verify=False)
    if res.status_code == 403:
        error_record(conn, pid, 403)
        Kit.print_red("BAN 403")
        return False

    # Parser json
    page_data = json.loads(res.text)
    if page_data["status_code"] == 404:
        error_record(conn, pid, 404)
        Kit.print_red("ERR 404")
        return False
    elif page_data["status_code"] == 200:
        tag_name = page_data["data"]["title"].split("]")[0].split("[")[-1]
        if tag_name == page_data["data"]["title"]:
            tag_name = page_data["data"]["categories"][0]["name"]
        sql_data = {
            "pid": page_data["data"]["id"],
            "url": "https://cangku.io/archives/{}".format(pid),
            "tag": tag_name,
            "user": page_data["data"]["user_id"],
            "title": page_data["data"]["title"],
            "cover": page_data["data"]["thumb"],
            "content": page_data["data"]["content"],
            "raw_data": res.text
        }
        sql = "REPLACE INTO `cangku`(id,url,tag,user,title,cover,content,raw_data)VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor = conn.cursor()
        cursor.execute(sql, args=list(sql_data.values()))
        conn.commit()

        Kit.print_green("OK")
        print("Info: {} // {} // {}".format(pid, sql_data["tag"], sql_data["title"]))
        return True
    else:
        error_record(conn, pid, page_data["status_code"])
        Kit.print_red("ERR ???")
        print("Error status", pid, page_data["status_code"], page_data["message"])
        return False


def error_record(conn, pid, status):
    cursor = conn.cursor()
    sql = "REPLACE INTO `cangku`(id,url,tag,user,title,cover,content,raw_data)VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql, args=[pid, "https://cangku.io/archives/{}".format(pid), status, "无法访问", "", "", "", ""])
    conn.commit()


if __name__ == '__main__':
    main()
