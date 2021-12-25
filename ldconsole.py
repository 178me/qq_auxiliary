import subprocess
import os
import win32com.client
from lib import log


class LdConsole:

    def __init__(self, exec_path=None):
        if not exec_path:
            exec_path = self.find_leidian_path()
        self.exec_path = exec_path

    @staticmethod
    def find_leidian_path():
        """ 查找雷电模拟器启动路径 """
        task_name = "查找雷电模拟器启动路径"
        log.info(f"{task_name} 开始")
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            path = os.path.join(os.path.expanduser(r'~'), "Desktop")
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    if "雷电多开器" in filename:
                        path = dirpath + "\\" + filename
            shortcut = shell.CreateShortCut(path).TargetPath
            shortcut = os.path.dirname(shortcut)
            exec_path = str(shortcut)
            #  self.exec_path = r'D:\leidian\LDPlayer4.0' + r'\ldconsole.exe'
            if "LDPlayer" not in exec_path:
                raise Exception("雷电模拟器路径查找失败")
            return exec_path
        except Exception as e:
            log.exception(e)
            log.error("{task_name} 出错")
            raise Exception("雷电模拟器路径查找失败")

    def ld_base_command(self, command, index, timeout=10):
        """ 雷电基础命令 """
        log.info(f"{command}")
        result = subprocess.check_output(
            f"{self.exec_path}\\ld.exe -s {index} {command}", timeout=timeout, encoding="gbk")
        # log.info(result)
        return result

    def console_base_command(self, command, timeout=10):
        """ 雷电控制台基础命令 """
        log.info(f"{command}")
        result = subprocess.check_output(
            f"{self.exec_path}\\ldconsole.exe {command}", timeout=timeout, encoding="gbk")
        #  log.info(result)
        return result

    def get_list2(self):
        """ 获取模拟器列表 """
        mnq_list = self.console_base_command("list2").split("\n")
        mnq_list.pop()
        for index, value in enumerate(mnq_list):
            mnq_list[index] = value.split(",")
        return mnq_list

    def launch(self, index):
        """ 启动模拟器 """
        self.console_base_command(f"launch --index {index}")

    def quit(self, index):
        """ 退出模拟器 """
        self.console_base_command(f"quit --index {index}")

    def quit_all(self):
        """ 退出所有模拟器 """
        self.console_base_command("quitall")

    def reboot(self, index):
        """ 重启模拟器 """
        self.console_base_command(f"reboot --index {index}")

    def run_app(self, index, package_name):
        """ 启动App """
        self.console_base_command(
            f"runapp --index {index} --packagename {package_name}")

    def kill_app(self, index, package_name):
        """ 关闭App """
        self.console_base_command(
            f"killapp --index {index} --packagename {package_name}")

    def install_app(self, index, filename):
        """ 安装App """
        self.console_base_command(
            f"installapp --index {index} --filename {filename}")

    def uninstall_app(self, index, package_name):
        """ 卸载App """
        self.console_base_command(
            f"uninstallapp --index {index} --packagename {package_name}")

    def downcpu(self, index, rate=50):
        """ 降低CPU使用率 """
        self.console_base_command(f"downcpu --index {index} --rate {rate}")

    def action(self, index, key, value):
        """ 执行动作
            --key call.keyboard --value back|home|menu|volumeup|volumedown
            --key call.input --value *
        """
        self.console_base_command(
            f"action --index {index} --key {key} --value {value}")

    def scan(self, index, file):
        """ 扫码 """
        self.console_base_command(f"scan --index {index} --file {file}")

    def sort(self):
        """ 模拟器排序 """
        self.console_base_command("sortWnd")

    def global_setting(self, fps=10, audio=0, fastplay=1, cleanmode=1):
        """ 全局设置 """
        self.console_base_command(
            f"glbalsetting --fps {fps} --audio {audio} --fastplay {fastplay} --cleanmode {cleanmode}")

    def screencap(self, index, filename=None):
        """ 屏幕截图 """
        if not filename:
            filename = f"/sdcard/Pictures/screenshot_{index}.png"
        self.ld_base_command(f"screencap -p {filename}", index)

    def get_page_xml(self, index, filename=None):
        """ 获取页面布局信息 """
        if not filename:
            filename = f"/sdcard/Pictures/xml_{index}.xml"
        return self.ld_base_command(f"uiautomator dump {filename}", index)

    def tap(self, index, x, y):
        """ 鼠标点击 """
        try:
            self.ld_base_command(f"input tap {x} {y}", index)
            return True
        except Exception as e:
            log.exception(e)
            return False

    def swipe(self, index, x1, y1, x2, y2, delay=500):
        """ 鼠标滑动 """
        try:
            self.ld_base_command(
                f"input swipe {x1} {y1} {x2} {y2} {delay}", index)
            return True
        except Exception as e:
            log.exception(e)
            return False


if __name__ == "__main__":
    print("雷电命令行 自动化测试")
    ld = LdConsole()
