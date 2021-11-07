## Pixiv插画tag导入Eagle

---

+ 偶然间被安利了`Eagle`这样一款图片管理软件，初次使用的时候看到这个tag就觉得大有用处。
+ 现在可以使用`pixiv2eagle`为`Eagle`内的`pixiv`插画添加`tag`，从而更好的建造、管理、筛选自己的`pixiv`插画数据库（涩图库）
+ 需要魔法使用

↓ 如图，筛选一下<柴郡>，全是可爱的猫猫:happy:
(会遗漏部分不是从`pixiv`上下载的插画，因为没有`tag`可筛选)

![1.png](D:\Code\Tools\0x09-Pixiv插画tag数据导入Eagle\img\1.png)

+ 这里给下数据参考。此处为使用`PixiC`下载`pixiv`个人收藏共`4.6w`张图片(`88G`)，导入Eagle后为`98G` (`Eagle`生成缩略图占用了`10G`)
+ 脚本默认使用8线程，处理以上数据花费时间 : `52min`(`13:05:34.040~13:57:52.723`)



**功能**

- [x] 从[PIXIC API](https://github.com/Coder-Sakura/PixiC/wiki)或`pixiv`获取对应插画的tag数据
- [x] 将插画`tag`数据及画师名称导入`Eagle metadata.json`
- [x] 线程池处理任务(默认8线程)
- [x] 执行过程及多线程日志记录



**支持识别的`pixiv`插画文件名称**

+ `86352163.jpg` / `86352163.png`
+ `86352163-1.jpg` / `86352163-2.png`
+ `86352163_p0.jpg` / `86352163_p1.png`



**一些话**

1. 由`PixiC`下载得到的`pixiv`插画，格式为`86352163-1.jpg`或`86352163.jpg`的形式（截图中使用的）
2. 直接从`pixiv`处下载的插画格式为`86352163_p0.jpg`，其他工具下载的文件请自行命令或在`Pixiv2Eagle.get_pid`处添加识别逻辑



**使用方法**

1. 添加插画到`Eagle`

选中要加入的图片文件，拖拽到`Eagle`上即可；或从左上角选择路径载入

![](D:\Code\Tools\0x09-Pixiv插画tag数据导入Eagle\img\0.png)



2. 复制`Eagle`资源库地址

> 这个地址就是上面创建的；比如`G:\EagleHome\个人收藏.library`

填入`pixiv2eagle.py`中的`EAGLE_HOME_PATH`，如：

```python
EAGLE_HOME_PATH = r"your EAGLE_HOME_PATH"
```



> 这里提供了一个TEST DIR供测试使用，即`Home.library`目录



3. 选择获取pixiv插画数据的方式

**从`PIXIC_API`获取**

将你的`PIXIC_API`地址填入到`pixiv2eagle.py`中的`PIXIC_API`，如：

```python
# 使用的是get-info API
# 默认操作的是Bookmark表
PIXIC_API = "http://xxx.xx.xxx.xx:1526/api/v2/get-info"
```



**从`pixiv`获取**

将`PIXIC_API`设置为空即可

```python
PIXIC_API = ""
```



4. 开始使用

```bash
# 安装依赖
pip install -r requirement.txt
# 运行脚本
python pixiv2eagle.py
```



**运行及效果截图**

脚本写入tag

![](D:\Code\Tools\0x09-Pixiv插画tag数据导入Eagle\img\2.png)

写入tag后在Eagle中的使用

柴郡

![](D:\Code\Tools\0x09-Pixiv插画tag数据导入Eagle\img\1.png)

大凤

![](D:\Code\Tools\0x09-Pixiv插画tag数据导入Eagle\img\4.png)

支持联想tag

![](D:\Code\Tools\0x09-Pixiv插画tag数据导入Eagle\img\3.png)