'''
@author: 178me
@description: window自动化操作
'''
try:
    import ctypes
    import re
    import base64
    import requests
    import sys
    import os
    import warnings
    from win32com.client import Dispatch
    sys.coinit_flags = 2
    warnings.simplefilter("ignore", UserWarning)
except Exception as e:
    pass
import logging
#  import pywinauto
import pyautogui
import configparser
import numpy as np
import cv2
from os import getcwd, sep, system
from time import sleep, time
#  from random import randint
from functools import wraps
#  import easyocr

# 日志模块设置
log = logging.getLogger('qq_login')
log.setLevel(level=logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s.%(msecs)d-%(levelname)s: %(message)s')
formatter.datefmt = "%H:%M:%S"
file_handler = logging.FileHandler('./out/log.txt')
file_handler.setLevel(level=logging.INFO)
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
log.addHandler(file_handler)
log.addHandler(stream_handler)


# 功能函数模块
class FunWrap(object):
    def __init__(self, task_name="", is_raise=False):
        # 功能标识名
        self.task_name = task_name
        # 是否抛出异常
        self.is_raise = is_raise

    def __call__(self, func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            try:
                # 预处理 args[0] 一般是类对象self 所以该方法用于类
                args[0].pretreatment(self.task_name)
                return func(*args, **kwargs)
            except Exception as e:
                if str(e) == "停止线程":
                    raise Exception("停止线程")
                log.exception(e)
                if self.is_raise:
                    raise Exception(f"{self.task_name} 出错")
                else:
                    log.error(f"{self.task_name} 出错")
                    return False
        return wrapped_function


# 图色模块
class Images:
    def __init__(self):
        self.app = None  # GUI需要
        self.screen = None

    def init_app(self, app):
        ''' Qt后台截图初始化 '''
        self.app = app  # GUI需要
        self.screen = app.primaryScreen()

    def QImageToCvMat(self, incomingImage):
        ''' QT截图 To opencv Mat '''
        qimg = incomingImage
        temp_shape = (qimg.height(), qimg.bytesPerLine()
                      * 8 // qimg.depth())
        temp_shape += (4,)
        ptr = qimg.bits()
        ptr.setsize(qimg.byteCount())
        result = np.array(ptr, dtype=np.uint8).reshape(temp_shape)
        result = result[..., :3]
        return result

    def window_screenshot(self, window_obj, image_name=None):
        ''' 窗口截图 '''
        try:
            if not self.app:
                raise Exception("未初始化App")
            hwnd = window_obj.element.handle
            if window_obj.get_dialog().is_minimized():
                window_obj.element.restore()
            img = self.screen.grabWindow(hwnd).toImage()
            if image_name:
                img.save(f"./image/{image_name}")
                return f"./temp/{hwnd}"
            img = self.QImageToCvMat(img)
            if isinstance(img, np.ndarray):
                return img
            raise Exception("图片格式未转换成功")
        except Exception as e:
            log.exception(e)
            raise Exception("窗口截图出错")

    def get_center_point(self, point):
        ''' 返回中心坐标 '''
        center_x = int(point[0] + (point[2] / 2))
        center_y = int(point[1] + (point[3] / 2))
        return (center_x, center_y)

    def find_image_by_ld(self, query_image_path, train_image_path, **option):
        ''' 查找图片 '''
        if "find_way" in option:
            if option["find_way"] == "flann":
                find_fun = self.find_image_by_flann
            elif option["find_way"] == "template":
                find_fun = self.find_image_by_template
            else:
                find_fun = self.find_image_by_template
        else:
            find_fun = self.find_image_by_template
        if "region" in option:
            region = option["region"]
        else:
            if "find_image_by_template" in str(find_fun):
                region = None
            else:
                region = [0, 0, 0.99, 0.99]
        if "confidence" in option:
            confidence = option["confidence"]
        else:
            if "find_image_by_template" in str(find_fun):
                confidence = 0.99
            else:
                confidence = 0.7
        log.debug(f"find_fun: {str(find_fun)}")
        log.debug(f"region: {region}")
        log.debug(f"confidence: {confidence}")
        img = find_fun(query_image_path, train_image_path,
                       region=region, confidence=confidence)
        if img:
            log.debug(f"查找图片成功,结果:")
            log.debug(img)
            if "find_image_by_template" in str(find_fun):
                return [img.left, img.top, img.width, img.height]
            else:
                return img
        return None

    def find_image(self, template_image, window_object, **option):
        ''' 查找图片 '''
        if "find_way" in option:
            if option["find_way"] == "flann":
                find_fun = self.find_image_by_flann
            elif option["find_way"] == "template":
                find_fun = self.find_image_by_template
            else:
                find_fun = self.find_image_by_template
        else:
            find_fun = self.find_image_by_template
        if "region" in option:
            region = option["region"]
        else:
            if "find_image_by_template" in str(find_fun):
                region = None
            else:
                region = [0, 0, 0.99, 0.99]
        if "confidence" in option:
            confidence = option["confidence"]
        else:
            if "find_image_by_template" in str(find_fun):
                confidence = 0.99
            else:
                confidence = 0.7
        if "timeout" in option:
            timeout = time() + option["timeout"]
        else:
            timeout = time() + 3
        if "find_delay" in option:
            find_delay = option["find_delay"]
        else:
            find_delay = 0.1
        log.debug(f"find_fun: {str(find_fun)}")
        log.debug(f"region: {region}")
        log.debug(f"confidence: {confidence}")
        log.debug(f"timeout: {timeout}")
        count = 0
        while timeout > time():
            log.debug(f"第 {count} 次查找图片")
            img = find_fun(template_image, self.window_screenshot(
                window_object), region=region, confidence=confidence)
            if img:
                log.debug(f"查找图片成功,结果:")
                log.debug(img)
                if "find_image_by_template" in str(find_fun):
                    return [img.left, img.top, img.width, img.height]
                else:
                    return img
            sleep(find_delay)
            count += 1
        log.warning("查找图片超时")
        return None

    def find_image_by_flann(self, template_image, source_image, region=[0, 0, 0.99, 0.99], confidence=0.7):
        ''' 通过flann方法找图(特征找图)
        :param queryImagePath: 需要查找的图片路径
        :param trainImage: 需要查找的图片路径 或者 mat对象
        :param region: 需要查找的图片所在区域
        :param confidence: 相似度
        :from https://blog.csdn.net/zhuisui_woxin/article/details/84400439
        :note 本函数如果出错可以用以下代码调试查看图片
        cv2.imshow('窗口标题', Mat对象)
        cv2.waitKey(0)
        cv2.imshow('template', template)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        :return: True || False
        '''
        template = cv2.imread(template_image, 0)  # queryImage
        if isinstance(source_image, np.ndarray):
            target = cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)
        elif isinstance(source_image, str):
            target = cv2.imread(source_image, 0)  # trainImage
        # Initiate SIFT detector创建sift检测器
        sift = cv2.SIFT_create()
        # find the keypoints and descriptors with SIFT
        kp1, des1 = sift.detectAndCompute(template, None)
        kp2, des2 = sift.detectAndCompute(target, None)
        # 创建设置FLANN匹配
        index_params = dict(algorithm=0, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des1, des2, k=2)
        # store all the good matches as per Lowe's ratio test.
        good = []
        h, w = target.shape
        region[0] *= w
        region[1] *= h
        region[2] = (region[2] * w) + region[0]
        region[3] = (region[3] * h) + region[1]
        # 舍弃大于0.7的匹配
        for m, n in matches:
            if m.distance > confidence * n.distance:
                continue
            if region[0] > kp2[m.trainIdx].pt[0] or kp2[m.trainIdx].pt[0] > region[2]:
                continue
            if region[1] > kp2[m.trainIdx].pt[1] or kp2[m.trainIdx].pt[1] > region[3]:
                continue
            good.append(m)
        MIN_MATCH_COUNT = 10  # 设置最低特征点匹配数量
        print(good)
        print(w, h)
        if not len(good):
            return None
        point_list = [kp2[value.trainIdx].pt for i,
                      value in enumerate(good)]
        rect = ()
        # 限制查找图的大小
        left = point_list[0][0]
        top = point_list[0][1]
        right = point_list[0][0]
        bottom = point_list[0][1]
        for key, value in enumerate(point_list):
            if value[0] < left:
                left = value[0]
            if value[1] < top:
                top = value[1]
            if value[0] > right:
                right = value[0]
            if value[1] > bottom:
                bottom = value[1]
        rect_w = right - left
        rect_h = bottom - top
        rect = (int(left), int(top), int(rect_w), int(rect_h))
        return rect

    def find_image_by_template(self, template_image, source_image, **kw):
        ''' 模板找图 grayscale 灰度'''
        images = list(pyautogui.locateAll(template_image, source_image, **kw))
        if not images:
            return None
        return images[0]

    def find_images_by_template(self, template_image, source_image, **kw):
        ''' 模板找图多个 '''
        images = list(pyautogui.locateAll(template_image, source_image, **kw))
        return images

    def get_region(self, region, image_width, image_height):
        ''' 获取范围 '''
        if region[0] <= 1:
            x = int(region[0] * image_width)
        else:
            x = int(region[0])
        if region[1] <= 1:
            y = int(region[1] * image_height)
        else:
            y = int(region[1])
        if region[2] <= 1:
            width = int(region[2] * image_width)
        else:
            width = int(region[2])
        if region[3] <= 1:
            height = int(region[3] * image_height)
        else:
            height = int(region[3])
        return (x, y, width, height)

    def find_image_by_canny(self, template_image_path, source_image_path, threshold=(500, 0), region=(0, 0, 1, 1), **kw):
        ''' 找轮廓图(建议优化:canny的高低阀值设置为参数) '''
        # 读取模板图像和源图像
        template_image_list = template_image_path.split("|")
        source_image = cv2.imdecode(
            np.fromfile(source_image_path, dtype=np.uint8), -1)
        image_height = source_image.shape[0]
        image_width = source_image.shape[1]
        region = self.get_region(region, image_width, image_height)
        # 灰度化并提取轮廓
        try:
            source_image = cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)
            source_image = cv2.Canny(source_image, threshold[0], threshold[1])
        except:
            log.warning("灰度化失败")
        # 转为3通道图片 找图需要
        source_image = cv2.cvtColor(source_image, cv2.COLOR_BGR2RGB)
        #  cv2.imencode('.bmp', source_image)[1].tofile(source_image_path)
        #  cv2.imshow('image', source_image)
        #  cv2.waitKey(0)
        # 查找出对应的图片
        for i, template_image in enumerate(template_image_list):
            template_image = cv2.imdecode(
                np.fromfile(template_image, dtype=np.uint8), -1)
            template_image = cv2.cvtColor(template_image, cv2.COLOR_BGR2RGB)
            result = self.find_image_by_template(
                template_image, source_image, region=region, **kw)
            if not result:
                continue
            return (i, result)
        return (-1, None)

    def show_contour_image(self, source_image_path):
        source_image = cv2.imdecode(
            np.fromfile(source_image_path, dtype=np.uint8), -1)
        source_image = cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)
        source_image = cv2.Canny(source_image, 500, 0)
        cv2.imshow("input image", source_image)
        cv2.waitKey(0)

    def save_contour_image(self, source_image_path, contour_image_name="contour", threshold=(500, 0),  region=(0, 0, 1, 1)):
        ''' 保存轮廓图(后期可写一个GUI) '''
        source_image = cv2.imdecode(
            np.fromfile(source_image_path, dtype=np.uint8), -1)
        image_height = source_image.shape[0]
        image_width = source_image.shape[1]
        region = self.get_region(region, image_width, image_height)
        # 灰度化并提取轮廓
        try:
            source_image = cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)
        except:
            log.warning("灰度化失败")
        grad_x = cv2.Sobel(source_image, cv2.CV_16SC1, 1, 0)
        grad_y = cv2.Sobel(source_image, cv2.CV_16SC1, 0, 1)
        source_image = cv2.Canny(grad_x, grad_y, threshold[0], threshold[1])
        #  cv2.imshow('image', source_image)
        #  cv2.waitKey(0)
        # 保存图片
        #  cv2.imencode('.bmp', source_image)[1].tofile(source_image_path)
        # 区域截图
        contour_image = source_image.copy()[
            region[1]:region[1] + region[3],
            region[0]:region[0]+region[2]]
        contour_image2 = source_image[
            region[1]:region[1] + region[3],
            region[0]:region[0]+region[2]]
        # 去除直线
        try:
            self.clear_line_contour(contour_image)
        # 使用自定义方式剪裁出最大轮廓
            conrect_image_rect = self.my_find_contour_image(contour_image)
            log.info(region)
            log.info(conrect_image_rect)
            contour_image = contour_image2[conrect_image_rect[0]:conrect_image_rect[1],
                                           conrect_image_rect[2]:conrect_image_rect[3]]
        except Exception as e:
            log.exception(e)
            log.warning("处理图片出错")
        #  cv2.imshow('image', source_image)
        #  cv2.waitKey(0)
        #  cv2.imshow('image1', contour_image)
        #  cv2.waitKey(0)
        #  cv2.imshow('image2', contour_image2)
        #  cv2.waitKey(0)
        #  cv2.destroyAllWindows()
        # 查找最大序号
        max_index = 0
        contour_image_path = os.getcwd() + os.sep + "src" + os.sep + "contour_image"
        filenames = [filename for x in os.walk(
            contour_image_path) for filename in x[2]]
        for filename in filenames:
            if contour_image_name not in filename:
                continue
            index = int(filename.replace(
                contour_image_name, "").replace(".bmp", "").replace("-", ""))
            if index > max_index:
                max_index = index
        #  print(max_index)
        max_index += 1
        # 保存图片
        try:
            log.info("正常保存")
            contour_image = cv2.cvtColor(contour_image, cv2.COLOR_BGR2RGB)
            cv2.imencode('.bmp', contour_image)[1].tofile(
                f"{contour_image_path}{os.sep}{contour_image_name}-{max_index}.bmp")
        except:
            log.warning("正常保存失败")
            contour_image = cv2.cvtColor(
                source_image[region[1]:region[3], region[0]:region[2]], cv2.COLOR_BGR2RGB)
            cv2.imencode('.bmp', contour_image)[1].tofile(
                f"{contour_image_path}{os.sep}{contour_image_name}-{max_index}.bmp")
        return True

    def clear_line_contour(self, canny):
        ''' 去除轮廓直线 '''
        canny = cv2.dilate(canny, (2, 2), iterations=1)
        w = canny.shape[1]
        lines = cv2.HoughLines(canny, 1, np.pi/180, int(w / 2), w)
        try:
            for i in range(len(lines)):
                for rho, theta in lines[i]:
                    a = np.cos(theta)
                    b = np.sin(theta)
                    x0 = a*rho
                    y0 = b*rho
                    x1 = int(x0 + w*(-b))
                    y1 = int(y0 + w*(a))
                    x2 = int(x0 - w*(-b))
                    y2 = int(y0 - w*(a))
                    if x1 < 0:
                        x1 = 0
                    cv2.line(canny, (x1, y1), (x2, y2), (0, 0, 0), 3)
            #  cv2.imshow("lines", canny)
            #  cv2.waitKey()
        except:
            log.warning("去除直线出错")
        return canny

    def my_find_contour_image(self, contour_image):
        ''' 自定义轮廓切片方法 '''
        # 查找图片中的最大轮廓
        contour_image_height = contour_image.shape[0]
        contour_image_width = contour_image.shape[1]
        top, left, bottom, right = (10000, 10000, 0, 0)
        for y in range(contour_image_height):
            for x in range(contour_image_width):
                #  print(y,x)
                if contour_image[y][x] != 255:
                    continue
                if top > y:
                    top = y
                if bottom < y:
                    bottom = y
                if y < int(contour_image_height * 0.5) and left > x:
                    left = x
                if y < int(contour_image_height * 0.5) and right < x:
                    right = x
        if left > 1:
            left -= 2
        if top > 1:
            top -= 2
        if right < contour_image_width-1:
            left += 2
        if bottom > contour_image_height-1:
            bottom += 2
        return (top, bottom, left, right)


class Config():
    """ 配置文件模块 """

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = os.getcwd() + os.sep + "input" + os.sep + "config.ini"
        if not os.path.exists(self.config_path):
            file = open(self.config_path, 'w')
            file.close()
        self.config.read(self.config_path, encoding="utf-8")

    def set(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)

    def get(self, section=None, key=None):
        if key:
            if not self.config.has_option(section,key):
                return None
            return self.config.get(section, key)
        if section:
            if not self.config.has_section(section):
                return []
            return self.config.items(section)
        return self.config.sections()

    def remove(self, section, key=None):
        if not self.config.has_section(section):
            return None
        if key:
            return self.config.remove_option(section, key)
        return self.config.remove_section(section)

    def write(self):
        with open(self.config_path, "w", encoding="utf-8") as config_file:
            self.config.write(config_file)


class CreateDm:
    """ 创建Dll插件 """
    @classmethod
    def create_dm(cls):
        try:
            dm = Dispatch("dm.dmsoft")
        except:
            dll_path = f"{getcwd()}{sep}input{sep}dm.dll"
            system(f"regsvr32 /s {dll_path}")
            dm = Dispatch("dm.dmsoft")
        return dm


class JianGuoYun:
    ''' 坚果云网盘 '''

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.auth = username+":"+password
        self.auth = "Basic " + \
            base64.b64encode(self.auth.encode('utf-8')).decode("utf-8")
        self.headers = {
            "Authorization": self.auth
        }
        self.base_url = "https://dav.jianguoyun.com/dav/"

    def put(self, path, file_path):
        ''' 上传文本数据 '''
        print(self.base_url+path)
        print(requests.put(self.base_url+path,
                           headers=self.headers, data=open(file_path, "rb")).text)

    def get(self, path):
        ''' 获取文本数据 '''
        return requests.get(self.base_url+path, headers=self.headers)

    def propfind(self, path):
        ''' 获取列表 '''
        html_str = requests.request(
            'propfind', self.base_url+path, headers=self.headers).text
        html_str = re.sub(r'<[^>]+>', "++", html_str)
        html_str = re.split(r"[++]+", html_str)
        file_path = "/dav/"+path
        if path[-1] != "/":
            file_path += "/"
        file_list = []
        for data in html_str:
            if re.search(r".*"+file_path+r".*", data):
                file_list.append(re.sub(file_path, '', data))
        return file_list

class Other:
    """ 其他 """
    @classmethod
    def set_console(cls, enable):
        """ 显示控制台 """
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd == 0:
            return False
        if enable:
            ctypes.windll.user32.ShowWindow(whnd, 1)
        else:
            ctypes.windll.user32.ShowWindow(whnd, 0)
        return True

    @classmethod
    def get_netpad_text(cls, note_id=""):
        ''' 获取网络剪贴板的内容,需要json request warnings库
        :param note_id: 剪贴板id
        :return: data || error
        '''
        # 如果标题为空的话获取所有标题
        netpad_url = "https://netcut.cn/api/note/data/?note_id=" + \
            note_id + "&_=" + str(int(time()))
        # 获取所有该用户名所有文本 verify是否忽略安全证书 我这里不忽略会报错
        warnings.simplefilter("ignore")
        result = requests.post(
            netpad_url,
            verify=False,
        ).json()
        if result["error"] == "":
            del result["data"]["log_list"]
            return result["data"]
        else:
            print("遇到错误 " + result['error'])
            return result['error']

    @classmethod
    def switch_view(cls, enable):
        """ 打开|关闭 上帝视角 """
        if enable:
            view_path = os.getcwd() + os.sep + "input" + os.sep + "上帝.exe"
            os.popen(view_path)
        else:
            os.popen("taskkill /im 上帝.exe")

    @classmethod
    def match_picname(cls, pic_dir, picname_re):
        pic_list = ""
        filenames = [filename for x in os.walk(
            pic_dir) for filename in x[2]]
        for filename in filenames:
            if picname_re in filename:
                pic_list += os.path.join(pic_dir, filename) + "|"
        if len(pic_list) > 1:
            pic_list = pic_list[:-1]
        return pic_list


if __name__ == "__main__":
    print("自动化库 测试")
