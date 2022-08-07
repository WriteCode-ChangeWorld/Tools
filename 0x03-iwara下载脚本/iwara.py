import os
import re
import sys
import json
import time
import glob
import requests
from lxml import etree
from loguru import logger
from urllib.parse import unquote
# 强制取消警告
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


from thread_pool import *


# ======================= CONFIG =================== #
# Version
VERSION = "V1.0.8"
# 如果需要下载private视频,则将自己的cookie填入此处
cookie = ""
# 设置为True 开启DEBUG模式
DEBUG = False
# 自定义下载路径
ROOT_DIR = r""
# thread num
THREAD_NUM = 8

# log config
if DEBUG:
	level = "DEBUG"
else:
	level = "INFO"

# remove default handler
logger.remove()
# 控制台输出
logger.add( 
    sys.stderr,
    level=level
)
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
# 日志写入
logger.add( 
    os.path.join(log_path, "{time}.log"),
    encoding="utf-8",
    rotation="00:00",
    enqueue=True,
    level=level
)
logger.add( 
    os.path.join(log_path, "[ERROR video] {time}.log"),
    encoding="utf-8",
    rotation="00:00",
    enqueue=True,
    level="ERROR"
)
# ======================= CONFIG =================== #


# 重试视频列表 - 视频完整性校验失败
# [{"args":args, "count":count},{}...]
RETRY_COUNT = 3
ERR_TASK_LIST = []


def check_video(resp, path)->bool:
	"""
	:params resp: 响应体
	:params path: 本地视频
	"""
	local_size = int(os.path.getsize(path))
	resp_size = int(resp.headers["content-length"])
	logger.debug(f"{local_size} {resp_size}")
	if local_size != resp_size:
		return False
	else:
		return True

def byte2size(value):
	value = int(value)
	units = ["B", "KB", "MB", "GB", "TB", "PB"]
	size = 1024.0
	for i in range(len(units)):
		if (value/size) < 1:
			return "%.2f%s" % (value, units[i])
		value = value/size

def dealwith_title(title):
	title = re.sub('[\/:*?"<>|]', '_', title)
	title = title.replace("&amp;", "&").replace("\u3000", "").\
					replace(".", "_")
	return title

def check_errTask_exists(data, err_task_list):
	for _ in err_task_list:
		if data == _["args"]:
			return True
	return False


class IwaraDownloader:
	"""
	目前支持
	1、iwara用户的所有视频下载,存储在单个的<用户名称>文件夹中
	2、单个iwara视频下载,存储在down文件夹下

	iwara地址:https://ecchi.iwara.tv/videos/v2km9s5npeterzlad
	对应api接口为:https://ecchi.iwara.tv/api/video/v2km9s5npeterzlad
	"""
	def __init__(self,links):
		self.iwara_host = "https://ecchi.iwara.tv"

		# 拼接videos页面
		# https://ecchi.iwara.tv/users/Forget%20Skyrim./videos?page=3
		self.host = "https://ecchi.iwara.tv{}?language=zh&page={}"
		
		# 视频信息接口
		self.api_url = "https://ecchi.iwara.tv/api/video/{}"
		# conver_link:用来判断跳出的页码
		self.page_num = 0

		# 页面请求头
		self.page_headers = {
			"user-agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3741.400 QQBrowser/10.5.3863.400",
			"referer":"https://ecchi.iwara.tv/",
			"accept-language": "zh-CN,zh;q=0.9"
		}
		# get_data请求头
		self.headers = {
			"host":"ecchi.iwara.tv",
			"user-agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3741.400 QQBrowser/10.5.3863.400",
		}
		# 添加用户自定义cookie,主要用于private视频获取
		if cookie:
			self.headers["cookie"] = cookie

		# 需要下载的iwara链接列表
		if links == []:
			logger.error("Iwara链接列表为空!")
			exit()
		else:
			# 去重
			self.original_links = list(set(links))
		logger.info(f"输入链接数量 - {len(self.original_links)}")
		logger.debug(f"输入链接 - {self.original_links}")

		# 初始化下载主目录
		self.root_path = os.path.abspath(os.path.dirname(__file__)) if not ROOT_DIR else ROOT_DIR
		if not os.path.exists(self.root_path):os.mkdir(self.root_path)

		self.error_code_list = {
			"ErrorVideoUrl": "无效的视频链接",
			"ErrorUserUrl": "错误的用户主页链接",
			"EmptyVideoLinks": "该用户无视频",
			"PrivateVideoUrl": "该视频为private视频 或 视频无法播放下载",
			"JsonDecodeError": "解析json数据出错",
			"UnknownError": "不明原因导致的失败",
			"NetWorkTimeoutError": "网络或代理超时"
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
								timeout=20,
								stream=stream,
								verify=False
								)
		except Exception as e:
			if retry_num >= 3:
				logger.info(f"网络错误,正在重试 - {url}")
				return self.get_resp(url,params=params,headers=headers,retry_num=retry_num-1,stream=stream)
			else:
				logger.warning(f"超出重试次数 - {url}")
				logger.warning(f"Exception - {e}")
				return None
		else:
			time.sleep(1)
			return resp

	def get_title(self,link):
		"""提供iwara视频链接,获取标题"""
		html = self.get_resp(link)
		if type(html) == type(None):
			return "NetWorkTimeoutError"
		response = html.text.replace("\u3000","")
		r = re.findall("<title>(.*?)</title>", response)[0].split("| Iwara")[0]
		title = dealwith_title(r)
		return title

	def get_data(self,link):
		"""
		获取视频接口信息,返回原始视频链接和动态host
		:params link: iwara video url, https://ecchi.iwara.tv/videos/9jqbjse8qhzmo8ja
		:return: [source_url,host] or err str
		"""
		# url - https://ecchi.iwara.tv/api/video/4kbwafpkz0tyv3k4m
		url = self.api_url.format(link.split("/")[-1])
		logger.debug(f"<api_url> - {url}")
		resp = self.get_resp(url,headers=self.headers)

		if resp.text == '[]':
			# private视频
			return "PrivateVideoUrl"
		else:
			try:
				json_data = json.loads(resp.text)
			except json.decoder.JSONDecodeError as e:
				logger.warning(f"JsonDecodeError Exception - {e}")
				return "JsonDecodeError"
			except Exception as e:
				logger.warning(f"UnknownError Exception - {e}")
				return "UnknownError"
			else:
				source_url = f'https:{[r["uri"] for r in json_data if r["resolution"] == "Source"][0]}'
				host = source_url.split("file.php")[0]
				return [source_url,host]

	def get_links(self,link,pageNum):
		"""
		https://ecchi.iwara.tv/users/%E5%92%95%E5%98%BF%E5%98%BF/videos?page=1
		https://ecchi.iwara.tv/users/forget-skyrim
		获取当前页面的iwara链接和页数
		视频不超过16个的用户,无videos页面
		"""
		href_list,title_list = [],[]
		resp = self.get_resp(link,headers=self.page_headers).text
		home_obj = etree.HTML(resp)
		home_expression = '//div[@id="block-views-videos-block-2"]//div[@class="more-link"]//a/@href'

		# 无效作者主页/无效视频
		if "ユーザーリスト | Iwara" in resp:
			return ["ErrorUserUrl"],0

		# 无videos页面 --> 获取用户主页视频
		if home_obj.xpath(home_expression) == []:
			# /videos/83wvbuz4yfl7bn3l
			href_expression = '//div[@id="block-views-videos-block-2"]//div[contains(@class,"views-responsive-grid")]//h3/a/@href' 
			title_expression = '//div[@id="block-views-videos-block-2"]//div[contains(@class,"views-responsive-grid")]//h3/a/text()' 
			if home_obj.xpath(href_expression) != []:
				href_list = [f"{self.iwara_host}{r}" for r in home_obj.xpath(href_expression)]
				logger.info(f"User Have {len(href_list)} Videos. Not Video Page")
				# 转义html字符
				title_list = [self.get_title(href) for href in href_list]

				# 补充无Video Page的业务跳出条件
				total_pageNum = -1
			# 用户无视频
			else:
				logger.info("User Not Have Video")
				return [],0
		# 有videos页面 --> 获取用户videos页面链接
		else:
			useVideoUrl = home_obj.xpath(home_expression)[0].split("?")[0]
			page_link = self.host.format(useVideoUrl,pageNum)

			obj = etree.HTML(self.get_resp(page_link,headers=self.page_headers).text)
			
			href_list = ["{}{}".format(self.iwara_host,r) for r in obj.xpath("//h3[@class='title']/a/@href")]
			# logger.info(f"Page Have {len(href_list)} Videos")
			# 转义html字符
			title_list = [dealwith_title(r) for r in obj.xpath(""".//div[@class='field-item even']/a/img/@title""")]
			# 页数
			try:
				total_pageNum = int(obj.xpath("//li[@class='pager-last last']//@href")[0].split("page=")[-1])
			except:
				# logger.warning(f"User Have Video Page. LastOne - {page_link}")
				logger.info(f"<User Videos Last PageNum>: {int(self.page_num)+1}/{int(self.page_num)+1} <Current Page Video>: {len(href_list)}")
				# 最后一页
				total_pageNum = -1
			else:
				logger.info(f"<User Videos PageNum>: {int(pageNum)+1}/{int(total_pageNum)+1} <Current Page Video>: {len(href_list)}")



		res = []
		for h,t in zip(href_list,title_list):
			res.append({"link":h,"title":f"{t}--{h.split('videos/')[-1].split('?')[0]}"})

		logger.debug("Exit Function")
		return res,total_pageNum

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
		:params link: 作者主页链接 / 视频链接
		:return :原始链接 or 包含作者视频链接的列表

		链接类型
			1、作者主页 https://ecchi.iwara.tv/users/xxxx
			
			更改获取videos页面的逻辑,改为从作者主页获取
			+ 作者主页: https://ecchi.iwara.tv/users/forget-skyrim
			+ videos页面会发生变化: https://ecchi.iwara.tv/users/Forget%20Skyrim./videos
			
			2、单个视频链接 https://ecchi.iwara.tv/videos/xxxx
		"""
		user_video_links = []
		if "/users" in link:
			logger.debug(f"<link>:{link} type:User")
			pageNum = 0
			while True:
				page_video_links,total_pageNum = self.get_links(link,pageNum)
				user_video_links.extend(page_video_links)
				pageNum += 1
				self.page_num = total_pageNum
				# 业务跳出条件
				if self.page_num == -1:
					break

				# 无效用户/视频链接 用户无视频
				if user_video_links == [] and \
					page_video_links == [] and \
					total_pageNum == 0:
					break

			# 用户无视频
			if user_video_links == []:
				return "EmptyVideoLinks"

			# 无效作者主页/视频链接
			if user_video_links[0] == "ErrorUserUrl":
				return "ErrorUserUrl"

			# 创建作者目录
			user_path = self.check_folder(link)
			for video in user_video_links:
				video["path"] = user_path
			# [{link, title, path}, {...}, ...]
			return user_video_links

		logger.debug(f"<link>:{link} type:Video")
		# 视频链接
		title = self.get_title(link)
		
		# 无效的视频链接
		if title == "Iwara":
			return "ErrorVideoUrl"
		# err code
		elif title in self.error_code_list.keys():
			return title

		return [{"link":link, "title":f"{title}--{link.split('videos/')[-1].split('?')[0]}", "path":self.root_path}]

	def download(self,args,source_url,file_path):
		"""
		下载原始视频
		"""
		response = self.get_resp(source_url,headers=self.page_headers,stream=True)
		logger.info(f"视频标题: {args[0]['title']} - 大小: {byte2size(response.headers['content-length'])} 正在下载")

		# content_size = int(response.headers['content-length']) # 获得文件大小(字节)
		# data_count = 0	# 计数
		chunk_size = 1024 # 每次最大请求字节
		with open(file_path, "wb") as file:
			for data in response.iter_content(chunk_size=chunk_size):
				file.write(data)
		return response

	@logger.catch
	def iwara_process(self, *args):
		"""
		子线程任务函数
		"""
		link, title, path = args[0]["link"], args[0]["title"], args[0]["path"]
		file_path = f"{os.path.join(path, title)}.mp4"
		logger.debug(f"<file_path> - {file_path}")
		logger.debug(f"<link> - {link}")

		# 检测本地文件
		isExists = False
		video_id = title.split("--")[-1]
		path_expression = os.path.join(path, f"**--{video_id}.mp4")

		for fn in glob.glob(path_expression):
			isExists = True
			break

		if isExists and os.path.getsize(glob.glob(path_expression)[0]) > 100000:
			logger.success(f"视频标题: {title} 已存在")
			return 

		try:
			data = self.get_data(link)
			# err code
			if type(data) == type("") and data in self.error_code_list.keys():
				err_code = self.error_code_list.get(data,'NotFoundErrorCode')
				logger.info(f"视频标题: {title} | err_code: {err_code}")
				return
			else:
				source_url,host = data[0],data[1]
		except Exception as e:
			logger.warning(f"Exception - {e}")
			return 
		else:
			try:
				response = self.download(args,source_url,file_path)
			except Exception as e:
				logger.warning(f"视频标题: {title} 视频下载失败,将在其他任务完成后进行重试.")
				logger.error(f"""错误视频链接: {link} - 视频标题: {title} - """\
						f"""服务器:{byte2size(response.headers['content-length'])} - 本地:{byte2size(os.path.getsize(file_path))}""")
				if not check_errTask_exists(args, ERR_TASK_LIST):
					ERR_TASK_LIST.append({"args": args, "count": RETRY_COUNT})
				# os.remove(file_path)
			else:
				# 3.9 视频完整性校验
				if not check_video(response, file_path):
					logger.warning(f"视频标题: {title} 视频完整性校验失败,将在其他任务完成后进行重试.")
					logger.error(f"""错误视频链接: {link} - 视频标题: {title} - """\
						f"""服务器:{byte2size(response.headers['content-length'])} - 本地:{byte2size(os.path.getsize(file_path))}""")
					if not check_errTask_exists(args, ERR_TASK_LIST):
						ERR_TASK_LIST.append({"args": args, "count": RETRY_COUNT})
					os.remove(file_path)
				else:
					logger.success(f"视频标题: {title} - {byte2size(response.headers['content-length'])}下载成功 让我歇歇,冲不动了~")
					
			# 判断/移除重试任务
			logger.debug(f"ERR_TASK_LIST 错误重试任务剩余: {len(ERR_TASK_LIST)}个")
			logger.debug(ERR_TASK_LIST)
			for _ in ERR_TASK_LIST[::]:
				if args == _["args"]:
					if _["count"] == 0:
						ERR_TASK_LIST.remove(_)
						logger.warning(f"视频标题: {title} 下载失败,无重试次数. 请参考log文件夹下的ERROR日志~")
					else:
						logger.warning(f"视频标题: {title} 剩余重试次数: {_['count']}次")
						_["count"] -= 1
						return self.iwara_process(*args)
					break

			time.sleep(0.5)

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
		pool = ThreadPool(THREAD_NUM)
		# 下载
		try:
			for link in self.original_links:
				# i站相关链接下载
				if link.startswith("https://ecchi.iwara.tv/"):
					logger.debug(f"<iwara url> - {link}")
					link_list = self.conver_link(link)

					# err code
					if type(link_list) == type("link_list") and link_list in self.error_code_list.keys():
						err_code = self.error_code_list.get(link_list,"NotFoundErrorCode")
						logger.info(f"【{link}】 {err_code}")
						continue

					# thread working
					if link_list != []:
						logger.info(f"<len_link_list> - {len(link_list)}")
						logger.debug(f"link_list - {link_list}")
						
						for l in link_list:
							pool.put(self.iwara_process, (l, ), callback)
		except Exception as e:
			logger.warning(f"Exception - {e}")
		# 错误重试
		else:
			logger.debug(ERR_TASK_LIST)
			for l in ERR_TASK_LIST:
				pool.put(self.iwara_process, (l, ), callback)
		finally:
			pool.close()


if __name__ == '__main__':
	logger.success(f"=== 欢迎使用< iwara下载脚本 {VERSION} > ===")
	logger.success(f"Github地址: https://github.com/WriteCode-ChangeWorld/Tools 欢迎Star~")

	logger.info("下载作者视频则输入作者主页链接...")
	logger.info("如: https://ecchi.iwara.tv/users/qishi\n")
	logger.info("下载单个视频则输入视频链接...")
	logger.info("如: https://ecchi.iwara.tv/videos/4kbwafpkz0tyv3k4m\n")
	logger.info("输入完成后,请输入'go'以开始下载...")
	# https://ecchi.iwara.tv/users/%E8%B4%BE%E5%94%AF%E2%84%A1 含private视频
	# https://ecchi.iwara.tv/users/qishi
	
	input_links = []
	while True:
		input_iwara_link = input("现在输入Iwara链接: ")
		if input_iwara_link == "":
			pass
		elif input_iwara_link == "go":
			logger.info("开冲!~ (*^▽^*)")
			break
		else:
			input_links.append(input_iwara_link)

	logger.info("现在开始获取链接,请稍后...")
	IDLoader = IwaraDownloader(input_links)
	IDLoader.main()