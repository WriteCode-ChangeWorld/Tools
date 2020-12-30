import os
import re
import sys
import json
import time
import requests
from urllib.parse import unquote
from lxml import etree

from thread_pool import *

# iwara地址:https://ecchi.iwara.tv/videos/v2km9s5npeterzlad
# iwara地址:https://ecchi.iwara.tv/videos/q9zkwied25ir7xokw
# 对应api接口为:https://ecchi.iwara.tv/api/video/v2km9s5npeterzlad

# 如果需要下载private视频,则将自己的cookie填入此处
cookie = ""

def log_str(*args, end=None):
    for i in args:
        print('[{}] {}'.format(time.strftime("%Y-%m-%d %H:%M:%S"),i),end=end)

def getFunctionName(extra=False):
	# https://www.jb51.net/article/49026.htm
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    if extra == True:
    	return f.f_lineno
    return f.f_code.co_name


class IwaraDownloader:
	"""
	目前支持
	1、iwara用户的所有视频下载,存储在单个的<用户名称>文件夹中
	2、单个iwara视频下载,存储在down文件夹下
	"""
	def __init__(self,links):
		self.iwara_host = "https://ecchi.iwara.tv"
		# 拼接videos页面
		# https://ecchi.iwara.tv/users/Forget%20Skyrim./videos?page=3
		self.host = "https://ecchi.iwara.tv{}?language=zh&page={}"
		# 视频信息接口
		self.api_url = "https://ecchi.iwara.tv/api/video/{}"
		# 起始页码
		self.page_num = 0

		# 页面请求头
		self.page_headers = {
			"user-agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3741.400 QQBrowser/10.5.3863.400",
			"referer":"https://ecchi.iwara.tv/",
			"accept-language": "zh-CN,zh;q=0.9"
		}
		# 请求头
		self.headers = {
			"host":"ecchi.iwara.tv",
			"user-agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3741.400 QQBrowser/10.5.3863.400",
		}
		# 添加用户自定义cookie,主要用于private视频获取
		if cookie != "":
			self.headers["cookie"] = cookie

		# 需要下载的iwara链接列表
		if links == []:
			log_str("Iwara链接列表为空!")
			exit()
		else:
			# 去重
			self.original_links = list(set(links))
		log_str("{}: {} {}".format(getFunctionName(),len(self.original_links),self.original_links))

		# 初始化下载主目录
		if not os.path.exists("./down"):os.mkdir("./down")
		self.root_path = os.path.join(os.getcwd(),"down")

		self.error_code_list = {
			"ErrorVideoUrl":"无效的视频链接",
			"ErrorUserUrl":"错误的用户主页链接",
			"EmptyVideoLinks":"该用户无视频",
			"PrivateVideoUrl":"无法下载private或无法播放的视频",
			"JsonDecodeError":"解析json数据出错",
			"UnknownError":"不明原因导致的失败",
			"NetWorkTimeoutError":"网络或代理超时",
		}

	def get_resp(self,url,
				 params=None,
				 headers=None,
				 retry_num=3,
				 stream=False,
				):
		""" 
		一个简单的网络请求函数
		"""
		if headers == None:
			headers = self.page_headers
		try:
			resp = requests.get(url,params=params,
								headers=headers,
								timeout=10,
								stream=stream
								)
		except Exception as e:
			if retry_num >= 3:
				return self.get_resp(url,params=params,headers=headers,retry_num=retry_num-1,stream=stream)
			else:
				log_str("{}: {} | 超出重试次数".format(getFunctionName(),url))
				log_str("{}: {}".format(getFunctionName(),e))
				return None
		else:
			time.sleep(1)
			return resp

	def get_title(self,link):
		"""
		提供iwara视频链接,获取标题
		https://ecchi.iwara.tv/videos/rmj21h3l1io6qm85
		"""
		# title = re.sub('[\/:*?"<>|]','',
		# 			re.findall("<title>(.*?)</title>",
		# 						self.get_resp(iwara_link).text.replace("\u3000",""))[0]
		# 				)
		html = self.get_resp(link)
		if type(html) == type(None):
			return "NetWorkTimeoutError"
		response = html.text.replace("\u3000","")
		r = re.findall("<title>(.*?)</title>",response)[0].split("| Iwara")[0]
		title = re.sub('[\/:*?"<>|]','',r)
		title = title.replace("&amp;","&").replace("\u3000","").\
						replace(" ","").replace(".","")
		return title

	def get_data(self,link):
		"""
		获取视频接口信息,返回原始视频链接和动态host
		https://ecchi.iwara.tv/api/video/4kbwafpkz0tyv3k4m
		return source_url,host/None
		"""
		url = self.api_url.format(link.split("/")[-1])
		# log_str("getdata {}".format(link))
		resp = self.get_resp(url,headers=self.headers)
		if resp.text == '[]':
			# private视频
			return "PrivateVideoUrl"
		else:
			try:
				json_data = json.loads(resp.text)
			except json.decoder.JSONDecodeError as e:
				log_str(e)
				return "JsonDecodeError"
			except Exception as e:
				log_str(e)
				return "UnknownError"
			else:
				source_url = "https:{}".format([r["uri"] for r in json_data if r["resolution"] == "Source"][0])
				host = source_url.split("file.php")[0]
				return [source_url,host]

	def get_links(self,link):
		"""
		https://ecchi.iwara.tv/users/%E5%92%95%E5%98%BF%E5%98%BF/videos?page=1
		https://ecchi.iwara.tv/users/forget-skyrim
		获取当前页面的iwara链接和页数
		视频不超过16个的用户,无videos页面
		"""
		href_list,title_list,page_num = [],[],0
		# 从作者主页获取videos链接,有则videos分支,无则主页沿用主页obj
		resp = self.get_resp(link,headers=self.page_headers).text
		home_obj = etree.HTML(resp)
		home_expression = '//div[@id="block-views-videos-block-2"]//div[@class="more-link"]//a/@href'

		# 无效作者主页/无效视频
		if "ユーザーリスト | Iwara" in resp:
			return ["ErrorUserUrl"],0

		# 无videos页面 --> 用户主页
		if home_obj.xpath(home_expression) == []:
			# /videos/83wvbuz4yfl7bn3l
			href_expression = '//div[@id="block-views-videos-block-2"]//div[contains(@class,"views-responsive-grid")]//h3/a/@href' 
			title_expression = '//div[@id="block-views-videos-block-2"]//div[contains(@class,"views-responsive-grid")]//h3/a/text()' 
			if home_obj.xpath(href_expression) != []:
				log_str("Not Video Url")
				href_list = ["{}{}".format(self.iwara_host,r) for r in home_obj.xpath(href_expression)]
				# 转义html字符
				title_list = [re.sub('[\/:*?"<>|]','',r).
								replace("&amp;","&").replace("\u3000","").
								replace(" ","").replace(".","") for r in home_obj.xpath(title_expression)]
			# 用户无视频
			else:
				return [],0
		# 有videos页面 --> videos
		else:
			useVideoUrl = home_obj.xpath(home_expression)[0].split("?")[0]
			page_link = self.host.format(useVideoUrl,self.page_num)
			log_str("Have Videos Url")	
			log_str(page_link)
			obj = etree.HTML(self.get_resp(page_link,headers=self.page_headers).text)
			# 页数
			try:
				page_num = int(obj.xpath("//li[@class='pager-last last']//@href")[0].split("page=")[-1])
			except:
				log_str("{}: User Video PageNum Not NotFound".format(getFunctionName()))
				# 最后一页或该用户视频数<=16,导致videos页面为空
				page_num = 0

			href_list = ["{}{}".format(self.iwara_host,r) for r in obj.xpath("//h3[@class='title']/a/@href")]
			# 转义html字符
			title_list = [re.sub('[\/:*?"<>|]','',r).
								replace("&amp;","&").replace("\u3000","").
								replace(" ","").replace(".","") for r in obj.xpath("//h3[@class='title']/a/text()")]
			
			log_str("page_num: {}".format(page_num))

		res = []
		for h,t in zip(href_list,title_list):
			res.append({"link":h,"title":"{}--{}".format(t,h.split("videos/")[-1])})

		# log_str("{}: Exit Function".format(getFunctionName()))
		return res,page_num

	def check_folder(self,link):
		"""
		https://ecchi.iwara.tv/users/%E8%B4%BE%E5%94%AF%E2%84%A1
		:params link: 原始链接
		:return :创建作者目录并返回目录
		"""
		user = link.split("users/")[-1]
		user = unquote(user,'utf-8')
		user_path = os.path.join(self.root_path,user)
		if not os.path.exists(user_path):
			os.mkdir(user_path)
		return user_path

	def conver_link(self,link):
		"""
		:params link: 原始链接
		:return :原始链接或包含作者视频链接的列表

		判断并转换链接
			1、作者主页链接,则获取其所有视频链接
			https://ecchi.iwara.tv/users/xxxx
			2、单个视频链接,不作处理
		"""
		# 更改获取videos页面的逻辑,从作者主页获取
		# https://ecchi.iwara.tv/users/forget-skyrim
		# 获取到的是https://ecchi.iwara.tv/users/Forget%20Skyrim./videos
		log_str(getFunctionName())
		user_video_links = []
		if "users" in link:
			while True:
				log_str("in loop")
				page_video_links,page_num = self.get_links(link)
				self.page_num = page_num
				user_video_links.extend(page_video_links)
				# 业务跳出条件
				if self.page_num == 0:
					log_str("out loop")
					break

			# 用户无视频
			if user_video_links == []:
				return "EmptyVideoLinks"

			if user_video_links[0] == "ErrorUserUrl":
				return "ErrorUserUrl"

			# 创建作者目录
			user_path = self.check_folder(link)
			# 数据组装
			for video in user_video_links:
				video["path"] = user_path
			return user_video_links

		title = self.get_title(link)
		# 无效的视频链接
		if title == "Iwara":
			return "ErrorVideoUrl"
		elif title in self.error_code_list.keys():
			return title

		return [{"link":link,"title":title,"path":self.root_path}]

	def download(self,host,source_url,file_path):
		"""
		下载原始视频
		"""
		# file_headers = {
		# 	"host":host,
		# 	"user-agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3741.400 QQBrowser/10.5.3863.400",
		# }
		response = self.get_resp(source_url,headers=self.page_headers,stream=True)
		# response = self.get_resp(source_url,headers=file_headers,stream=True)
		# content_size = int(response.headers['content-length']) # 获得文件大小(字节)
		# data_count = 0	# 计数
		chunk_size = 1024 # 每次最大请求字节
		with open(file_path, "wb") as file:
			for data in response.iter_content(chunk_size=chunk_size):
				file.write(data)             
		time.sleep(0.5)

	def iwara_process(self,*args):
		"""
		子线程任务函数
		"""
		link,title,path = args[0]["link"],args[0]["title"],args[0]["path"]
		# 获取当前函数名称
		file_path = "{}.mp4".format(os.path.join(path,title))
		# log_str("{}: {}".format(getFunctionName(),link))
		# log_str(file_path)
		try:
			if os.path.exists(file_path) and os.path.getsize(file_path) > 100000:
				log_str("【{}】已存在".format(title))
			else:
				log_str("【{}】正在下载".format(title))
				data = self.get_data(link)
				# get_data返回错误码
				if type(data) == type("") and data in self.error_code_list.keys():
					log_str("【{}】 {} {}".format(
						title,link,self.error_code_list.get(data,"NotFoundErrorCode")
						)
					)
					return
				else:
					source_url,host = data[0],data[1]
		except Exception as e:
			log_str("{}: {}".format(getFunctionName(),e))
			return 
		else:
			try:
				self.download(host,source_url,file_path)
			except Exception as e:
				log_str("【{}】下载失败-->{}".format(title,e))
			else:
				log_str("【{}】下载成功".format(title))

			
			# url,host = self.get_data(iwara_link)
			# host,url,data = self.get_data(iwara_link)
			# self.download(host,filename,url,data)
			# self.download(self.get_data(iwara_link))

	def main(self):
		"""
		一、单个iwara视频
		1.无限制 https://ecchi.iwara.tv/videos/4kbwafpkz0tyv3k4m
		2.private https://ecchi.iwara.tv/videos/wdz0ofvm9buqwapjb
		3.无效视频 https://ecchi.iwara.tv/videos/xxxxxxx

		二、作者主页
		1.无private
			1.小于等于16个视频 https://ecchi.iwara.tv/users/shikou
			2.大于16个视频 1页无页码 https://ecchi.iwara.tv/users/forget-skyrim
						  2页以上 https://ecchi.iwara.tv/users/shirakamisan
						  # 存在无法播放的视频,按private视频处理
		2.有private
			1.小于等于16个视频 暂时没找到,按1.1处理
			2.大于16个视频 https://ecchi.iwara.tv/users/贾唯℡
		
		3.无视频 https://ecchi.iwara.tv/users/lilan0538
		4.无效作者主页 https://ecchi.iwara.tv/users/测试
		"""
		pool = ThreadPool(8)
		try:
			for link in self.original_links:
				# i站相关链接下载
				if link.startswith("https://ecchi.iwara.tv/"):
					# print(link)
					link_list = self.conver_link(link)
					if type(link_list) == type("link_list") and link_list in self.error_code_list.keys():
						log_str("【{}】 {}".format(
							link,self.error_code_list.get(link_list,"NotFoundErrorCode")
							)
						)
						continue

					if link_list != []:
						log_str("len_link_list:{}".format(len(link_list)))
						# log_str("len_link_list:{}\nlink_list:{}".format(len(link_list),link_list))
						
						for l in link_list:
							pool.put(self.iwara_process,(l,),callback)
		except Exception as e:
			log_str("Exception {} line:{}".format(e,getFunctionName(extra=True)))
		finally:
			pool.close()

		# iwara = []
		# for l in links[::-1]:
		# 	if "ecchi.iwara.tv/users" in l:
		# 		for r in self.get_links(l):
		# 			iwara.append(r)
		# 	else:
		# 		iwara.append(l)
		# print(iwara)
		

if __name__ == '__main__':
	log_str("下载作者视频则输入作者主页链接...","如:https://ecchi.iwara.tv/users/qishi")
	log_str("下载单个视频则输入视频链接...","如:https://ecchi.iwara.tv/videos/4kbwafpkz0tyv3k4m")
	log_str("输入完成后,请输入'go'以开始下载...")
	# https://ecchi.iwara.tv/users/%E8%B4%BE%E5%94%AF%E2%84%A1 存在private
	# https://ecchi.iwara.tv/users/qishi
	input_links = []
	while True:
		input_iwara_link = input("现在输入Iwara链接:")
		if input_iwara_link == "":
			pass
		elif input_iwara_link == "go":
			break
		else:
			input_links.append(input_iwara_link)
	log_str("现在开始获取链接,请稍后...")
	IDLoader = IwaraDownloader(input_links)
	IDLoader.main()