import re
import os
import time
import random
import requests
from lxml import etree

from requests.packages.urllib3.exceptions import InsecureRequestWarning     #强制取消警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  

class mzitu():
    def __init__(self):
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
            'referer':'https://www.mzitu.com'
        }
        self.host = "https://www.mzitu.com"
        self.template = "https://www.mzitu.com/page/{}"
        # 修改self.path为你的存储地址
        self.path = r'D:\Tools\mzitu'
        self.folder_path = ''

    def max_num(self)->int:
        resp = self.request(self.host)
        resp_obj = etree.HTML(resp.text)
        resp_expression = """//div[@class='nav-links']//a/text()"""
        resp_result = resp_obj.xpath(resp_expression)
        if resp_result == []:
            return 0
        else:
            num = int(resp_result[-2])
            return num

    def main(self):
        """
        主流程
        """
        num = self.max_num()
        print("一共有{}页".format(num))
        if num == 0:
            exit()

        for i in range(1,num+1):
            page_url = self.template.format(i)
            print(page_url)
            
            page_result = self.get_page_html(page_url)
            if page_result == []:
                continue

            for page_data in page_result:
                # 创建套图文件夹
                self.folder_path = self.create_folder(page_data["name"])
                # 获取套图的所有图片链接
                print("正在下载【{}】--{}".format(page_data["name"],page_data["href"]))
                self.get_img_href(page_data["href"])
                # break
                
            # break

    def get_page_html(self,page_url:str)->dict:
        """
        获取当前page页面,各个套图的名称及链接
        :param page_url: 页面url:https://www.mzitu.com/page/1
        :return: 当前页面的套图名称及链接
        """
        html = self.request(page_url)
        html_obj = etree.HTML(html.text)
        name_expression = """//ul[@id='pins']//li/span/a/text()"""
        href_expression = """//ul[@id='pins']//li/span/a/@href"""
        
        name_list = html_obj.xpath(name_expression)
        href_list = html_obj.xpath(href_expression)

        result = []
        for name,href in zip(name_list,href_list):
            result.append({"name":name,"href":href})
        return result

    def get_img_href(self,url:str)->None:
        """
        图片页面获取多个图片地址,并下载原图
        :param url: 套图链接,https://www.mzitu.com/227785
        :return: 套图链接中所有图片的原图链接
        """
        html = self.request(url)
        obj = etree.HTML(html.text)
        img_expression = """//div[@class="main-image"]//img/@src"""
        num_expression = """//div[@class='pagenavi']//a/span/text()"""

        num = int(obj.xpath(num_expression)[-2])

        # 套图目录下有对应num张的图片则跳过该套图下载
        if os.listdir(self.folder_path) == num:
            return 
        
        for i in range(1,num+1):
            # https://www.mzitu.com/227785/61
            img_url = "{}/{}".format(url,i)
            print(img_url)
            img_resp = self.request(img_url)
            img_obj = etree.HTML(img_resp.text)

            try:
                img_href = img_obj.xpath(img_expression)[0]
            except:
                img_href = ""
            img_name = img_href.rsplit("/",1)[-1]

            img_path = os.path.join(self.folder_path,img_name)
            # 不存在则下载
            if os.path.exists(img_path) == False:
                self.save_img(img_href,img_path)

            # 存在但字节数少于1000
            if os.path.exists(img_path) == True and os.path.getsize(img_path) < 1000:
                self.save_img(img_href,img_path)

            # 休眠
            time.sleep(0.1)

    def save_img(self,img_url:str,path:str)->None:
        """
        写入图片二进制数据

        :param img_url: 图片链接
        :param path: 图片存储路径
        :return: None
        """
        img = self.request(img_url)
        with open(path, 'ab') as f:
            f.write(img.content)

    def create_folder(self,title:str)->str:
        """
        创建文件夹
        :param title: 文件夹名称:
        :return: 创建的文件夹路径
        """
        title = re.sub(r'[\/:*?"<>|]','_',title)
        folder_path = os.path.join(self.path,title)
        isExists = os.path.exists(folder_path)
        if not isExists:
            print("已创建【{}】该文件夹".format(title))
            os.makedirs(folder_path)
            return folder_path
        print("已存在【{}】该文件夹".format(title))
        return folder_path

    def request(self,url:str,retry_num=5):
        try:
            response = requests.get(url, headers=self.headers,verify=False, timeout=10)
            response.encoding = "utf8"
            return response
        except Exception as e:
            if retry_num > 0:
                return self.request(url,retry_num-1)
            else:
                print('网络错误:{} {}'.format(url,e))
                return None

Mzitu = mzitu()
Mzitu.main()