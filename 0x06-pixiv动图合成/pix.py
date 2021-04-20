import os
import json
import zipfile
import imageio
import requests

class Pixiv_Gif:
	def __init__(self):
		self.headers = {
			# "cookie":"irst_visit_datetime_pc=2021-01-18+23%3A46%3A22; p_ab_id=4; p_ab_id_2=1; p_ab_d_id=1174719623; yuid_b=JVZjaQc; c_type=21; a_type=0; b_type=0; __utma=235335808.1683020896.1611026902.1611026902.1611026902.1; __utmz=235335808.1611026902.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmv=235335808.|3=plan=normal=1^6=user_id=27858363=1^11=lang=zh=1; login_ever=yes; PHPSESSID=27858363_yDl8WSYNlr2COVTjHHENyDFS9vYBmf3E; privacy_policy_agreement=2; __cfduid=d788199f9cb94e1c9fe4771d24633d2f31613573687; p_b_type=1; __cf_bm=570419761d3f9b0aecc8f92429e5c40fe20c142d-1614658458-1800-AYaL7o9FG66P0Z2Zv/IpHa8yZzNWKXRxzJLrZgSwnfV5BPsgmrFF9Yod5ZkXVBsfW/j6aBM9P38rwLbLNRwqTkNalbMMBLglxJq14e9kn0iu; tag_view_ranking=0xsDLqCEW6~_EOd7bsGyl~Lt-oEicbBr~tgP8r-gOe_~KN7uxuR89w~uusOs0ipBx~jhuUT0OJva~yTFlPOVybE~eVxus64GZU~RcahSSzeRf~BSlt10mdnm~Ie2c51_4Sp~RokSaRBUGr~RTJMXD26Ak~KOnmT1ndWG~5oPIfUbtd6~ziiAzr_h04~yroC1pdUO-~O2wfZxfonb~faHcYIP1U0~7Y-OaPrqAv~-TeGk6mN86~jk9IzfjZ6n~PHQDP-ccQD~zZZn32I7eS~aPdvNeJ_XM~txZ9z5ByU7~dK-VDbfFxD~zIv0cf5VVk~zyKU3Q5L4C~r01unnQL0a~qNQ253s6b0~Bd2L9ZBE8q~HY55MqmzzQ~AI_aJCDFn0~WVrsHleeCL~m3EJRa33xU~y8GNntYHsi~52-15K-YXl~WcTW9TCOx9~UX647z2Emo~skx_-I2o4Y~2EpPrOnc5S~M_kcfifITK~QaiOjmwQnI~CrFcrMFJzz~_vCZ2RLsY2~ouiK2OKQ-A~tL0dW9hy1Z~v3nOtgG77A~3cT9FM3R6t~q303ip6Ui5~m47KFuLUuf~sOBG5_rfE2~BU9SQkS-zU~FqVQndhufZ~3gc3uGrU1V~cofmB2mV_d~AYsIPsa0jE~PvCsalAgmW~rNs-bh_gk3~MM6RXH_rlN~4QveACRzn3~ePN3h1AXKX~0NVHtCi70U~leIwAgTj8E~TqiZfKmSCg~lz1iXPdNUF~F-9IXA9R-9~Qg95CBAuxh~ZQorENB8GQ~8EI9ovnGxw~-0JKThjl-M~tTvZK72fmv~D0nMcn6oGk~EZQqoW9r8g~QniSV1XRdS~5BhtaeNUYC~_3oeEue7S7~vzTU7cI86f~KhVXu5CuKx~rOnsP2Q5UN~-StjcwdYwv~cbmDKjZf9z~azESOjmQSV~GFExx0uFgX~u8McsBs7WV~04qbH3MKfd~d2ro84lQRz~96TwI9y7eq~6qxeznuWaX~L7-FiupSjg~y3NlVImyly~FPCeANM2Bm~X_1kwTzaXt~-MuiEJf_Sr~0F4QqxTayD~mzJgaDwBF5~YHRjLHL-7q~g5izzko3j2",
			"user-agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3741.400 QQBrowser/10.5.3863.400",
			"referer":"https://www.pixiv.net"
		}
		self.zip_url = "https://www.pixiv.net/ajax/illust/{}/ugoira_meta"

		for _ in ["gif","zip"]:
			_path = os.path.join(os.getcwd(),_)
			if not os.path.exists(_path):
				os.mkdir(_path)

		self.gif_path = os.path.join(os.getcwd(),"GIF")
		self.zip_path = os.path.join(os.getcwd(),"ZIP")

	def get_url_data(self,url,retry_num=3):
		try:
			resp = requests.get(url,headers=self.headers,timeout=15)
		except Exception as e:
			if retry_num > 0:
				return self.get_url_data(url,headers,retry_num=retry_num-1)
			else:
				print("网络出错,超过重试次数")
				exit()
		else:
			return resp

	def main(self,pid):
		resp = self.get_url_data(self.zip_url.format(pid))
		zip_name = "{}.zip".format(pid)
		zipfile_path = os.path.join(self.zip_path,zip_name)
		gif_name = '{}.gif'.format(pid)
		giffile_path = os.path.join(self.gif_path,gif_name)

		# delay
		gif_info = json.loads(resp.text)
		delay = [item["delay"]/1000 for item in gif_info["body"]["frames"]]
		print("delay list:\n",delay)

		# download zip
		zip_originalSrc = gif_info["body"]["src"]
		zip_resp = self.get_url_data(zip_originalSrc)
		with open(zipfile_path,'ab') as f:
			f.write(zip_resp.content)

		# extract zip & delete zip
		with zipfile.ZipFile(zipfile_path,'r') as f:
			for file in f.namelist():
				f.extract(file,self.zip_path)
		os.remove(zipfile_path)

		# composite gif
		images = []
		files = os.listdir(self.zip_path)
		print("extract list:\n",files)
		for file in files:
			file_path = os.path.join(self.zip_path,file)
			images.append(imageio.imread(file_path))
		imageio.mimsave(giffile_path,images,duration=delay)

		# delete extract file
		for file in files:
			os.remove(os.path.join(self.zip_path,file))

		# success
		print("Download Success\n{}".format(giffile_path))

PG = Pixiv_Gif()

if __name__ == '__main__':
	print("输入q以退出")
	print("接下来粘贴你要下载的动图pid吧！")
	while True:
		pid = input("\n现在输入:")
		if pid == "":
			print("pid not null")
			exit()
		elif pid == "q":
			print("退出成功")
			exit()
		else:
			PG.main(pid=pid)