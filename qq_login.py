import psutil
import os
from auto_moudle import AutoMationModule
from lib import FunWrap, log, sleep, JianGuoYun
from ldconsole import LdConsole


class QQ_Login(AutoMationModule):
    def __init__(self, ld_path=None):
        # 初始化父类方法
        super(QQ_Login, self).__init__()
        # 定义雷电模块
        self.ld = LdConsole(ld_path)
        self.jgy = JianGuoYun("1403341393@qq.com", "abhdwrkfxxrnhnyf")
        self.set_script_message = None
        # 显示脚本状态的信号
        self.init_var()

    def init_var(self):
        # 脚本执行状态
        self.status = "初始化"
        # 执行参数
        self.params = {}
        # 保存二维码的窗口标题
        self.qrcode_name = "加载"
        self.login_status = "初始化"

    def pretreatment(self, task_name=""):
        ''' 预处理函数(每个函数开始之前执行) '''
        if "stop" in self.status:
            self.exit()
            self.set_status("停止脚本")
            self.dl("停止线程")
            raise Exception("停止线程")
        self.wait_cpu()
        if task_name != "":
            self.dl(task_name + " 开始")
            self.set_status(task_name)

    def set_status(self, status_text):
        ''' 设置脚本状态 '''
        self.status = status_text
        if self.set_script_message:
            self.set_script_message.emit(self.index, status_text)

    def wait_cpu(self):
        for _ in range(30):
            if psutil.cpu_percent(None) > 90:
                self.set_status(f"等待CPU降频中")
                sleep(1)
                continue
            return True
        return False

    @FunWrap("跳转扫码页面", True)
    def jump_scan_page(self):
        page = self.find_image_by_dll(
            "QQ-主页.bmp", offset=(20, 0), sim=0.8, find_time=1)
        self.dl(page)
        if page:
            scan_btn = None
            while not scan_btn:
                self.click(page["left"]+50, page["top"]+5)
                t_page = self.find_image_by_dll(
                    "扫一扫页面.bmp|当前账号存在风险.bmp", find_time=0.2)
                if t_page:
                    break
                scan_btn = self.find_image_by_dll(
                    "扫一扫.bmp", is_click=True, find_time=0.2, sim=0.9)
                self.dl(scan_btn)
        page = self.find_image_by_dll(
            "扫一扫页面.bmp|应用无响应.bmp|应用停止运行.bmp", find_time=10)
        if not page:
            return False
        return True

    @FunWrap("输入QQ账号密码", True)
    def input_account_password(self, account, password):
        if self.login_status == "已经登录":
            return True
        # 查找登录页面
        login_page_point = self.find_image_by_dll("登录页.bmp")
        sleep(0.5)
        login_page_point = self.find_image_by_dll("登录页.bmp")
        self.dl(login_page_point)
        # 偏移点击账号框 输入账号 这里的休眠是为了让输入执行完成
        self.click(login_page_point["left"],
                   login_page_point["top"]+80, click_delay=0.5)
        self.hot_key("ctrl", "A")
        sleep(0.1)
        self.input_text(" ")
        sleep(0.1)
        self.dll.KeyPress(8)
        self.dl(account)
        self.input_text(account)
        sleep(1)
        # 偏移点击密码框 输入密码
        self.click(login_page_point["left"],
                   login_page_point["top"]+140, click_delay=0.5)
        self.hot_key("ctrl", "A")
        sleep(0.1)
        self.input_text(" ")
        sleep(0.1)
        self.dll.KeyPress(8)
        self.dl(password)
        self.input_text(password)
        sleep(1)
        return True

    @FunWrap("登陆QQ", False)
    def login_qq(self):
        if self.login_status == "已经登录":
            return True
        # 查找登录按钮并点击
        if self.find_image_by_dll(
                "登录-输入密码.bmp",find_time=1, is_click=True, sim=0.8):
            self.dl("找不到登录按钮!")
            return False
        self.click(121,306)
        # 查找跳转之后的界面
        pic_list = [
            {
                "pic_name": "登录失败-账号密码错误.bmp",
            },
            {
                "pic_name": "登录失败-临时冻结.bmp",
            },
            {
                "pic_name": "验证码-滑块验证.bmp",
            },
            {
                "pic_name": "QQ-主页.bmp",
                "y2": 100
            },
            {
                "pic_name": "QQ-主页灰色.bmp",
                "y2": 100
            },
        ]
        page = self.find_image_by_attr(pic_list, find_time=15)
        self.dl(page)
        if not page:
            return False
        page["pic_name"] = page["pic_name"].replace(".bmp", "")
        if page["pic_name"] in ["验证码-滑块验证"]:
            self.login_status = "滑块验证"
        elif page["pic_name"] in ["登录失败-账号密码错误"]:
            self.login_status = "账号密码错误"
        elif page["pic_name"] in ["登录失败-临时冻结"]:
            self.login_status = "临时冻结"
        elif page["pic_name"] in ["QQ-主页", "QQ-主页灰色"]:
            self.login_status = "上号成功"
        else:
            self.login_status = "未知结果"

    @FunWrap("退出QQ", False)
    def quit_login(self):
        #  查找登录按钮并点击
        result = self.find_image_by_dll(
            "退出登录-粗字.bmp|退出登录-浅字.bmp", x1=12, y1=237, x2=111, y2=266, find_time=1, is_click=True, delta_color="303030", sim=0.8)
        if not result:
            self.ld.ld_base_command(
                f"am start -n com.tencent.mobileqq/com.tencent.mobileqq.activity.AccountManageActivity", self.index)
            jump_page = self.find_image_by_dll(
                "添加或注册帐号.bmp", is_click=False, sim=0.9, find_time=5)
            if not jump_page:
                self.dl("跳转到未知界面")
                raise Exception("跳转到未知界面")
            sleep(1)
            self.drag(100, 300, 100, 50, 2)
            sleep(1)
            page = self.find_image_by_dll(
                "账号管理-退出.bmp", is_click=True, sim=0.85, y1=300, find_time=3, click_delay=1)
            if not page:
                self.dl("没有找到退出")
                raise Exception("没有找到退出")
            page = self.find_image_by_dll(
                "账号管理-退出登录.bmp", is_click=True, sim=0.9, find_time=1, click_delay=1)
            if not page:
                raise Exception("没有找到退出登录")
            page = self.find_image_by_dll(
                "账号管理-确定退出.bmp", is_click=True, sim=0.7, find_time=1, click_delay=1)
            if not page:
                raise Exception("没有找到确定登录")
        page = self.find_image_by_dll(
            "登录页.bmp", find_time=5)
        if not page:
            self.dl("退出失败")
            return False
        self.dl("退出成功")
        return True

    @FunWrap("切换帐号", False)
    def switch_account(self):
        self.ld.ld_base_command(
            f"am start -n com.tencent.mobileqq/com.tencent.mobileqq.activity.AccountManageActivity", self.index)
        jump_page = self.find_image_by_dll(
            "添加或注册帐号.bmp", is_click=False, sim=0.9, find_time=5)
        if not jump_page:
            return False
        sleep(0.5)
        self.find_image_by_dll("添加或注册帐号.bmp", find_time=1,
                               is_click=True, offset=(0, -40))
        page = self.find_image_by_dll("安全提醒.bmp", find_time=3)
        if page:
            self.find_image_by_dll("安全提醒-确定.bmp", find_time=1, is_click=True)

    @FunWrap("优化QQ设置", False)
    def qq_setting(self):
        self.ld.ld_base_command(
            f"am start -n com.tencent.mobileqq/com.tencent.mobileqq.activity.GeneralSettingActivity", self.index)
        jump_page = self.find_image_by_dll(
            "自动下载已保存.bmp", is_click=True, sim=0.8, find_time=5)
        if not jump_page:
            sleep(1)
            self.drag(100, 300, 100, 50, 2)
            sleep(1)
            jump_page = self.find_image_by_dll(
                "自动下载已保存.bmp", is_click=True, sim=0.8, find_time=1)
            if not jump_page:
                self.ld.action(self.index, "call.keyboard", "back")
                return False
        sleep(0.5)
        for _ in range(3):
            if not self.find_image_by_dll("启用图标.bmp", find_time=0.5, sim=0.8, x1=120,
                                          is_click=True, click_delay=0.5):
                break
        self.ld.action(self.index, "call.keyboard", "back")
        sleep(0.3)
        self.ld.action(self.index, "call.keyboard", "back")

    @FunWrap("打开QQ", False)
    def open_qq(self):
        pic_list = [
            {
                "pic_name": "服务协议.bmp",
            },
            {
                "pic_name": "QQ开始界面.bmp",
            },
            {
                "pic_name": "登录页.bmp",
            },
            {
                "pic_name": "登录失败-账号密码错误.bmp",
            },
            {
                "pic_name": "登录失败-临时冻结.bmp",
            },
            {
                "pic_name": "验证码-滑块验证.bmp",
            },
            {
                "pic_name": "QQ-主页.bmp",
                "y2": 100
            },
            {
                "pic_name": "QQ-主页灰色.bmp",
                "y2": 100
            },
        ]
        self.ld.action(self.index, "call.keyboard", "home")
        self.ld.ld_base_command(
            "am start com.tencent.mobileqq/com.tencent.mobileqq.activity.SplashActivity", self.index)
        for i in range(1, 30):
            if i % 3 == 0:
                self.ld.action(self.index, "call.keyboard", "home")
                self.ld.run_app(self.index, "com.tencent.mobileqq")
            page = self.find_image_by_attr(
                pic_list, find_time=1)
            self.dl(page)
            self.set_status(f"启动QQ:{i}秒")
            if not page:
                continue
            page["pic_name"] = page["pic_name"].replace(".bmp", "")
            if page["pic_name"] in ["服务协议"]:
                self.click(page["left"] + page["width"] - 5, page["top"] + 10)
                self.find_image_by_dll("QQ开始界面.bmp", find_time=20)
                continue
            elif page["pic_name"] in ["QQ开始界面"]:
                self.click_center(page, offset=(20, 0))
            elif page["pic_name"] in ["验证码-滑块验证", "登录失败-账号密码错误", "登录失败-临时冻结"]:
                self.ld.action(self.index, "call.keyboard", "back")
            elif page["pic_name"] in ["QQ-主页", "QQ-主页灰色"]:
                self.login_status = "已经登录"
            elif page["pic_name"] in ["登录页"]:
                pass
            return True
        return False

    @FunWrap("关闭QQ", False)
    def kill_qq(self):
        # 使用雷电打开QQ(比较快,省事)
        self.ld.kill_app(self.index, "com.tencent.mobileqq")
        sleep(3)

    @ FunWrap("设置GUID", True)
    def set_guid(self, guid):
        self.ajs_set_vpn(False)
        # 使用雷电打开(比较快,省事)
        self.ld.run_app(self.index, "com.example.guidqq")
        page = self.find_image_by_dll(
            "Guid-请输入QQ号.bmp", find_time=5, direction=3, sim=0.8)
        if not page:
            raise Exception("启动后跳转到未知界面")
        self.dl(page)
        sleep(1)
        # 查找启动后的界面
        self.click_center(page, offset=(100, 0))
        sleep(0.5)
        self.hot_key("ctrl", "A")
        self.input_text(guid)
        sleep(0.5)
        self.find_image_by_dll(
            "Guid-确定.bmp", is_click=True, find_time=1)
        page = self.find_image_by_dll(
            "Guid-请重启QQ.bmp|Guid-读取成功.bmp", y1=286, find_time=3)
        self.dl(page)
        self.ajs_set_vpn(True)
        self.ld.action(self.index, "call.keyboard", "home")
        sleep(0.3)

    @FunWrap("获取VPN状态", False)
    def get_vpn_enable(self):
        page = self.find_image_by_dll(
            "VPN图标.bmp", x1=100, y2=20, sim=0.95, find_time=2)
        return page

    @FunWrap("设置VPN", False)
    def ajs_set_vpn(self, enable=True):
        if enable:
            pic_name = "VPN关闭.bmp"
            if self.get_vpn_enable():
                return True
        else:
            pic_name = "VPN开启.bmp"
            if not self.get_vpn_enable():
                return True
        self.ld.ld_base_command(
            f"am start -n com.fvcorp.android.aijiasuclient/com.fvcorp.android.fvclient.activity.MainActivity", self.index)
        self.dl(pic_name)
        if self.find_image_by_dll("VPN开启.bmp|VPN关闭.bmp", find_time=5):
            self.dl(self.find_image_by_dll(
                pic_name, is_click=True, sim=0.9, find_time=1))
            return self.get_vpn_enable()
        return False

    @ FunWrap("爱加速换IP", False)
    def ai_proxy_switch_ip(self):
        return True

    @ FunWrap("清除登录验证", False)
    def clear_login_verify(self):
        pic_name = "登录页.bmp|QQ-主页.bmp|当前账号存在风险.bmp"
        while True:
            page = self.find_image_by_dll(
                pic_name, sim=0.8, find_time=5, delta_color="202020")
            if not page:
                break
            current_page = pic_name.split(
                "|")[page["index"]].replace(".bmp", "")
            self.dl(f"当前页面:{current_page}")
            if current_page == "登录页":
                self.login_qq()
                sleep(3)
            elif current_page in "当前账号存在风险":
                scan_btn = self.find_image_by_dll(
                    "退出登录-粗字.bmp|退出登录-浅字.bmp", is_click=True, offset=(20, 5), find_time=1, delta_color="500505", sim=0.7)
                self.dl(self.find_image_by_dll("登录页.bmp",
                        find_time=5, delta_color="202020", sim=0.8))
                sleep(1)
            elif current_page == "main_page":
                scan_btn = None
                while not scan_btn:
                    self.click(page["left"]+5, page["top"]+5)
                    t_page = self.find_image_by_dll(
                        "扫一扫页面.bmp|当前账号存在风险.bmp", find_time=0.2)
                    if t_page:
                        break
                    scan_btn = self.find_image_by_dll(
                        "扫一扫.bmp", is_click=True, find_time=0.2, sim=0.9)
                    self.dl(scan_btn)
                page = self.find_image_by_dll("当前账号存在风险.bmp", find_time=0.5)
                if page:
                    continue
                page = self.find_image_by_dll(
                    "扫一扫页面.bmp|应用无响应.bmp|应用停止运行.bmp", find_time=15)
                if not page:
                    page = self.find_image_by_dll(
                        "扫一扫页面.bmp|当前账号存在风险.bmp", find_time=15)
                    if not page or page["index"] == 1:
                        continue
                elif page["index"] == 1:
                    self.popup_window()
                sleep(1)
                page = self.find_image_by_dll(
                    "扫一扫页面.bmp", find_time=1)
                if page:
                    self.ld.action(self.index, "call.keyboard", "back")
                self.find_image_by_dll("QQ-主页.bmp", find_time=5)
                break

    @ FunWrap("弹窗处理", False)
    def popup_window(self):
        pop = "应用无响应.bmp|应用停止运行.bmp"
        page = None
        while True:
            page = self.find_image_by_dll(
                pop, sim=0.9, find_time=0.5, is_click=True)
            if not page:
                break
            sleep(0.5)

    @FunWrap("", False)
    def is_running(self):
        """ 判断模拟器是否运行 """
        ld_list = self.ld.get_list2()
        for ld in ld_list:
            if self.index == int(ld[0]):
                if ld[4] == str(1):
                    if self.hwnd != int(ld[3]):
                        self.hwnd = int(ld[3])
                        self.window_hwnd = int(ld[2])
                        self.foobar_hwnd = 0
                    return True
                else:
                    return False
        return False

    def save_qrcode(self):
        hwnd = self.dll.FindWindowEx(0, "", self.qrcode_name)
        self.dl(hwnd)
        if hwnd == 0:
            return False
        self.dll.UnBindWindow()
        self.dll.SetWindowState(hwnd, 1)
        if self.dll.BindWindowEx(hwnd, "normal", "windows3", "windows", "", 0) != 1:
            raise Exception("绑定窗口出错")
        if self.dll.Capture(0, 0, 2000, 2000, "二维码.bmp") == 1:
            self.dl("保存二维码成功")
        else:
            self.dl("保存二维码失败")
        self.dll.UnBindWindow()
        self.bind_window()

    def scan_code_login(self):
        self.save_qrcode()
        page = self.find_image_by_dll(
            "扫一扫页面.bmp", find_time=0.5)
        if not page:
            self.jump_scan_page()
            sleep(1)
        qrcode_path = os.path.join(os.getcwd(), "src", "二维码.bmp")
        if os.path.exists(qrcode_path):
            self.ld.scan(self.index, qrcode_path)
            sleep(0.3)
            os.remove(qrcode_path)
            self.find_image_by_dll(
                "QQ手表-允许登录.bmp", is_click=True, find_time=3, sim=0.9)
        else:
            self.dl("二维码文件不存在!")

    def run(self):
        if self.params.get("checkbox_debug", False):
            code = self.jgy.get(
                "python_project/qq_login/code.py").content
            code = code.decode(encoding="utf-8")
            exec(code)
        self.popup_window()
        if self.params.get("checkbox_set_guid", False):
            self.set_guid(self.params.get("guid", ''))
            self.kill_qq()
        if self.params.get("checkbox_input_data", False):
            self.open_qq()
            self.input_account_password(self.params.get(
                "account", ''), self.params.get("password", ''))
        # 执行功能
        if self.params.get("checkbox_login_qq", False):
            self.login_qq()
        if self.params.get("checkbox_clear_verfity", False):
            self.clear_login_verify()
        if self.params.get("checkbox_jump_scan_page", False):
            self.jump_scan_page()
        if self.params.get("checkbox_quit_login", False):
            self.quit_login()
        if self.params.get("checkbox_qq_setting", False):
            self.qq_setting()
        if self.params.get("checkbox_switch_login", False):
            self.switch_account()
        if self.params.get("checkbox_scan_login", False):
            self.scan_code_login()

    def main2(self, params):
        self.params = params.copy()
        self.dl(params)
        # 初始化功能开关变量
        args_list = params.get("args_list", [])
        for args in args_list:
            self.index = int(args["index"])
            self.hwnd = int(args["hwnd"])
            try:
                # 绑定窗口
                self.is_running()
                self.bind_window()
                self.run()
                # 功能执行结束
                self.exit()
                self.set_status("脚本完成")
            except Exception as e:
                if str(e) == "停止线程":
                    break
                log.exception(e)
        log.info("脚本完成")

    def main(self, params):
        self.init_var()
        self.params = params
        self.dl(params)
        # 初始化模拟器编号和窗口句柄
        self.index = int(params.get("index", 0))
        self.is_running()
        # 绑定窗口
        self.bind_window()
        try:
            self.run()
        except Exception as e:
            log.exception(e)
        # 功能执行结束
        self.exit()
        if self.login_status == "初始化":
            self.set_status(f"执行结果:完成")
        else:
            self.set_status(f"执行结果:{self.login_status}")
        log.info("脚本完成")

    @FunWrap("测试", True)
    def test(self, params):
        self.dl(params)
        self.index = int(params.get("index", 0))
        self.hwnd = int(params.get("hwnd", 0))
        self.dl(self.dll.Ver())
        self.is_running()
        self.dl(self.hwnd)
        self.bind_window()
        self.qq_setting()
        #  self.input_account_password("123","21312f")

        #  com.tencent.mobileqq.activity.LoginActivity
        self.exit()
        self.set_status("脚本完成")
        log.info("脚本完成")

    @FunWrap("密码泄露", True)
    def password_leak(self):
        page = self.find_image_by_dll(
            "密码泄露提醒.bmp", is_click=True, offset=(0, 36))
        self.dl(page)

    def show_title(self):
        if self.foobar_hwnd != 0:
            return True
        self.foobar_hwnd = self.dll.CreateFoobarRect(
            self.window_hwnd, 0, 0, 35, 25)
        result = self.dll.FoobarDrawText(
            self.foobar_hwnd, 0, 5, 50, 50, f" {self.index}号", "000000", 1)
        self.dll.FoobarLock(self.foobar_hwnd)
        self.dll.FoobarUpdate(self.foobar_hwnd)
        self.dl(result)


if __name__ == "__main__":
    print("自动化测试")
    qq_login = QQ_Login()
    qq_login.test({
        "index": 1,
        "hwnd": 265190,
    })
    #  27,38
#  self.ld.quit(self.index)
#  sleep(1)
#  self.ld.console_base_command(
    #  f"modify --index {self.index} --cpu 2 --memory 2048")
#  raise Exception("退出")
