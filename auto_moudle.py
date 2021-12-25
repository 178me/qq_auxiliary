import os
from time import sleep, time
from random import randint
from lib import log, CreateDm, Images


class AutoMationModule:
    def __init__(self):
        self.debug_mode = True
        self.index = 0
        self.hwnd = 0
        self.image = Images()
        self.dll = CreateDm.create_dm()
        self.dl(self.dll.Ver())
        result = int(self.dll.reg(
            "clyl8888b2267205e330bf543b632e30b65e9003", ""))
        #  self.dl(result)
        if result != 1:
            log.error("大漠初始化失败")
        # 大漠设置
        self.dll.setAero(0)
        self.dll.EnableKeypadSync(1, 3000)
        self.dll.SetPath(f"{os.getcwd()}{os.sep}src")
        self.window_size = (960, 540)
        self.window_hwnd = 0
        self.foobar_hwnd = 0

    def pretreatment(self):
        pass

    def exit(self):
        self.un_bind_window()
        self.dll.FoobarClose(self.foobar_hwnd)

    def dl(self, message):
        if self.debug_mode:
            log.info(f"模拟器{self.index}: {message}")

    def save_errpage(self):
        self.dll.Capture(0, 0, 2000, 2000, f"not_found-{self.index}.bmp")

    def bind_window(self):
        self.dll.SetWindowState(self.hwnd, 1)
        if self.dll.BindWindowEx(self.hwnd, "dx.graphic.opengl", "windows3", "windows", "", 0) != 1:
            raise Exception("绑定窗口出错")
        self.window_size = self.get_window_size()

    def un_bind_window(self):
        self.dll.UnBindWindow()

    def get_window_size(self):
        size = self.dll.GetClientSize(self.hwnd)
        return (size[1], size[2])

    def ocr(self, x1=0, y1=0, x2=2000, y2=2000, color_format="000000-101010", sim=0.99, find_time=3):
        timeout = time() + find_time
        font = ""
        while timeout > time():
            self.pretreatment()
            font = self.dll.ocr(
                x1, y1, x2, y2, color_format, sim)
            if font != "":
                break
        if font == "":
            return None
        return font

    def find_image_by_opencv(self, template_image_path: str, region=(0, 0, 1, 1), confidence=0.95, find_time=3, offset=(0, 0), is_click=False, **option):
        window_image_path = f"{os.getcwd()}{os.sep}src{os.sep}cache{os.sep}cache-{self.index}.bmp"
        point = (-1, None)
        timeout = time() + find_time
        while timeout > time():
            self.pretreatment()
            self.dll.Capture(0, 0, 2000, 2000, window_image_path)
            point = self.image.find_image_by_canny(
                template_image_path, window_image_path, region=region, confidence=confidence)
            if -1 not in point:
                break
        if -1 in point:
            return None
        if is_click:
            click_point = self.image.get_center_point(point[1])
            self.click(click_point[0] + offset[0],
                       click_point[1] + offset[1], **option)
        return point

    def find_image_by_dll(self, pic_name, find_time=3, offset=(0, 0), is_click=False, x1=0, y1=0, x2=2000, y2=2000, delta_color="050505", sim=0.8, direction=0, **option):
        timeout = time() + find_time
        last_point = (-1, -1, -1)
        point = (-1, -1, -1)
        while timeout > time():
            self.pretreatment()
            point = self.dll.FindPic(
                x1, y1, x2, y2, pic_name, delta_color, sim, direction)
            if -1 not in point:
                if last_point[0] == -1:
                    last_point = point
                    continue
                elif last_point[1] != point[1] or last_point[2] != point[2]:
                    last_point = point
                    continue
                break
        if -1 in point:
            return None
        image_size = self.dll.GetPicSize(
            pic_name.split("|")[point[0]]).split(",")
        #  self.dl(pic_name.split("|")[point[0]])
        point = {
            "index": point[0],
            "left": point[1],
            "top": point[2],
            "width": int(image_size[0]),
            "height": int(image_size[1]),
        }
        if is_click:
            self.click(point["left"] + int(point["width"] * 0.5) + offset[0],
                       point["top"] + int(point["height"] * 0.5) + offset[1], **option)
        return point

    def find_images_by_dll(self, pic_name, find_time=3, x1=0, y1=0, x2=2000, y2=2000, delta_color="050505", sim=0.8, direction=0):
        timeout = time() + find_time
        images = []
        point = ""
        while timeout > time():
            self.pretreatment()
            point = self.dll.FindPicEx(
                x1, y1, x2, y2, pic_name, delta_color, sim, direction)
            if point != "":
                break
        if point == "":
            return None
        point = point.split("|")
        for p in point:
            p = p.split(",")
            image_size = self.dll.GetPicSize(
                pic_name.split("|")[int(p[0])]).split(",")
            images.append({
                "index": int(p[0]),
                "left": int(p[1]),
                "top": int(p[2]),
                "width": int(image_size[0]),
                "height": int(image_size[1]),
            })
        return images

    def find_image_by_attr(self, attr_list, find_time=3, find_delay=0, offset=(0, 0), is_click=False, **option):
        timeout = time() + find_time
        pic_name = ""
        last_point = (-1, -1, -1)
        point = (-1, -1, -1)
        pic_index = -1
        while timeout > time():
            self.pretreatment()
            for index, attr in enumerate(attr_list):
                point = self.dll.FindPic(attr.get("x1", 0), attr.get("y1", 0), attr.get("x2", 2000), attr.get("y2", 2000), attr.get(
                    "pic_name"), attr.get("delta_color", "050505"), attr.get("sim", 0.9), attr.get("direction", 0))
                if -1 not in point:
                    pic_name = attr.get("pic_name")
                    pic_index = index
                    break
            if -1 not in point:
                if last_point[0] == -1:
                    last_point = point
                    sleep(find_delay)
                    continue
                elif last_point[1] != point[1] or last_point[2] != point[2]:
                    last_point = point
                    sleep(find_delay)
                    continue
                break
        if -1 in point:
            return None
        image_size = self.dll.GetPicSize(pic_name).split(",")
        point = {
            "pic_name": pic_name,
            "index": pic_index,
            "left": point[1],
            "top": point[2],
            "width": int(image_size[0]),
            "height": int(image_size[1]),
        }
        if is_click:
            self.click(point["left"] + int(point["width"] * 0.5),
                       point["top"] + int(point["height"] * 0.5),offset=offset, **option)
        return point

    def is_disappear_by_image(self, pic_name, search_time=5, find_time=0.5, **find_iamge_param):
        timeout = time() + search_time
        while timeout > time():
            self.pretreatment()
            image_point = self.find_image_by_dll(
                pic_name, find_time=find_time, **find_iamge_param)
            #  self.dl(image_point)
            if not image_point:
                self.dl("页面已跳转")
                return True
        self.dl("页面未跳转")
        return False

    def click(self, x, y,offset=(0,0), button="left", click_count=1, interval=0.1, click_delay=0.1):
        self.pretreatment()
        x += offset[0]
        y += offset[1]
        if x <= 1:
            x *= self.window_size[0]
            y *= self.window_size[1]
        x = int(x)
        y = int(y)
        self.dl(f"x点击坐标:{x}")
        self.dl(f"y点击坐标:{y}")
        self.dll.MoveTo(x, y)
        if "left" in button:
            down = self.dll.LeftDown
            up = self.dll.LeftUp
        else:
            down = self.dll.RightDown
            up = self.dll.RightUp
        down_state, up_state = 0, 0
        for _ in range(click_count):
            down_state = down()
            sleep(interval)
            up_state = up()
        sleep(click_delay)
        if int(down_state) != 1 and int(up_state) != 1:
            return False
        return True

    def click_center(self, point, **option):
        self.click(point["left"] + int(point["width"] * 0.5),
                   point["top"] + int(point["height"] * 0.5), **option)

    def swipe(self, begin_x, begin_y, end_x, end_y):
        self.dll.MoveTo(begin_x, begin_y)
        self.dll.LeftDown()
        sleep(0.1)
        self.dll.MoveTo(end_x, end_y)
        sleep(0.1)
        self.dll.LeftUp()

    @classmethod
    def smlMove(cls, begin_x, begin_y, end_x, end_y, duration):
        xxy = []
        point = [
            {
                "x": begin_x,
                "y": begin_y
            },
            {
                "x": randint(begin_x-100, begin_x+100),
                "y": randint(begin_y, begin_y+50)
            },
            {
                "x": randint(end_x-100, end_x+100),
                "y": randint(end_y, end_y+50)
            },
            {
                "x": end_x,
                "y": end_y
            },
        ]

        def bezierCurves(cp, t):
            cx = 3.0 * (cp[1]["x"] - cp[0]["x"])
            bx = 3.0 * (cp[2]["x"] - cp[1]["x"]) - cx
            ax = cp[3]["x"] - cp[0]["x"] - cx - bx
            cy = 3.0 * (cp[1]["y"] - cp[0]["y"])
            by = 3.0 * (cp[2]["y"] - cp[1]["y"]) - cy
            ay = cp[3]["y"] - cp[0]["y"] - cy - by
            tSquared = t * t
            tCubed = tSquared * t
            return [int((ax * tCubed) + (bx * tSquared) + (cx * t) + cp[0]["x"]),
                    int((ay * tCubed) + (by * tSquared) + (cy * t) + cp[0]["y"])]
        i = 0
        t = 0
        total_delay = 0
        distance = abs(end_y - begin_y)
        while t < 1:
            xxy.append(bezierCurves(point, t))
            if i > 0:
                mobile_distance = abs(xxy[i][0] - xxy[i-1][0])
                delay = duration * (mobile_distance / distance)
            else:
                delay = 0
            total_delay += delay
            xxy[i].append(delay)
            t += 0.08
            i += 1
        return xxy

    def drag(self, x1, y1, x2, y2, duration):
        move_arr = self.smlMove(x1, y1, x2, y2, duration)
        i = 0
        while i < len(move_arr):
            if i == 0:
                self.dll.moveTo(move_arr[i][0], move_arr[i][1])
                self.dll.LeftDown()
            elif i == len(move_arr)-1:
                self.dll.moveTo(move_arr[i][0], move_arr[i][1])
                self.dll.LeftUp()
            else:
                self.dll.moveTo(move_arr[i][0], move_arr[i][1])
            sleep(move_arr[i][2])
            i += 1
        return True

    def input_text(self, text):
        self.dll.Delay(100)
        self.dll.SendString(self.hwnd, text)
        self.dll.Delay(100)

    def hot_key(self, control_key, key):
        self.dll.Delay(100)
        self.dll.KeyDownChar(control_key)
        self.dll.KeyPressChar(key)
        self.dll.KeyUpChar(control_key)
        self.dll.Delay(100)


if __name__ == "__main__":
    print("自动化测试")
    auto = AutoMationModule()
    auto.hwnd = 131652
    # auto.bind_window()
    #  auto.find_image_by_dll("test.bmp|test2.bmp", is_click=True, click_count=2)
    #  point = auto.find_image_by_opencv("./src/test2.bmp|./src/test.bmp", confidence=0.8,
    #  is_click=True, click_count=2)
    #  print(point)
    # auto.input_text("我有一个大香蕉")
