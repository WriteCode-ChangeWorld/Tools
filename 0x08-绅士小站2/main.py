# coding=utf-8
import os
import re
import Kit
import uuid
import Config
import urllib3
import pymysql
import requests
import subprocess
import urllib.error
import urllib.request
from bs4 import BeautifulSoup
from urllib.parse import quote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    config = Config.get_config()
    print("[INFO]", "Start at", Kit.str_time())

    # Fetch archives
    session = requests.Session()
    session.headers = {
        "User-Agent": config['BASE']['user_agent'],
        "Connection": "keep-alive",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    session.cookies.update({"age_gate": "18"})

    conn = Kit.mysql_conn(config, "MYSQL")
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    for pid in range(1, 2760):
        sql = "SELECT * FROM `gca_tw` WHERE `id`=%s"
        cursor.execute(sql, pid)
        record = cursor.fetchone()
        if record is not None and record["tag"] in ["202", "404"]:
            continue

        if record is not None and record["download"] == "Yes":
            continue

        try:
            fetch_page(config, conn, session, pid)
        except Exception as e:
            Kit.print_red("Runtime Error: {}".format(e))
            raise e


def fetch_page(config, conn, session, pid):
    # Fetch info data
    page_url = "https://ca.gca.tw/{}.html".format(pid)
    print("[INFO]", "Fetch page {} ... ".format(page_url), end="")

    # Get page data
    res = session.get(page_url)

    if res.status_code == 404:
        Kit.print_red("ERR-404")
        error_record(conn, pid, 404)
        return False
    Kit.print_green("SUCCESS")

    soup = BeautifulSoup(res.text, "lxml")
    title = soup.find(rel="bookmark")
    if title is None:
        title = "None-{}".format(uuid.uuid1())
    else:
        title = title.string
    print("Page title:", title)

    # Submit password
    payload = {
        "post_password": title,
        "Submit": "提交"
    }
    session.post("https://ca.gca.tw/wp-login.php?action=postpass", data=payload)

    # Re-get page content
    res = session.get(page_url)

    soup = BeautifulSoup(res.text, "lxml")
    content = soup.find(class_="entry-content")

    sql_data = {
        "pid": pid,
        "url": page_url,
        "tag": "video",
        "title": title,
        "cover": "",
        "video": "",
        "download": "No",
        "raw_data": res.text
    }
    sql = "REPLACE INTO `gca_tw`(id,url,tag,title,cover,video,download,raw_data)VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
    cursor = conn.cursor()
    cursor.execute(sql, args=list(sql_data.values()))
    conn.commit()

    # Download image
    image_list = content.find_all("img")
    if image_list is not None:
        for index, image in enumerate(image_list):
            image_url = "https://ca.gca.tw/{}".format(image["src"])
            image_path = "{}/Image/{}-{}.jpg".format(config["BASE"]["download_path"], legalize_name(title), index)
            try:
                urllib.request.urlretrieve(quote(image_url, safe='/:?='), filename=image_path)  # Images
            except urllib.error.HTTPError:
                continue

    # Download video
    video_box = content.find("video")
    if video_box is not None:

        if video_box["poster"].find("ca.gca.tw") != -1:
            cover_url = video_box["poster"]
        else:
            cover_url = "https://ca.gca.tw/{}".format(video_box["poster"])

        if "src" in video_box.attrs.keys():
            video_url = video_box["src"]
        else:
            video_url = video_box.find("source")["src"]

        video_path = os.path.abspath("{}/{}".format(config["BASE"]["download_path"], legalize_name(title)))
        if os.path.exists(video_path) is False:
            os.mkdir(video_path)

        urllib.request.urlretrieve(quote(cover_url, safe='/:?='), filename="{}/cover.jpg".format(video_path))  # Image
        aria2c_pull(config, page_url, video_path, "{}.mp4".format(legalize_name(title)), [video_url], True)  # Video

        sql = "UPDATE `gca_tw` SET `cover`=%s,`video`=%s WHERE `id`=%s"
        cursor.execute(sql, args=[cover_url, video_url, pid])

    sql = "UPDATE `gca_tw` SET `download`='Yes' WHERE `id`=%s"
    cursor.execute(sql, args=[pid])
    conn.commit()


def error_record(conn, pid, status):
    cursor = conn.cursor()
    sql = "REPLACE INTO `gca_tw`(id,url,tag,title,cover,video,download,raw_data)VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql, args=[pid, "https://ca.gca.tw/{}.html".format(pid), status, "无法访问", "", "", "", ""])
    conn.commit()


def aria2c_pull(config, page, path, name, url_list, show_process=False):
    # 设置输出信息
    if show_process:
        out_pipe = None
    else:
        out_pipe = subprocess.PIPE

    # 读取代理信息
    proxies = ''
    proxies += ' --http-proxy="{}"'.format(config["PROXY"]["http"]) if config["PROXY"]["http"] is not None else ""
    proxies += ' --https-proxy="{}"'.format(config["PROXY"]["https"]) if config["PROXY"]["https"] is not None else ""

    url = '"{}"'.format('" "'.join(url_list))
    shell = 'aria2c -c -k 1M -x {} -d "{}" -o "{}" --referer="{}" {} {}'
    shell = shell.format(len(url_list) * 4, path, name, page, proxies, url)
    process = subprocess.Popen(shell, stdout=out_pipe, stderr=out_pipe, shell=True)
    process.wait()


def legalize_name(name):
    legal_name = re.sub(r"[\/\\\:\*\?\"\<\>\|\s']", '_', name)
    legal_name = re.sub(r'[‘’]', '_', legal_name)
    if len(legal_name) == 0:
        return 'null'
    return legal_name


if __name__ == '__main__':
    main()
