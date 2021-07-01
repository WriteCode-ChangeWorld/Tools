# coding=utf-8
import os
import re
import Kit
import stat
import zipfile
import requests
import subprocess
from selenium import webdriver

# 引入Windows特定库
if Kit.run_platform() == "windows":
    import winreg

# 全局变量
version_re = re.compile(r'^[1-9]\d*\.\d*.\d*')


def run_browser(driver_path, headless="Yes"):
    driver_path = os.path.abspath(driver_path) + "/chromedriver"
    option = webdriver.ChromeOptions()
    if headless == "Yes":
        option.add_argument('--headless')
    option.add_argument('--no-sandbox')
    option.add_argument('--disable-gpu')
    browser = webdriver.Chrome(driver_path, options=option)
    return browser


def env_check(cache_path):
    print("[INFO]", "Check chrome driver env...")
    cache_path = os.path.abspath(cache_path)

    chrome_version = get_chrome_version()
    driver_version = get_driver_version(cache_path)

    if chrome_version == "0":
        print("[INFO]", "Please install chrome browser")
        return False

    if driver_version == "0":
        # Download driver
        print("[INFO]", "Download chrome driver")
        return download_driver(chrome_version, cache_path)

    if version_re.findall(chrome_version)[0] != version_re.findall(driver_version)[0]:
        # Update driver
        print("[INFO]", "Update chrome driver")
        return download_driver(chrome_version, cache_path)

    print("[INFO]", "Chrome driver check pass")
    return True  # Check success


def get_chrome_version():
    print("[INFO]", "Check chrome version...")
    if Kit.run_platform() == "windows":
        try:
            # 从注册表中获得版本号
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            version, _ = winreg.QueryValueEx(key, "version")

            print("[INFO]", "Current chrome Version: {}".format(version))  # 这步打印会在命令行窗口显示
            return version
        except WindowsError as e:
            print("[INFO]", "Check chrome failed:{}".format(e))
            return "0"
    else:
        try:
            cmd = r"google-chrome-stable --version"
            out, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            out = out.decode("utf-8")
            version = out.split(" ")[2]  # 拆分回显字符串，获取版本号
            print("[INFO]", "Current chrome Version:{}".format(version))
            return version
        except WindowsError as e:
            print("[INFO]", "Check chrome failed:{}".format(e))
            return "0"


def get_driver_version(driver_path):
    print("[INFO]", "Check driver version...")
    if Kit.run_platform() == "windows":
        try:
            # 执行cmd命令并接收命令回显
            cmd = r'"{}/chromedriver" --version'.format(driver_path)
            out, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            out = out.decode("utf-8")
            version = out.split(" ")[1]  # 拆分回显字符串，获取版本号
            print("[INFO]", "Current driver Version:{}".format(version))
            return version
        except IndexError as e:
            print("[INFO]", "Check driver failed:{}".format(e))
            return "0"
    else:
        try:
            # 执行cmd命令并接收命令回显
            cmd = r"{}/chromedriver --version".format(driver_path)
            out, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            out = out.decode("utf-8")
            version = out.split(" ")[1]  # 拆分回显字符串，获取版本号
            print("[INFO]", "Current driver Version:{}".format(version))
            return version
        except IndexError as e:
            print("[INFO]", "Check driver failed:{}".format(e))
            return "0"


def download_driver(version, driver_path):
    print("[INFO]", "Download driver on", Kit.run_platform())
    driver_path = os.path.abspath(driver_path)

    # 获取淘宝镜像列表
    http_res = requests.get("http://npm.taobao.org/mirrors/chromedriver")
    mirror_list = re.findall(r'<a href="/(.*)/">(.*)</a>', http_res.text)

    # 检索驱动版本列表
    url_path = ""
    version_prefix = version_re.findall(version)[0]
    for mirrors in mirror_list:
        if mirrors[1].startswith(version_prefix):
            url_path = mirrors[0]

    print("[INFO]", "Download driver version:", url_path.split("/")[-1])
    if Kit.run_platform() == "windows":
        file_url = "http://npm.taobao.org/{}/chromedriver_win32.zip".format(url_path)
    elif Kit.run_platform() == "linux":
        file_url = "http://npm.taobao.org/{}/chromedriver_linux64.zip".format(url_path)
    elif Kit.run_platform() == "darwin":
        file_url = "http://npm.taobao.org/{}/chromedriver_mac64.zip".format(url_path)
    else:
        print("[ERR]", "Not found chrome driver")
        return False

    print("[INFO]", "Download driver url:", file_url)
    driver_res = requests.get(file_url)

    # 写入压缩文件
    zip_path = driver_path + "/chromedriver.zip"
    zip_file = open(zip_path, "wb")
    zip_file.write(driver_res.content)
    zip_file.close()

    # 下载完成后解压
    zip_file = zipfile.ZipFile(zip_path, "r")
    for fileM in zip_file.namelist():
        zip_file.extract(fileM, os.path.dirname(zip_path))
    zip_file.close()

    # 删除残留文件
    os.remove(zip_path)

    # 授予执行权限
    if Kit.run_platform() == "linux":
        os.chmod(driver_path + "/chromedriver", stat.S_IXGRP)

    print("[INFO]", "Download chrome driver finish")
    return True
