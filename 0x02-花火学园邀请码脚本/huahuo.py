import requests,json
import random

url ="https://www.say-huahuo.com/qa.php"

headers = {
	"content-type":"application/json;charset=UTF-8",
	"user-agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3741.400 QQBrowser/10.5.3863.400",
}

se = requests.session()

doc = [
	{"title":"下列哪个数据类型占用内存空间最少","answer":"Byte"},
	{"title":"以下哪个不是世萌萌王获得者","answer":"木之本樱"},
	{"title":"この世の果てで恋を唄う少女YU-NO里的主角有马拓也被称为？","answer":"行走的性欲"},
	{"title":"key社的春夏冬秋四季分别是，CLANNAD、AIR、Kanon和____。 ","answer":"ONE～辉之季节～"},
	{"title":"《北斗神拳》中不属于健次郎的奥义的是","answer":"无明封杀阵"},
	{"title":"动画《干物妹！小埋》中，小埋的游戏名称是什么","answer":"UMR"},
	{"title":"《尘骸魔京》中追风者寻找的夫婿就是","answer":"九门克绮"},
	{"title":"《黑执事》中，伊丽莎白是","answer":"剑术天才"},
	{"title":"《黑执事》中称呼女装的夏尔为美丽小巧的知更鸟的是","answer":"阿雷斯特·钱帕"},
	{"title":"《近月少女的礼仪》中人物的名字与以下哪个相关","answer":"银行"},
	{"title":"《名侦探柯南》《少年侦探团》《文豪野犬》这三部动画都与以下那位作家有关联","answer":"太宰治"},
	{"title":"《天书奇谭》中刚出生的蛋生一开始吃了什么","answer":"大饼"},
	{"title":"ChuSingura46＋1中谁拯救了陷入绝望的直刃","answer":"主税"},
	{"title":"CLANNAD有多少集","answer":"49"},
	{"title":"在第三部jojo中DIO的the World最终暂停了几秒？","answer":"九秒"},
	{"title":"以下哪个动画不是游戏改编的？","answer":"2008年P.A.WORKS的真实之泪"},
	{"title":"中二社因为那部作品转变为巨乳社的？","answer":"sppl"},
	{"title":"下列哪一位是G吧大吧主？","answer":"ACG之神"},
	{"title":"请问论坛的通用解压密码是？","answer":"Say花火"},
	{"title":"下面哪个 jQuery 方法用于隐藏被选元素？","answer":"display(none)"},
	{"title":"传颂之物 二人的白皇中旧人类怎么样了？","answer":"没救了，都变树了"},
	{"title":"死に逝く君、館に芽吹く憎悪中，上位种族的弱点是什么？","answer":"血液"},
	{"title":"老虚是____。","answer":"爱的战士"},
	{"title":"动画《干物妹！小埋》中，被网友调侃为GBA的是在哪个场景？","answer":"开车去海边的时候"},
	{"title":"一休哥的法名是？","answer":"一休宗纯"},
	{"title":"《らぶらぶシスターズ ～花嫁＆姉妹達とのドキドキハーレム生活》中H了就会变瘦的妹子是？","answer":"模特妹妹"},
	{"title":"这幅画的作者是谁？","answer":"梵高"},
	{"title":"蹭的累是什么的谐音","answer":"腹黑"},
	{"title":"财团b指的是？","answer":"万代"},
	{"title":"正田崇是什么系的剧本家？","answer":"燃系"},
	{"title":"被誉为为神仙水的是？","answer":"SK-II"},
	{"title":"奇迹的世代不包括下面的谁？","answer":"火神大我"},
	{"title":"駄作中四个女主角中，哪一位是渴求别人的爱的怪物？","answer":"菜々ヶ木アリス"},
	{"title":"在Linux中，哪一个标记可以把该命令（组）作为子进程","answer":"&"},
	{"title":"下面哪个声优的给初音未来的歌曲提供了舞蹈动作？","answer":"小仓唯"},
	{"title":"以下哪个作品不含ntr？","answer":"纯白交响曲"},
	{"title":"哆啦A梦原来是啥颜色？","answer":"黄色"},
	{"title":"以下哪个角色出自约会大作战？","answer":"时崎狂三"},
	{"title":"请问论坛的学园长是？","answer":"Say花火"},
	{"title":"百合同人作品花吻在上的20部正作中，哪部于2010年8月被改编成OVA动画？","answer":"3"},
	{"title":"蜥蜴の尻尾切り中男主为什么痴迷于人体再生？","answer":"女朋友得癌症了"},
	{"title":"游戏Myself ; Yourself中若月修辅是____之一。","answer":"男主"},
	{"title":"在 PHP 中，所有的变量以哪个符号开头？","answer":"$"},
	{"title":"以下不是国产gal的是？","answer":"格林花园的少女"},
	{"title":"自称superai的人工智能叫什么名字？","answer":"绊爱"},
	{"title":"战极姬系列里哪部有NTR的感觉？","answer":"战极姬6"},
	{"title":"爱衣酱大胜利出自哪部番？","answer":"我的女友和青梅竹马的惨烈修罗场"},
	{"title":"g弦上的魔王被称为？","answer":"赌上性命的——纯爱"},
	{"title":"幸福噩梦中主人公前期靠什么识别梦和现实？","answer":"眼镜"},
	{"title":"gore screaming show里ユカ的真名是？","answer":"音无紫"},
	{"title":"以下不属于米泽円配过的音是","answer":"樱木由加利"},
	{"title":"鬼哭街中男主的绰号是？","answer":"紫电掌"},
	{"title":"下列每条选项的声优中，所属事务所完全不同的是","answer":"佐仓绫音 东山央奈 种田梨沙"},
	{"title":"清水爱不光是一位声优也是一名职业运动员，那么这门项目是什么？","answer":"体操"},
	{"title":"多啦A梦的体重是多少？","answer":"129.3斤"},
	{"title":"动画《山田君与7人魔女》里白石丽的能力是？","answer":"交换身体"},
	{"title":"在Fate HF线中，土狼说他喜欢谁？","answer":"樱"},
	{"title":"国内玩家对于《夏娃年代纪》里大公主的争议主要原因为？","answer":"ntr"},
	{"title":"贾宝玉身上佩戴的玉叫啥？","answer":"通灵宝玉"},
	{"title":"下面哪一部没有和泉万夜参与脚本？","answer":"maggot biats"},
	{"title":"下面哪一部不是钟表社的作品？","answer":"maggot biats"},
	{"title":"传颂之物中，谁和谁去开店了？","answer":"藤香和卡米拉"},
	{"title":"观沧海的作者是？","answer":"曹操"},
	{"title":"装甲恶鬼村正英雄篇中最后村正最后成为了谁的剑？","answer":"一条"},
	{"title":"哪个作品与田中罗密欧，龙骑士07，都乃河勇人三人都相关？","answer":"rewrite"},
	{"title":"日本同人漫画家二阶堂みつき和哪位漫画家关系最近？","answer":"大岛永远"},
	{"title":"苍翼默示录动漫是游戏里哪一部的主线剧情？","answer":"厄运扳机"},
	{"title":"以下那部漫画不是BL向作品？","answer":"累"},
	{"title":"下面那个不是新十年的假面骑士？","answer":"假面骑士Decade"},
	{"title":"渡りの诗是一首什么语言的歌？","answer":"包含多种"},
	{"title":"纸上魔法使中哪一个是？","answer":"游行寺夜子"},
	{"title":"恋樱中带来幸福的死神是？","answer":"缇娜"},
	{"title":"游戏《秘密の花园》里，女主是？","answer":"母亲和父亲生的"},
	{"title":"以下哪个加藤不存在于三次元？","answer":"加藤断"},
	{"title":"以下哪个人物和佐伯克哉出现在同一款游戏里？","answer":"御堂孝典"},
	{"title":"以下哪个是Cross Days里的可攻略对象？","answer":"伊藤诚"},
	{"title":"以下哪个不是百合作品？","answer":"処女はお姉さまに恋してる"},
	{"title":"以下哪个不是elf会社的作品？","answer":"トラク=ナクア."},
	{"title":"以下四个角色哪个喜欢女性？","answer":"佐藤圣"},
	{"title":"多啦A梦2012年剧场版中出现的稀有独角仙叫啥？","answer":"黄金赫拉克勒斯"},
	{"title":"关于特摄假面骑士中骑士的安全区是下列那个地点？","answer":"水域"},
	{"title":"以下哪位导演没有参与异形系列？","answer":"昆汀·塔伦蒂诺"},
	{"title":"被钉X型十字架殉道的是？","answer":"圣安德烈"},
	{"title":"该场景出现时真白说的第一句话是什么？","answer":"呐，你想成为什么颜色？"},
	{"title":"提起法国剧作家罗斯丹的代表作《西哈诺》，你会想到以下哪部galgame？","answer":"美好的每一天"},
	{"title":"下列歌手不是隶属于Sony音乐旗下的是","answer":"春奈露娜"},
	{"title":"2017年7月20日发售的扶她百合游戏名为？","answer":"戦国の黒百合～ふたなり姫忍ぶ少女達～"},
	{"title":"被称为西域战神的是？","answer":"阿古柏"},
	{"title":"下面哪条 SQL 语句用于在数据库中插入新的数据？","answer":"INSERT NEW"},
	{"title":"星之卡比中，卡比吞下小怪之后会发生什么","answer":"变身"},
	{"title":"超炮中被称为海澜之家和上升气流lv6的是？","answer":"佐天泪子"},
	{"title":"“所谓的人类,是连短短的十分钟也等不起的！”出自？","answer":"AngleBeats!"},
	{"title":"生天目仁美曾为四大百合女王中的哪个配音？","answer":"花园静马"},
	{"title":"前前前世出自哪部电影？","answer":"你的名字"},
	{"title":"世界上最ng恋爱是哪位脚本作家的作品？","answer":"丸户史明"},
	{"title":"Teaching Feeling中最有名的动作是","answer":"摸头"},
	{"title":"与今野绪雪所写的女校故事《玛利亚的凝望》所对应的男校故事名为？","answer":"释迦摩尼也凝望"},
	{"title":"胃药魔女冈田磨里的成名作是什么？","answer":"真实之泪"},
	{"title":"动画《奇幻贵公子》的主角涉谷一也，被女主称为Naru的原因为。","answer":"百合熊岚"},
	{"title":"以下那部不是15年的动漫四大名著？","answer":"自恋"},
	{"title":"游戏《白色相簿》中，绪方理奈的职业是？","answer":"人气偶像"},
	{"title":"欧派星人是哪位画师？","answer":"西又葵"},
	{"title":"C3-魔方少女中的女主角是谁？","answer":"菲娅"},
	{"title":"妖精森林的小不点第八集中，什么使两派人和好？","answer":"蜂蜜酒"},
	{"title":"动画《绝园的暴风雨》里，不破爱花经常爱引用____的句子。","answer":"哈姆雷特"},
	{"title":"下面哪个与游戏主题无关？","answer":"ReLIFE"},
	{"title":"Gamers!第八集中，出现的key社作品为？","answer":"CLANNAD"},
	{"title":"“エル・プサイ・コングルゥ!”出自？","answer":"Steins;Gate"},
	{"title":"以下那作不是KEY社作品？","answer":"《Clover Day’s》"},
	{"title":"《近月少女的礼仪》中人物的名字与以下哪个有关？","answer":"寺庙"},
	{"title":"下面的四位中的那位是其中最漂亮的女主？","answer":"立华奏"},
	{"title":"斯特拉的魔法中，SNS部之前的作品叫什么？","answer":"TEARMENT TEARSTAR"},
	{"title":"小邪神飞踢！第二季中，出现的新人物名字叫什么？","answer":"僵僵"},
	{"title":"学园长花火喜欢____。","answer":"巨乳"},
	{"title":"在小说マリア様がみてる中出现的，小笠原祥子的胸围是？","answer":"65D"},
	{"title":"约会大作战小说第21卷结束时中谁已经死了？","answer":"冰芽川四糸乃"},
]

resp = se.get(url).text
j = json.loads(resp)

data = []
for k,i in enumerate(j):
	d = {}
	# print(i["code"])
	# print(i["title"])
	# print(i["options"])
	for qa in doc:
		# print(i["title"],len(i["title"]))
		# print(qa["title"],len(qa["title"]))
		question = i["title"]
		question = i["title"].replace("？","")
		if question in qa["title"]:
			d["answer"] = qa["answer"]
			# print(d["answer"])
			break
	else:
		print(question)
		print("\n当前第{}题不在题库中...".format(k+1))
		print("题目为: ",i["title"])
		print("选项为: ",i["options"])
		print("第一项输入1,第二项输入2,第三项输入3,第四项输入4")
		num = input("选择答案项: ")
		if num == "":
			d["answer"] = random.choice(i["options"])
		else:
			n = int(num)-1
			d["answer"] = i["options"][n]
			d["answer"] = i["options"][n]
		
	d["code"] = i["code"]
	data.append(d)
	# break

p_resp = se.post(url,headers=headers,json=data).text
res = json.loads(p_resp)
print("考试分数为: ",res["score"])
print("获得邀请码: ",res["invitecode"])
# print(p_resp.text)