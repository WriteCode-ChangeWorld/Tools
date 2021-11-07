# -*- encoding: utf-8 -*-
'''
@File    :   pixiv2eagle.py
@Time    :   2021/11/04 15:25:48
@Author  :   Coder-Sakura
@Version :   1.0
@Desc    :   将pixiv插画的tag信息写入到Eagle的metadata.json中\
    使得在Eagle中也能通过标签查找自己喜欢的作品
'''

# here put the import lib
import os
import json
import time
import requests
from loguru import logger
# 强制取消警告
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from thread_pool import ThreadPool,callback

"""
=========================================================
1. 插画图片名称
可识别的pixiv插画名称包括:
# 图片从PIXIC下载
<pid>.jpg
<pid>.png
<pid>-1.jpg
<pid>-2.png
# 直接从PIXIV下载
<pid>_p0.jpg
<pid>_p1.png

=========================================================
2. tag数据来源
pixiv2eagle.py 提供两种形式以获取 pixiv 插画的 tag 信息

# 通过PixiC API的形式, PixiC API的部署形式可以参考:
https://github.com/Coder-Sakura/PixiC/wiki

部署好之后,先地址填入 PIXIC_API_HOST.
如: PIXIC_API = http://xxx.xx.xxx.xx:1526/api/v2/get-info

# 觉得麻烦的朋友直接将 PIXIC_API 留空. 如: PIXIC_API = ""

=========================================================
3. 填入Eagle Home Path

使用Eagle创建一个新的资源库时,在你指定的文件夹下会生成
形如 Home.library的文件夹, 将这个地址填入到EAGLE_HOME_PATH即可
如: EAGLE_HOME_PATH = r"G:\EagleHome\Home.library"

"""


PIXIC_API = ""
# EAGLE_HOME_PATH = r"G:\EagleHome\个人收藏.library"
# TEST DIR -> Home.library
EAGLE_HOME_PATH = r""

log_path = os.path.split(os.path.abspath(__file__))[0]
# 日志写入
logger.add( 
    os.path.join(log_path, "{time}.log"),
    encoding="utf-8",
    enqueue=True,
)
TOOL = ThreadPool(8)

class Pixiv2Eagle:
    # 计数
    count = 0
    # 识别成功
    _count = 0
    # 无法识别
    un_count = 0
    # 写入成功
    succees_count = 0
    # 已写入
    pass_count = 0

    def __init__(self):
        # EAGLE_HOME_PATH
        if not EAGLE_HOME_PATH:
            logger.warning("<EAGLE_HOME_PATH> 没有正确配置. 请填写")
            exit()
        else:
            self.eagle_home_path = EAGLE_HOME_PATH

        # PIXIC_API
        # FLAG - False - TEMP URL
        # FLAG - True - PIXIC API
        if not PIXIC_API:
            self.pixic_api = ""
            self.flag = False
        else:
            self.pixic_api = PIXIC_API
            self.flag = True
            logger.info(f"<PIXIC API> {self.pixic_api}")

        # AJAX URL
        self.temp_url = "https://www.pixiv.net/ajax/illust/"

        # HEADERS
        self.headers = {
            "Host": "www.pixiv.net",
            "referer": "https://www.pixiv.net/",
            "origin": "https://accounts.pixiv.net",
            "accept-language": "zh-CN,zh;q=0.9",
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        }

    def baseRequest(self, options, method="GET", data=None, params=None, retry_num=5):
        """
        一个小型的健壮的网络请求函数
        :params options: 包括url,自定义headers,超时时间,cookie等
        :params method: 请求类型
        :params data: POST传参
        :params params: GET传参
        :params retry_num: 重试次数

        demo如下:
        demo_headers = headers.copy()
        demo_headers['referer']  = 'www.example.com'
        options ={
            "url": origin_url,
            "headers": demo_headers
        }
        baseRequest(options = options)
        """
        try:
            response = requests.request(
                    method,
                    options["url"],
                    data = data,
                    params = params,
                    cookies = options.get("cookies",""),
                    headers = self.headers,
                    verify = False,
                    timeout = options.get("timeout",5),
                )
            response.encoding = "utf8"
            return response
        except Exception as e:
            if retry_num > 0:
                time.sleep(0.5)
                return self.baseRequest(options,data,params,retry_num=retry_num-1)
            else:
                logger.info("网络请求出错 url:{}".format(options["url"]))
                return 

    def get_images(self, path=None):
        if not path:path = self.eagle_home_path
        return os.listdir(path)

    def get_pid(self, name):
        """
        识别和切分pid
        :params name: 文件名称
        :return: pid or ""
        """
        pid = ""
        if "-" in name:
            pid = name.split("-")[0]
        elif "_" in name:
            pid = name.split("_")[0]
        else:
            pid = name.split(".")[0]

        try:
            int(pid)
        except Exception as e:
            return ""
        else:
            return pid

    # PIXIC API
    def get_tags_pixic(self,pid):
        """
        从PIXIC API获取pid tag(get-info API)
        查询不到结果则使用pixiv api进行复查
        
        :params pid: pixiv插画id
        :return: [tag1,tag2...] or []
        """
        data = {"pid": pid}
        resp = self.baseRequest(
            options = {"url":self.pixic_api},
            method = "POST",
            data = data
        )
        if not resp:
            return []

        json_data = json.loads(resp.text)

        if json_data["result"][0].get("message","") != "":
            # PIXIC API内包含画师名称
            tags = json_data["result"][0]["tag"]
            tag_list = []
            
            _ = tags.split("、")
            for i in _:
                temp = i.split("/")
                for t in temp:tag_list.append(t)
            return list(set(tag_list))
        else:
            logger.info(json_data["result"][0]["message"])
            return []

    # AJAX URL
    def get_tags(self, pid):
        """
        从pixiv api获取pid tag
        :params pid: pixiv插画id
        :return: [tag1,tag2...] or []
        """
        resp = self.baseRequest(
            options = {"url":f"{self.temp_url}{pid}"}
        )
        if not resp:
            return []

        json_data = json.loads(resp.text)

        if json_data["error"] == False:
            tags = json_data["body"]["tags"]["tags"]
            tag_list = []
            # 加入画师名称
            tag_list.append(json_data["body"]["userName"])
            for i in tags:
                if "translation" in i.keys():
                    tag_list.append(i["translation"]["en"])
                tag_list.append(i["tag"])
            return list(set(tag_list))
        else:
            logger.info(json_data["message"])
            return []

    @logger.catch
    def thread_task(self, _, num):
        """
        线程任务函数
        :params _: 待处理文件路径
        :params num: 当前序号
        """
        metajson_path = os.path.join(self.images_path,_,"metadata.json")
        # logger.info(f"<{num}/{self.len_images_folders}> <metajson_path> {metajson_path}")
        with open(metajson_path,encoding="utf8") as f:
            # 记载metadata
            metadata = json.load(f)
            # 获取metafilename
            name = metadata["name"]
            logger.info(f"<{num}/{self.len_images_folders}> <name> {name} <metajson_path> {metajson_path}")
            pid = self.get_pid(name)
            # 成功识别
            if pid:
                self._count += 1
            # 无法识别
            else:
                self.count += 1
                self.un_count += 1
                return 
            
            # TAG
            # tags已有内容跳过
            if metadata["tags"]:
                self.count += 1
                self.pass_count += 1
                return 
            else:
                tag_list = []
                # 有定义PIXIC API则使用
                if self.flag:
                    tag_list = self.get_tags_pixic(pid)
                
                # PIXIC获取失败或未定义PIXIC API
                if not tag_list:
                    tag_list = self.get_tags(pid)

                # tag_list获取为空则跳过
                if tag_list == []:
                    self.count += 1
                    self.pass_count += 1
                    return
                else:
                    metadata["tags"] = tag_list

            # 写入
            if metadata:
                with open(metajson_path,"w",encoding="utf8") as f:
                    json.dump(metadata,f,ensure_ascii=False)
                    self.succees_count += 1
            time.sleep(0.1)
            self.count += 1

    def main(self):
        self.images_path = os.path.join(self.eagle_home_path,"images")
        images_folders = self.get_images(self.images_path)
        self.len_images_folders = len(images_folders)

        try:
            for _ in range(0,len(images_folders)):
                TOOL.put(self.thread_task, (images_folders[_], _+1, ), callback)
                # break
        except Exception as e:
            logger.info("Exception:{}".format(e))
            TOOL.close()
        finally:
            TOOL.close()

        while True:
            logger.info(f"<free_list> {TOOL.free_list} <max_num> {TOOL.max_num} <generate_list> {TOOL.generate_list}")
            # 正常关闭线程池
            if TOOL.free_list == [] and TOOL.generate_list == []:
                TOOL.close()
                logger.info(f"<当前总数> {self.count}")
                logger.info(f"<成功识别数> {self._count}")
                logger.info(f"<无法识别数> {self.un_count}")
                logger.info(f"<写入成功数> {self.succees_count}")
                logger.info(f"<跳过数> {self.pass_count}")
                break
            time.sleep(3)

if __name__ == "__main__":
    pixiv2eagle = Pixiv2Eagle()
    pixiv2eagle.main()