import os
import re
import time
import requests
from lxml import etree
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

default_headers = {
	"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
	"referer":"https://ca.gca.tw",
}

def log_str(*args,end=None):
    for i in args:
        print('[{}] {}'.format(time.strftime("%Y-%m-%d %H:%M:%S"),i),end=end)

def net_requests(options,method="GET",data=None,headers=default_headers,stream=False,retry_num=5):
	try:
		# se = requests.session()
		response = requests.request(
				method,
				options["url"],
				data = data,
				headers = headers,
				stream = stream,
				verify = False,
				timeout = 10,
			)
		response.encoding = "utf8"
		return response
	except Exception as e:
		if retry_num > 0:
			return net_requests(options,method,data,headers,stream,retry_num-1)
		else:
			log_str("网络请求出错 url:{}".format(options["url"]))
			return None

def stream_process(word,url,path):
	# 每次最大请求字节
	chunk_size = 1024
	# 网络请求
	response = net_requests(options={"url":url},stream=True)
	if response == None:
		return "NetWorkError"
	# 获得本次请求的字节
	content_size = int(response.headers['content-length'])
	data_count = 0
	
	with open(path, "wb") as file:
		for data in response.iter_content(chunk_size=chunk_size):
			file.write(data)
			data_count = data_count + len(data)
			now = (data_count / content_size) * 100
			print("\r%s下载进度:%d%%" % (word,now), end=" ")
	print("—— {}下载完成".format(word))
	return response


class GCA:
	"""绅士小站"""
	def __init__(self):
		self.HOST = "https://ca.gca.tw"
		self.host = "https://ca.gca.tw/page/{}"
		self.root_path = os.getcwd()

		# cover封面图 article_url文章链接 title文章标题
		self.expression = """//div[@class='simple-grid-posts simple-grid-posts-grid']/div"""
		# self.cover_expression = """.//img//@src"""
		self.article_url_expression = """.//div//a//@href"""
		self.title_expression = """.//h3//a/text()"""
		# video封面&video链接
		self.video_cover_expression = """//span[@class='arve-embed']/meta[@itemprop="thumbnailUrl"]/@content"""
		self.video_cover_expression_second = """//figure[@class="wp-block-video"]/video/@poster"""

		self.video_url_expression = """//span[@class='arve-embed']/meta[@itemprop="contentURL"]/@content"""
		self.video_url_expression_second = """//figure[@class="wp-block-video"]/video/@src"""

	def download(self,path,content):
		with open(path,"wb") as f:
			f.write(content)

	def folder(self,title):
		title = re.sub(r'[\/:*?"<>|]','',title)
		title = title.replace(".","")
		target = os.path.join(self.root_path,title)
		isExists = os.path.exists(target)
		if not isExists:
			os.mkdir(target)
		return target

	def get_html(self,article_url,title):
		"""获取输入密码后的html"""
		action_url = "https://ca.gca.tw/wp-login.php?action=postpass"
		headers = {
			"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
			"referer":article_url,
		}
		data = {
			"post_password":title, # 密码
		}

		resp = net_requests(options={"url":action_url},method="POST",data=data,headers=headers)
		return resp

	def main(self):
		"""主流程"""
		offset = 1
		all_info_list = []

		while True:
			page_url = self.host.format(offset)
			obj = etree.HTML(net_requests(options={"url":page_url}).text)
			article_list = obj.xpath(self.expression)
			log_str("当前第{}页,共{}篇文章".format(offset,len(article_list)))

			for article in article_list:
				# article_url
				try:
					article_url = article.xpath(self.article_url_expression)[0]
				except Exception as e:
					article_url = ""
				# title
				try:
					title = article.xpath(self.title_expression)[0]
				except Exception as e:
					title = ""
				info = {"article_url":article_url,"title":title}
				all_info_list.append(info)

			# 最后一页小于60页,则跳出
			if len(article_list) < 60:
				log_str("全站文章获取完毕...共{}页{}个".format(offset,len(all_info_list)))
				break

			offset += 1
			# break # 测试
			time.sleep(1)

		if all_info_list == []:
			log_str("获取到的文章为空,可能是网站结构发现变化或其他原因")
			exit()

		# ============# start ============ #
		"""
		文件夹 --> title(文件夹名称)
		视频 --> article_url(文章链接),title(密码) --> 后面获取的视频链接
		"""
		for index,info in enumerate(all_info_list):
			log_str("({}/{}){} {} ".format(index+1,len(all_info_list),info["title"],info["article_url"]))
			if info["article_url"] == "" and info["title"] == "":
				log_str("当前文章标题及链接获取有误,将跳过")
				continue

			# 创建文章文件夹,title过滤一些字符
			article_path = self.folder(info["title"])
			# 获取页面解密后的html,原始title用于解密
			resp = self.get_html(info["article_url"],info["title"])
			obj = etree.HTML(resp.text)

			# video_cover视频封面
			try:
				video_cover = obj.xpath(self.video_cover_expression)
				if video_cover == []:
					video_cover = obj.xpath(self.video_cover_expression_second)
			except Exception as e:
				video_cover = []
			# video_url
			try:
				video_url = obj.xpath(self.video_url_expression)
				if video_url == []:
					video_url = obj.xpath(self.video_url_expression_second)
			except Exception as e:
				video_url = []

			if video_cover == [] and video_url == []:
				log_str("当前文章无视频及视频封面,将跳过")
				continue
			# log_str("video_cover: {} video_url: {}".format(video_cover,video_url))
			
			# 下载视频封面video_cover
			cover_path = os.path.join(article_path,"{}.jpg".format(info["title"]))
			if os.path.exists(cover_path) == False or os.path.getsize(cover_path) < 1000:
				try:
					video_cover = video_cover[0]
					video_cover = self.HOST + video_cover
					response = stream_process("视频封面",video_cover,cover_path)
				except Exception as e:
					log_str("video_cover: {}".format(video_cover))
					log_str(e)
			else:
				pass
				# log_str("视频封面已存在")

			# 下载视频
			video_path = os.path.join(article_path,"{}.mp4".format(info["title"]))
			if os.path.exists(video_path) == False or os.path.getsize(video_path) < 1000:
				try:
					video_url = video_url[0]
					response = stream_process("视频",video_url,video_path)
					if response == "NetWorkError":
						continue
					time.sleep(3)
				except Exception as e:
					log_str("video_url: {}".format(video_url))
					log_str(e,response)
			else:
				pass
				# log_str("视频已存在")

			# break # 测试
		# =============# end ============= #
			
		
gca = GCA()
gca.main()