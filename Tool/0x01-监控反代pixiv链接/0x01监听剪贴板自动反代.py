import win32clipboard as wc
import time
import re

"""
__author__:Coder-Sakura
__time__:2020/07/06 00:44:53
监听所复制的pixiv插画地址,并将其反代成无需梯子即可访问的反代链接.
比如:
在pixiv复制了https://i.pximg.net/img-master/img/2020/07/01/21/08/21/82688845_p0_master1200.jpg
脚本会转换为https://i.pixiv.cat/img-master/img/2020/07/01/21/08/21/82688845_p0_master1200.jpg
会自动拷贝到剪贴板.
"""

#获取粘贴板里的内容
def getCopyTxet():
    # 异常则关闭,防止因为复制文件/文件夹/图片/视频等非文本类型文件而崩溃
    wc.OpenClipboard()
    try:
        copytxet = wc.GetClipboardData()
    except:
        wc.CloseClipboard()
    else:
        wc.CloseClipboard()
        return copytxet

def setText(text):
    wc.OpenClipboard()  
    wc.EmptyClipboard()  
    wc.SetClipboardText(text)  
    wc.CloseClipboard()  

def r_sub(text):
    return re.sub(r"pximg.net","pixiv.cat",text)

if __name__ == '__main__':
    # 存储上次剪切板内容
    last_data = None
    while True:
        # 轮询
        time.sleep(1)
        data = getCopyTxet()
        if data == None:
            continue

        if data != last_data:
        # 如果内容和上次的不同
            print("剪贴板内容为：\n" + data,'\n')

        if "https://i.pximg.net" in data:
            data = r_sub(data)
            setText(data)
            print("反代链接替换成功:",data,'\n')

        last_data = data