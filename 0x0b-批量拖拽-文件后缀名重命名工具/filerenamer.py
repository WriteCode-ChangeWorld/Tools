# -*- encoding: utf-8 -*-
'''
@File    :   filerenamer.py
@Time    :   2024/09/06 21:29:04
@Author  :   Coder-Sakura
@Version :   1.0
@Desc    :   None
'''

# here put the import lib
import wx
import os
import re
from datetime import datetime
from loguru import logger


# 配置loguru日志
logger.add("{time}.log",encoding="utf-8",enqueue=True)
# 跳过名单 , "."
skip_formats = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".zip", ".rar", ".7z", ".tar.gz", ".EXE", ".exe",\
                ".png", ".jpg", ".jpeg", ".gif", ".ico", ".psd", ".webp", ".mp3", ".wav", ".ass", ".lrc",\
                ".vtt", ".WAV", ".html"}
# 检测名单
target_formats = {".zi", ".rr"}
# 无后缀名时默认添加的后缀名
default_suffix = ".zip"


class FileDrop(wx.FileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        # super(FileDropTarget, self).__init__()
        self.window = window

    def OnDropFiles(self, x, y, files):
        """处理拖放的文件"""
        self.window.WriteLog(f"============ 运行开始 ============\n")
        if files:
            for file in files:
                if os.path.isdir(file):
                    self.window.WriteLog(f"识别到文件夹 - {file}\n")
                    for r, ds, fs in os.walk(file):
                        for f_ in fs:
                            full_f_ = os.path.join(r,f_)
                            self.window.WriteLog(f"识别到文件 - {full_f_}")
                            self.window.RenameFile(full_f_)
                else:
                    self.window.WriteLog(f"识别到文件 - {file}")
                    self.window.RenameFile(file)

            # 返回True表示成功处理了拖放的文件
            self.window.WriteLog(f"============ 运行结束 ============\n")
            return True
        
        # 返回False表示没有文件被拖放
        self.window.WriteLog(f"============ 运行结束 ============\n")
        return False


class DropFile(wx.Frame):
    # def __init__(self, parent, id, title):
        # wx.Frame.__init__(self, parent, id, title, size = (450, 400))
    def __init__(self, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)
        self.InitUI()

    def InitUI(self):
        self.title = "文件重命名工具"

        # 启用拖放
        self.text = wx.TextCtrl(self, -1, style = wx.TE_MULTILINE | wx.TE_RICH)
        self.text.SetBackgroundColour(wx.Colour(200, 200, 200))
        dt = FileDrop(self)
        self.text.SetDropTarget(dt)

        # 设置窗口大小和位置
        self.Centre()
        self.SetSize((800, 400))
        self.SetTitle(self.title)
        self.Show(True)

    def WriteLog(self, text, color=""):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start = self.text.GetInsertionPoint()   # 获取当前文本位置
        attr = wx.TextAttr()
        attr.SetTextColour(wx.Colour(255, 0, 0))  # 红色
        attr.SetTextColour([wx.Colour(255, 0, 0) if color == "red" else wx.Colour(0, 0, 255) if color == "blue" else wx.Colour(0, 0, 0)][0])  # 红/蓝/黑
        self.text.WriteText(f"{now} {text}\n")
        self.text.SetStyle(start, start + len(now+text), attr)  # 插入文本并应用样式

    def RenameFile(self, file_path):
        dir,fullfname = os.path.split(file_path)
        fname,ext = os.path.splitext(fullfname)
        # logger.info(f"检测到文件 - {dir}|{fullfname}|{fname}|{ext}")
        # return

        # ================= 后缀名处理 ================= #
        # 跳过名单的后缀名 -> 跳过
        if ext in skip_formats:
            self.WriteLog(f"跳过文件 - {file_path}\n")
            return 

        # 无后缀名 -> 添加默认后缀名
        if not ext and fullfname == fname:
            dst = os.path.join(dir, f"{fname}{default_suffix}")
            os.rename(file_path, dst)
            self.WriteLog(f"添加后缀名 - {dst}\n", color="blue")
            logger.success(f"添加后缀名 - {dst}")
            return 
        
        # 全中文后缀名/检测名单的后缀名 -> 修改为默认后缀名
        if bool(re.match(r"^[\u4e00-\u9fa5]+$", ext[1:])) \
            or ext in target_formats:
            dst = os.path.join(dir, f"{fname}{default_suffix}")
            os.rename(file_path, dst)
            self.WriteLog(f"重命名文件 - {dst}\n", color="blue")
            logger.success(f"重命名文件 - {dst}")
            return 

        # 部分中文后缀名 -> 去除中文
        if bool(re.findall(r"[\u4e00-\u9fa5]", ext[1:])):
            new_ext = re.sub(r"[\u4e00-\u9fa5]", "", ext)
            dst = os.path.join(dir, f"{fname}{new_ext}")
            os.rename(file_path, dst)
            self.WriteLog(f"重命名文件 - {dst}\n", color="blue")
            logger.success(f"重命名文件 - {dst}")
            return 

        self.WriteLog(f"未知类型 - {file_path}\n", color="red")
        logger.warning(f"未知类型 - {file_path}")
        return


app = wx.App()
DropFile(None, -1, 'filedrop.py')
app.MainLoop()