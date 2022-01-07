# -*- encoding: utf-8 -*-
'''
@File    :   blhx_img_tool.py
@Time    :   2021/12/24 17:07:46
@Author  :   Coder-Sakura
@Version :   1.1
@Desc    :   碧蓝航线静态立绘加解密工具
'''

# here put the import lib
import os
import cv2
import sys
import time
import shutil
import numpy as np
from loguru import logger


# DEBUG
DEBUG = False

# log config
level = "DEBUG" if DEBUG else "INFO"
logger.remove()
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
    level="INFO"
)


class tool:
    """公共方法"""
    check_list = [
        "Mesh",         # obj文件
        "Picture",      # 解密立绘
        "Texture2D",    # 加密立绘
        "Used"          # 处理过的加密立绘
        ]

    def __init__(self):
        self.check_folders()

    def check_folders(self):
        """检查文件夹"""
        for i in tool.check_list:
            _ = os.path.join(os.getcwd(),i)
            if not os.path.exists(_):
                os.mkdir(_)
                logger.debug(f"Path Not Found: {_}. 请在脚本当前目录创建<{i}>文件夹")

    def get_material(self):
        """
        获取文件夹文件
        :return:
        [
            {"Mesh": ["22-mesh.obj"]},
            {"Texture2D": ["22.png"]}
        ]
        """
        result = {}
        for i in tool.check_list:
            result[i] = os.listdir(os.path.join(os.getcwd(),i))
        return result

    def get_shape(self,img):
        """
        return Img height and weight
        """
        return img.shape[0], img.shape[1]

    def read_file(self,mesh_path):
        """
        读取mesh文件,去除\n后以空格为间隔切分返回
        :params s: Mesh文件地址
        :return: [["v",1,1,0], ...]
        """
        List1 = []
        Filer = open(mesh_path,'r')
        List2 = Filer.readlines()
        Filer.close()
        for i0 in range(0, len(List2)):
            List2[i0] = List2[i0].replace("\n", "")
            List1.append(List2[i0].split())
        return List1

    def read_png(self,png_path):
        """
        读取PNG图片 - 参考: https://blog.csdn.net/weixin_44015965/article/details/109547129
        cv2.IMREAD_COLOR:默认参数，读入一副彩色图片，忽略alpha通道，可用1作为实参替代
        cv2.IMREAD_GRAYSCALE:读入灰度图片，可用0作为实参替代
        cv2.IMREAD_UNCHANGED:顾名思义，读入完整图片，包括alpha通道，可用-1作为实参替代
        PS: alpha通道，又称A通道，是一个8位的灰度通道，该通道用256级灰度来记录图像中的透明度复信息，\
            定义透明、不透明和半透明区域，其中黑表示全透明，白表示不透明，灰表示半透明
        :params png_path: PNG文件路径
        :returnL img obj
        """
        img = cv2.imread(png_path, cv2.IMREAD_UNCHANGED)
        return img

    def save_png(self, file_path, img):
        """
        以PNG形式保存图像
        :params file_path: 保存路径
        :params img: img obj
        :return: None
        """
        cv2.imwrite(file_path, img, [int(cv2.IMWRITE_PNG_COMPRESSION), 9])

    def rotate(self, img, flipCode=-1):
        """
        根据翻转代码来翻转图片
        cv2.flip(image, 1)  # 水平翻转
        cv2.flip(image, 0)  # 垂直翻转
        cv2.flip(image, -1)  # 水平垂直翻转 180°垂直翻转一次+180°水平翻转一次

        :params img: img obj
        :params flipCode: 翻转代码
        :return: new_img obj
        """
        new_img = cv2.flip(img, flipCode)
        return new_img


class encrypt_img:
    """封包 - 将修改好的立绘加密为碎片图"""
    def task(self, mesh_obj, pic):
        """
        :params mesh_obj: mesh文件名称
        :params pic: 加密或解密图片名称
        """
        logger.info(f" ===== 正在处理: <{pic}> ===== ")

        # mesh数据
        mesh = os.path.join(".", "Mesh", mesh_obj)
        # 解密后的正常立绘
        picture = os.path.join(".", "Picture", pic)
        # 游戏内拆包出来的加密图
        texture = os.path.join(".", "Used", pic)
        # 最后的结果图片路径
        final_png = os.path.join(".", "Texture2D", pic)
        logger.debug(f"<mesh> - {mesh}")
        logger.debug(f"<picture> - {picture}")
        logger.debug(f"<texture> - {texture}")
        logger.debug(f"<final_png> - {final_png}")

        mesh_data = Tool.read_file(mesh)
        img = Tool.read_png(picture)
        texture_img = Tool.read_png(texture)

        vjShu = firstx = endx = firsty = endy = 0
        # 解密图 - 高,宽
        # height,weight = img.shape[0],img.shape[1]
        # 根据之前的加密图创建还原画布
        max_height, max_weight = texture_img.shape[0],texture_img.shape[1]

        # 水平垂直翻转
        img = Tool.rotate(img, -1)
        img = Tool.rotate(img,1)

        # 第一个vt坐标的序列
        vt_index = 0
        for i in range(1, len(mesh_data)):
            # 第一个v所在行 1
            if mesh_data[i][0] == 'v' and vjShu == 0:
                vjShu = i

            if mesh_data[i][0] != "vt" and mesh_data[i-1][0] == "vt":
                break

            if mesh_data[i][0] == "vt":
                if vt_index == 0:
                    vt_index = i
            
        # 创建画布前打印信息
        logger.debug(f"<max_height> - {max_height}")
        logger.debug(f"<max_weight> - {max_weight}")
        logger.debug(f"<vjShu/jShu> - {vjShu}")
        logger.debug("vjShu | firstx | firsty | endx | endy | x1 | y1")
 
        # 根据最大宽高创建画布
        Base_img = np.zeros([max_height, max_weight, 4], np.uint8)
        jShu = vjShu
        while vjShu < len(mesh_data):
            if mesh_data[vjShu][0] != 'v':
                break

            # 选择解密图中的图像 v第一组
            firsty = abs(int(mesh_data[vjShu][1]))
            firstx = abs(int(mesh_data[vjShu][2]))
            endy = abs(int(mesh_data[vjShu+2][1]))
            endx = abs(int(mesh_data[vjShu+2][2]))
            # 锁定粘贴的坐标 vt第一组
            # y1 = int(float(mesh_data[vjShu-jShu+vt_index][1]) * float(max_weight))
            y1 = int(float(mesh_data[vjShu-jShu+vt_index][1]) * float(max_weight) + 0.5)
            # x1 = int(float(mesh_data[vjShu-jShu+vt_index][2]) * float(max_height))
            x1 = int(float(mesh_data[vjShu-jShu+vt_index][2]) * float(max_height) + 0.5)

            logger.debug(f"{vjShu},{firstx},{firsty},{endx},{endy},{x1},{y1}")

            for i in range(firstx-1, endx+1):
                for j in range(firsty-1, endy+1):
                    Base_img[x1+i-firstx][y1+j-firsty] = img[i][j]

            # Tool.save_png(final_png, Base_img)

            vjShu += 4

        # 垂直翻转
        Base_img = Tool.rotate(Base_img, 0)
        Tool.save_png(final_png, Base_img)
        logger.info(f"处理完成: <{pic}> 路径: {final_png}")

    def main(self):
        material = Tool.get_material()
        Mesh_list = material.get("Mesh", [])
        Picture_list = material.get("Picture", [])
        Texture2D_list = material.get("Texture2D", [])
        Used_list = material.get("Used", [])

        logger.info(f"检测到{len(Picture_list)}组文件...")
        for i in range(0, len(Picture_list)):
            mesh_obj = Picture_list[i].replace(".png", "-mesh.obj")
            if mesh_obj not in Mesh_list:
                logger.warning(f"Can't Find {mesh_obj} in Mesh.")
            else:
                time_start = time.time()
                self.task(mesh_obj, Picture_list[i])
                time_end = time.time()
                logger.info(f"处理完毕. 耗时 - {round(time_end-time_start,2)}")
        logger.success("Tasks Over.")
        os.system("pause")


class decrypt_img:
    """解包 - 将解包出来的加密立绘解密"""
    def task(self, mesh_obj, pic):
        """
        :params mesh_obj: mesh文件名称
        :params pic: 加密或解密图片名称
        """
        logger.info(f"\n ===== 正在处理: <{pic}> ===== ")
        
        # mesh数据
        mesh = os.path.join(".", "Mesh", mesh_obj)
        # 游戏内拆包出来的加密图
        texture = os.path.join(".", "Texture2D", pic)
        # 最后的结果图片路径
        final_png = os.path.join(".", "Picture", pic)
        logger.debug(f"<mesh> - {mesh}")
        logger.debug(f"<texture> - {texture}")
        logger.debug(f"<final_png> - {final_png}")

        mesh_data = Tool.read_file(mesh)
        img = Tool.read_png(texture)

        max_height = max_weight = vtjShu = firstx = endx = firsty = endy = 0
        # 加密图 宽,高
        height,weight = img.shape[0],img.shape[1]

        # 垂直翻转
        img = Tool.rotate(img,0)

        for i in range(1, len(mesh_data)):
            if mesh_data[i][0] != 'v':
                # beierfasite为例 - 205
                vtjShu = i
                break
            if abs(int(mesh_data[i][1])) > max_weight:
                max_weight = abs(int(mesh_data[i][1]))
            if abs(int(mesh_data[i][2])) > max_height:
                max_height = abs(int(mesh_data[i][2]))

        # 创建画布前打印信息
        logger.debug(f"<max_height> - {max_height}")
        logger.debug(f"<max_weight> - {max_weight}")
        logger.debug(f"<vtjShu/jShu> - {vtjShu}")
        logger.debug("vtjShu | firstx | firsty | endx | endy | x1 | y1")

        # 根据得出的最大宽高创建画布
        Base_img = np.zeros([max_height+1, max_weight+1, 4], np.uint8)
        jShu = vtjShu
        while vtjShu < len(mesh_data):
            if mesh_data[vtjShu][0] != 'vt':
                break

            # 选择加密图中的图像 vt第一组
            firsty = int(float(mesh_data[vtjShu][1]) * float(weight) + 0.5)
            firstx = int(float(mesh_data[vtjShu][2]) * float(height) + 0.5)
            endy = int(float(mesh_data[vtjShu+2][1]) * float(weight) + 0.5)
            endx = int(float(mesh_data[vtjShu+2][2]) * float(height) + 0.5)
            # 锁定粘贴的坐标 v第一组
            y1 = abs(int(mesh_data[vtjShu-jShu+1][1]))
            x1 = abs(int(mesh_data[vtjShu-jShu+1][2]))
            
            logger.debug(f"{vtjShu},{firstx},{firsty},{endx},{endy},{x1},{y1}")

            for i in range(firstx, endx):
                for j in range(firsty, endy):
                    Base_img[x1+i-firstx][y1+j-firsty] = img[i][j]

            # Tool.save_png(final_png, Base_img)

            vtjShu += 4

        # 水平垂直翻转
        Base_img = Tool.rotate(Base_img,-1)
        Base_img = Tool.rotate(Base_img,1)
        Tool.save_png(final_png, Base_img)
        logger.info(f"处理完成: <{pic}> 路径: {final_png}")

    def main(self):
        material = Tool.get_material()
        Mesh_list = material.get("Mesh", [])
        Picture_list = material.get("Picture", [])
        Texture2D_list = material.get("Texture2D", [])
        Used_list = material.get("Used", [])

        logger.info(f"检测到{len(Texture2D_list)}组文件...")
        for i in range(0, len(Texture2D_list)):
            mesh_obj = Texture2D_list[i].replace(".png", "-mesh.obj")
            if mesh_obj not in Mesh_list:
                logger.warning(f"Can't Find {mesh_obj} in Mesh.")
            else:
                time_start = time.time()
                self.task(mesh_obj, Texture2D_list[i])
                time_end = time.time()
                logger.info(f"处理完毕. 耗时 - {round(time_end-time_start,2)}")
                shutil.copy("./Texture2D/" + Texture2D_list[i], "./Used/" + Texture2D_list[i])
        logger.success("Tasks Over.")
        os.system("pause")


class manager:
    """处理流程"""
    help_info = """\n === 欢迎使用碧蓝航线立绘加解密工具 ===\n"""\
    """代码托管于: https://github.com/WriteCode-ChangeWorld/Tools 欢迎star~\n\n"""\
    """ === 说明 === \n1.立绘解密: 将mesh文件 (如22.mesh.obj) 放在<Mesh>文件夹, 将加密文件"""\
    """ (如:22.png) 放在<Texture2D>文件夹.  \n脚本执行完成后,解密文件在<Picture>文件夹.  """\
    """\n\n2.立绘加密: 将mesh文件 (如22.mesh.obj) 放在<Mesh>文件夹, 将魔改好或要替换立绘的解密文件"""\
    """ (如:22.png) 放在<Picture>文件夹, 同时将同名加密立绘文件 (如:22.png) 放在<Used>文件夹.  """\
    """\n脚本执行完成后,加密文件在<Texture2D>文件夹.  """\
    """\n\n特别说明: 如果是先执行1再执行2, 通常程序会copy一份加密文件到<Used>文件夹. 此时不用再手动copy"""\
    """\n\n === 回复数字以使用功能 === \n请将文件放置好后再运行本程序\n1.立绘解密还原\n2.立绘加密封包\n3.退出"""

    def __init__(self):
        self.command_info = {
            "1": "Decrypt_Img.main()", # 解密还原
            "2": "Encrypt_Img.main()", # 加密封包
            "3": "exit()"              # 退出
        }

    def main(self):
        """主函数"""
        print(manager.help_info)
        mode = input(": ")
        if str(mode) not in list(self.command_info.keys()):
            logger.warning(f"<mode>: {mode} 不在支持列表内,请重新输入或检查输入内容...")
            exit()
        else:
            eval(self.command_info[mode])

        """
        # Mesh文件
        Mesh_files = os.listdir("./Mesh")
        # 加密图像文件
        Texture2D_files = os.listdir("./Texture2D")
        # 解密图像/魔改图像文件
        Picture_files = os.listdir("./Picture")
        Encrypt_Img.main()
        """


Tool = tool()
Encrypt_Img = encrypt_img()
Decrypt_Img = decrypt_img()
Manager = manager()
Manager.main()