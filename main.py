import sys
import os
import re
import pyperclip
from time import sleep
from PyQt5 import (uic, QtGui)
from PyQt5.Qt import (QApplication, QThread, pyqtSignal)
from PyQt5.QtCore import (QObject, Qt)
from PyQt5.QtWidgets import (
    QMainWindow, QHeaderView, QAbstractItemView, QTableWidgetItem)
from my_qt_material import apply_stylesheet
from lib import log, Config, JianGuoYun, Other
from ldconsole import LdConsole
from qq_login import QQ_Login


class Console_Stream(QObject):
    console_signal = pyqtSignal(str)  # 定义一个发送str的信号

    def write(self, text):
        self.console_signal.emit(str(text))
        QApplication.processEvents()  # 实时更新UI界面


class MyThread(QThread):
    status_signal = pyqtSignal(str)  # 状态栏消息设置 (考虑后期去掉)

    def __init__(self, func=None, args=None, obj=None, signal=None):
        super(MyThread, self).__init__()
        # 要执行的函数
        self.func = func
        # 函数参数
        self.fun_args = args
        # 函数对应的对象
        self.fun_object = obj
        # 给对象设置信号
        if self.fun_object:
            self.fun_object.set_script_message = signal

    def run(self):
        ''' 执行对应的任务 '''
        try:
            if not self.func:
                return False
            if self.fun_args:
                result = self.func(self.fun_args)
            else:
                result = self.func()
        except Exception as e:
            if "停止线程" in str(e):
                if self.fun_object:
                    log.info(f"{self.fun_object.index} 号模拟器脚本已停止")
            else:
                log.exception(e)
            result = False
        if result:
            if isinstance(result,bool):
                self.status_signal.emit("任务执行成功")
            else:
                self.status_signal.emit(result)
        else:
            if isinstance(result,bool):
                self.status_signal.emit("任务执行失败")
            else:
                self.status_signal.emit(result)


class Function_Run(QObject):
    # 表格状态的信号
    table_signal = pyqtSignal(int, str)

    def __init__(self, ld_path=None):
        super().__init__()
        self.jgy = JianGuoYun("1403341393@qq.com", "abhdwrkfxxrnhnyf")
        self.ld = LdConsole(ld_path)
        self.ld.global_setting()
        # 线程对象列表
        self.thread_list = []
        self.list2 = []
        self.qq_info_list = []
        self.one_thread = None

    def split_qq_info(self, number_index: int = -1):
        desktop_path = os.path.join(os.path.expanduser(r'~'), "Desktop")
        if os.path.exists(os.path.join(desktop_path, "1账号.txt")) and os.path.exists(os.path.join(desktop_path, "2账号.txt")):
            return True
        qq_info_list = []
        qq_info_path = None
        if number_index > 0:
            number_text = f"{number_index}号机.txt"
        else:
            number_text = "号机.txt"
        filenames = [filename for x in os.walk(
            desktop_path) for filename in x[2]]
        for filename in filenames:
            if number_text in filename:
                if os.path.exists(os.path.join(desktop_path + os.sep + filename)):
                    qq_info_path = desktop_path + os.sep + filename
        if not qq_info_path:
            raise Exception("服务器信息未找到")
        with open(qq_info_path, "r", encoding="utf-8") as file_reader:
            qq_info_list_temp = file_reader.read().replace("\r", "").split("\n")
        for i, qq_info in enumerate(qq_info_list_temp):
            if len(qq_info) < 5:
                continue
            qq_info_list.append(qq_info)
        with open(os.path.join(desktop_path, "1账号.txt"), "w", encoding="utf-8") as file_writer:
            file_writer.write(
                "\n".join(qq_info_list[:15]))
        with open(os.path.join(desktop_path, "2账号.txt"), "w", encoding="utf-8") as file_writer:
            if len(qq_info_list) > 15:
                file_writer.write(
                    "\n".join(qq_info_list[15:]))
            else:
                file_writer.write("")

    def get_qq_info_list(self, number_index: int):
        desktop_path = os.path.join(os.path.expanduser(r'~'), "Desktop")
        qq_info_list = []
        qq_info_path = None
        if number_index > 0:
            number_text = f"{number_index}账号.txt"
        else:
            number_text = "账号.txt"
        filenames = [filename for x in os.walk(
            desktop_path) for filename in x[2]]
        for filename in filenames:
            if number_text in filename:
                qq_info_path = desktop_path + os.sep + filename
        if not qq_info_path:
            raise Exception("服务器信息未找到")
        with open(qq_info_path, "r", encoding="utf-8") as file_reader:
            qq_info_list_temp = file_reader.read().replace("\r", "").split("\n")
        qq_info_text = ""
        for i, qq_info in enumerate(qq_info_list_temp):
            if len(qq_info) < 5:
                continue
            if len(re.split(r"[-]+", qq_info)) <= 3:
                qq_info_text += qq_info + "----" + str(i+1) + "\n"
                qq_info_list.append(
                    re.split(r"[-]+", qq_info + "----" + str(i+1)))
                continue
            qq_info_text += qq_info + "\n"
            qq_info_list.append(re.split(r"[-]+", qq_info))
        with open(qq_info_path, "w", encoding="utf-8") as file_writer:
            file_writer.write(qq_info_text)
        return qq_info_list

    def start_script(self, args):
        ''' 启动脚本(后期优化成可选择功能) '''
        self.split_qq_info()
        self.qq_info_list = self.get_qq_info_list(args["number_index"])
        #  return True
        self.list2 = self.ld.get_list2()
        #  log.info(self.qq_info_list)
        #  log.info(args["selected_list"])
        if "单线程" in args["thread_mode"]:
            args_list = []
            for index in args['selected_list']:
                # 查看该模拟器是否存在并且启动
                ld_list = self.search_ld(index)
                #  log.info(ld_list)
                if not ld_list:
                    continue
                qq_info = self.search_qq_info(index)
                #  log.info(qq_info)
                if not qq_info:
                    continue
                args_list.append({
                    "index": ld_list[0],
                    "hwnd": ld_list[3],
                    "account": qq_info[0],
                    "password": qq_info[1],
                    "guid": qq_info[2],
                })
            if not args_list:
                return True
            if not self.one_thread:
                fun_object = QQ_Login(self.ld.exec_path)
                self.one_thread = MyThread(func=fun_object.main2, obj=fun_object,
                                           signal=self.table_signal)
            if self.one_thread.isRunning():
                log.info("单线程已运行")
            else:
                args["script_args"]["args_list"] = args_list
                self.one_thread.fun_args = args["script_args"].copy()
                self.one_thread.start()
            return True
        # 多线程
        for index in args['selected_list']:
            # 查看该模拟器是否存在并且启动
            ld_list = self.search_ld(index)
            # ld_list = ['1', '', '', '0']
            if not ld_list:
                log.info("该模拟器不存在!")
                continue
            qq_info = self.search_qq_info(index)
            if not qq_info:
                log.info("该账号信息不存在!")
                continue
            # 获取该模拟器对应的线程对象
            thread = self.search_thread(index)
            if not thread:
                fun_object = QQ_Login(self.ld.exec_path)
                thread = MyThread(func=fun_object.main, obj=fun_object,
                                  signal=self.table_signal)
                self.add_thread(thread)
            if thread.isRunning():
                log.info(f"{index}号模拟器脚本运行中")
            else:
                args["script_args"]["index"] = ld_list[0]
                args["script_args"]["hwnd"] = ld_list[3]
                args["script_args"]["account"] = qq_info[0]
                args["script_args"]["password"] = qq_info[1]
                args["script_args"]["guid"] = qq_info[2]
                thread.fun_args = args["script_args"].copy()
                thread.start()
                sleep(0.5)
        return True

    def stop_script(self, args):
        ''' 停止脚本 '''
        if "单线程" in args["thread_mode"]:
            if not self.one_thread:
                return True
            if not self.one_thread.isRunning():
                log.info("单线程已停止")
                return True
            if self.one_thread.fun_object:
                self.one_thread.fun_object.status = "stop"
            log.info("单线程停止请求已发送")
            return True
        # 多线程
        for index in args['selected_list']:
            thread = self.search_thread(index)
            if not thread:
                continue
            if not thread.isRunning():
                log.info(f"{index}号模拟器脚本已停止")
                continue
            thread.fun_object.status = "stop"
            log.info(f"{index}号模拟器脚本停止请求发送")
        return True

    def stop_thread(self):
        for thread in self.thread_list:
            if not thread.isRunning():
                continue
            thread.fun_object.status = "stop"

    def search_qq_info(self, index):
        ''' 获取模拟器对应的信息 '''
        for qq_info in self.qq_info_list:
            if str(index) in qq_info:
                return qq_info
        return None

    def search_ld(self, index):
        ''' 获取模拟器对应的信息 '''
        for ld_list in self.list2:
            if str(ld_list[0]) != str(index):
                continue
            if str(ld_list[4]) != str(1):
                continue
            return ld_list
        return False

    def search_thread(self, index):
        ''' 获取线程对象 '''
        for thread in self.thread_list:
            if not thread.fun_object:
                continue
            if thread.fun_object.index != index:
                continue
            return thread
        return False

    def add_thread(self, thread):
        ''' 添加线程对象 '''
        self.thread_list.append(thread)

    def import_qq(self, args):
        qq_info_list = self.get_qq_info_list(args["number_index"])
        qq_info_text = ""
        for qq_info in qq_info_list:
            qq_info_text += f"{qq_info[0]}----{qq_info[1]}----6----{qq_info[2]}\r\n"
        pyperclip.copy(qq_info_text)
        return True

    def copy_qq_number(self, args):
        self.qq_info_list = self.get_qq_info_list(args["number_index"])
        log.info(self.qq_info_list)
        if not args["selected_list"]:
            return False
        index = args["selected_list"][0]
        qq_info = self.search_qq_info(index)
        if not qq_info:
            return False
        pyperclip.copy(qq_info[0])
        return f"当前复制的QQ:{qq_info[0]}"

    def copy_password(self, args):
        if not self.qq_info_list:
            self.qq_info_list = self.get_qq_info_list(args["number_index"])
        if not args["selected_list"]:
            return False
        index = args["selected_list"][0]
        qq_info = self.search_qq_info(index)
        if not qq_info:
            return False
        pyperclip.copy(qq_info[1])
        return f"当前复制的密码:{qq_info[1]}"

    def copy_guid(self, args):
        if not self.qq_info_list:
            self.qq_info_list = self.get_qq_info_list(args["number_index"])
        if not args["selected_list"]:
            return False
        index = args["selected_list"][0]
        qq_info = self.search_qq_info(index)
        if not qq_info:
            return False
        pyperclip.copy(qq_info[2])
        return f"当前复制的GUID:{qq_info[2]}"

    def restart_mnq(self, args):
        ''' 重启模拟器 '''
        for index in args['selected_list']:
            log.info(f"重启模拟器{index}")
            self.ld.quit(index)
            sleep(0.5)
            self.ld.console_base_command(
                f"modify --index {index} --cpu 2 --memory 3072")
            self.ld.launch(index)
        return True

    def open_mnq(self, args):
        ''' 打开模拟器 '''
        for index in args['selected_list']:
            log.info(f"打开模拟器{index}")
            self.ld.console_base_command(
                f"modify --index {index} --cpu 2 --memory 2048")
            self.ld.launch(index)
        return True

    def close_mnq(self, args):
        ''' 关闭模拟器 '''
        for index in args['selected_list']:
            log.info(f"关闭模拟器{index}")
            self.ld.quit(index)
        return True

    def sort_window(self):
        ''' 排列模拟器 '''
        log.info("排序")
        self.ld.sort()


class TableWidget():
    def __init__(self, table):
        # 初始化表格控件
        self.table = table
        # 显示网格
        self.table.setShowGrid(True)
        # 设置表头是否自动排序
        self.table.setSortingEnabled(False)
        # 初始化表格控件
        self.table = table
        # 调整列宽
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        # 忘了
        #  self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 选中表头不高亮
        self.table.horizontalHeader().setHighlightSections(False)
        # 隐藏垂直表头
        self.table.verticalHeader().setVisible(False)
        # 取消隔行变色
        self.table.setAlternatingRowColors(False)
        # 不可编辑
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 选中一行
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 多选模式
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table.setStyleSheet("selection-background-color:#047cd4;")

    def refresh_table(self, list2):
        # 清除表格内容
        self.table.setRowCount(0)
        self.table.clearContents()
        if int(list2[0][0]) == 0:
            del list2[0]
        # 添加模拟器信息
        for i, ld_data in enumerate(list2):
            self.table.setRowCount(self.table.rowCount() + 1)
            # 模拟器ID
            newItem = QTableWidgetItem(ld_data[0])
            # 水平居中 | 垂直居中
            newItem.setTextAlignment(4 | 128)
            self.table.setItem(i, 0, newItem)
            # 模拟器标题
            newItem = QTableWidgetItem(ld_data[1])
            newItem.setTextAlignment(4 | 128)
            self.table.setItem(i, 1, newItem)
            # 模拟器启动状态
            if ld_data[4] == "0":
                newItem = QTableWidgetItem("未启动")
            elif ld_data[4] == "1":
                newItem = QTableWidgetItem("已启动")
            else:
                newItem = QTableWidgetItem("未知")
            newItem.setTextAlignment(4 | 128)
            self.table.setItem(i, 2, newItem)
            # 脚本状态
            newItem = QTableWidgetItem("未开始")
            newItem.setTextAlignment(4 | 128)
            self.table.setItem(i, 3, newItem)
        # 内容自适应
        self.table.horizontalHeader().resizeSections(QHeaderView.ResizeToContents)
        self.table.setColumnWidth(3, 160)

    def set_item_status(self, index, status_text):
        # 设置脚本状态
        item = self.get_row_by_index(index)
        if item:
            item.setText(status_text)
        QApplication.processEvents()  # 实时更新UI界面

    def get_row_by_index(self, index):
        index = int(index)
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 0)
            if not item:
                continue
            if int(item.text()) == index:
                return self.table.item(i, 3)
        return None

    def get_selected_list(self):
        ''' 获取已选择的列表 '''
        selected_list = []
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 0)
            if not item:
                continue
            if not item.isSelected():
                continue
            selected_list.append(int(item.text()))
        return selected_list

    def select_all(self):
        ''' 选择全部 '''
        self.table.selectAll()
        return True

    def select_cancel(self):
        ''' 取消选择 '''
        for i in range(self.table.rowCount()):
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if not item:
                    continue
                item.setSelected(False)

    def select_invert(self):
        ''' 反向选择 '''
        for i in range(self.table.rowCount()):
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if not item:
                    continue
                if item.isSelected():
                    item.setSelected(False)
                else:
                    item.setSelected(True)


class mainwindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.password_verfity()
            self.version = "V2.0.0"
            # 加载UI
            self.ui = uic.loadUi("./input/mainwindow.ui")
            # 初始化控制台输出流
            self.init_stdout()
            # 初始化数据
            self.init_data()
            # 初始化功能函数
            self.init_run()
            # 初始化线程
            self.init_thread()
            # 初始化UI事件
            self.init_event()
            # 初始化连接
            self.init_connect()
            # 初始化UI
            self.init_ui()
        except Exception as e:
            log.exception(e)

    def password_verfity(self):
        #  password = input("请输入密码:")
        my_password = None
        try:
            my_password = Other.get_netpad_text("2ab97e3a0189004c")["note_content"].replace("\n","")
        except:
            log.info("遇到错误~")
        if "123" != my_password:
            sys.exit(0)

    def get_ui_object_value(self, id_list=[]):
        ''' 获取UI对象的值 '''
        ui_object_param = {}
        for ui_object_id in id_list:
            ui_object = getattr(self.ui, ui_object_id, False)
            if not ui_object:
                continue
            if "QCheckBox" in ui_object.metaObject().className():
                value = ui_object.isChecked()
            elif "QLineEdit" in ui_object.metaObject().className():
                value = ui_object.text()
            elif "QTextEdit" in ui_object.metaObject().className():
                value = ui_object.toPlainText()
            elif "QComboBox" in ui_object.metaObject().className():
                value = ui_object.currentText()
            else:
                value = None
            ui_object_param[ui_object_id] = value
        return ui_object_param

    def get_ui_object(self, keys=["btn_", "checkbox_", "cmb", "text_", "input_"]):
        ''' 获取UI对象 '''
        ui_key_list = keys
        ui_object_list = []
        for attr in dir(self.ui):
            for key in ui_key_list:
                # 根据UI对象名获取
                if key in attr:
                    #  print(getattr(self.ui, attr))
                    ui_object_list.append(getattr(self.ui, attr))
        #  print(ui_object_list)
        return ui_object_list

    def save_data(self):
        for ui_object in self.ui_object_list:
            if "QCheckBox" in ui_object.metaObject().className():
                self.config.set(
                    "ui_config", ui_object.objectName(), str(ui_object.isChecked()))
            elif "QLineEdit" in ui_object.metaObject().className():
                self.config.set(
                    "ui_config", ui_object.objectName(), str(ui_object.text()))
            elif "QComboBox" in ui_object.metaObject().className():
                self.config.set(
                    "ui_config", ui_object.objectName(), ui_object.currentText())
        self.config.write()

    def init_data(self):
        # 初始化配置模块
        self.config = Config()
        # 获取所有UI对象
        self.ui_object_list = self.get_ui_object()
        # 获取UI配置
        ui_config = self.config.get("ui_config")
        # 恢复数据
        for key, value in ui_config:
            ui_object = getattr(self.ui, key, False)
            if not ui_object:
                continue
            if "QCheckBox" in ui_object.metaObject().className():
                if "False" in value:
                    value = False
                else:
                    value = True
                ui_object.setChecked(value)
            if "QLineEdit" in ui_object.metaObject().className():
                ui_object.setText(value)
            if "QComboBox" in ui_object.metaObject().className():
                ui_object.setCurrentText(value)

    def init_thread(self):
        self.run_thread = MyThread()

    def init_run(self):
        # 获取雷电路径
        ld_path = self.config.get("app", "ld_path")
        self.fc_run = Function_Run(ld_path=ld_path)
        # 设置雷电状态
        self.config.set("app", "ld_path", self.fc_run.ld.exec_path)
        # 验证
        code = self.fc_run.jgy.get(
            "python_project/qq_login/isUpdate.txt").content
        code = code.decode(encoding="utf-8")
        if code != "Y":
            self.closeEvent(0)
            sys.exit(0)

    def init_event(self):
        # 关闭事件
        self.ui.closeEvent = self.closeEvent

    def init_stdout(self):
        sys.stdout = Console_Stream(console_signal=self.console_output)
        sys.stderr = Console_Stream(console_signal=self.console_output)
        if hasattr(log, "setSteam"):
            log.handlers[1].setStream(sys.stdout)
        else:
            log.handlers[1].stream = sys.stdout

    def init_connect(self):
        ''' 按钮连接 '''
        # 初始化表格
        self.table = TableWidget(self.ui.table_emulator)
        self.table.refresh_table(self.fc_run.ld.get_list2())
        self.fc_run.table_signal.connect(self.table.set_item_status)
        # 状态栏
        self.run_thread.status_signal.connect(self.show_message)
        # 模拟器操作
        self.ui.btn_select_all.clicked.connect(self.table.select_all)
        self.ui.btn_select_cancel.clicked.connect(self.table.select_cancel)
        self.ui.btn_select_invert.clicked.connect(self.table.select_invert)
        self.ui.btn_refresh_table.clicked.connect(
            lambda: self.table.refresh_table(self.fc_run.ld.get_list2()))
        # 模拟器操作
        self.ui.btn_open_ld.clicked.connect(
            lambda: self.task_manage({
                "name": self.fc_run.open_mnq,
                "args": {
                    "selected_list": self.table.get_selected_list(),
                }
            }))
        self.ui.btn_close_ld.clicked.connect(
            lambda: self.task_manage({
                "name": self.fc_run.close_mnq,
                "args": {
                    "selected_list": self.table.get_selected_list(),
                }
            }))
        self.ui.btn_restart_ld.clicked.connect(
            lambda: self.task_manage({
                "name": self.fc_run.restart_mnq,
                "args": {
                    "selected_list": self.table.get_selected_list(),
                }
            }))
        self.ui.btn_sort_window.clicked.connect(self.fc_run.sort_window)
        # 脚本设置
        self.ui.btn_startup_script.clicked.connect(
            lambda: self.task_manage({
                "name": self.fc_run.start_script,
                "args": {
                    "selected_list": self.table.get_selected_list(),
                    "thread_mode": self.ui.cmb_thread.currentText(),
                    "number_index": int(self.ui.input_number_index.text()),
                    "script_args": self.get_ui_object_value([
                        "checkbox_set_guid", "checkbox_input_data", "checkbox_login_qq",
                        "checkbox_clear_verfity", "checkbox_jump_scan_page", "checkbox_quit_login",
                        "checkbox_scan_login", "checkbox_debug","checkbox_switch_login","checkbox_qq_setting"
                    ])
                }
            }))
        self.ui.btn_stop_script.clicked.connect(
            lambda: self.task_manage({
                "name": self.fc_run.stop_script,
                "args": {
                    "selected_list": self.table.get_selected_list(),
                    "thread_mode": self.ui.cmb_thread.currentText()
                }
            }))
        self.ui.btn_import_qq.clicked.connect(
            lambda: self.task_manage({
                "name": self.fc_run.import_qq,
                "args": {
                    "number_index": int(self.ui.input_number_index.text())
                }
            }))
        self.ui.btn_copy_qq_number.clicked.connect(
            lambda: self.task_manage({
                "name": self.fc_run.copy_qq_number,
                "args": {
                    "selected_list": self.table.get_selected_list(),
                    "number_index": int(self.ui.input_number_index.text())
                }
            }))
        self.ui.btn_copy_password.clicked.connect(
            lambda: self.task_manage({
                "name": self.fc_run.copy_password,
                "args": {
                    "selected_list": self.table.get_selected_list(),
                    "number_index": int(self.ui.input_number_index.text())
                }
            }))
        self.ui.btn_copy_guid.clicked.connect(
            lambda: self.task_manage({
                "name": self.fc_run.copy_guid,
                "args": {
                    "selected_list": self.table.get_selected_list(),
                    "number_index": int(self.ui.input_number_index.text())
                }
            }))
        self.ui.checkbox_quit_login.stateChanged.connect(
            self.checkbox_quit_login_state_changed)
        self.ui.checkbox_set_guid.stateChanged.connect(
            self.checkbox_set_guid_state_changed)
        self.ui.checkbox_auto_enable.stateChanged.connect(
            self.checkbox_auto_enable_state_changed)

    def init_ui(self):
        # 隐藏控制台
        Other.set_console(False)
        # 设置窗口标题
        self.ui.setWindowTitle(f"上号中控 {self.version}")
        # 窗口置顶
        self.ui.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.ui.resize(780, 470)
        # 窗口显示
        self.ui.show()

    def closeEvent(self, event):
        ''' 关闭事件 '''
        try:
            self.save_data()
            self.fc_run.stop_thread()
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            if hasattr(log, "setSteam"):
                log.handlers[1].setStream(sys.stdout)
            else:
                log.handlers[1].stream = sys.stdout
        except Exception as e:
            log.exception(e)

    def checkbox_quit_login_state_changed(self, changed):
        ''' 退出登录变化事件 '''
        if changed == 2:
            checkbox_list = self.get_ui_object(["checkbox_"])
            for checkbox_obj in checkbox_list:
                if checkbox_obj.objectName() in "checkbox_quit_login":
                    continue
                checkbox_obj.setChecked(False)

    def checkbox_set_guid_state_changed(self, changed):
        ''' 设置GUID变化事件 '''
        if changed == 2:
            checkbox_list = self.get_ui_object(["checkbox_"])
            for checkbox_obj in checkbox_list:
                if checkbox_obj.objectName() in ["checkbox_set_guid", "checkbox_input_data", "checkbox_login_qq"]:
                    checkbox_obj.setChecked(True)
                    continue
                checkbox_obj.setChecked(False)

    def checkbox_auto_enable_state_changed(self, changed):
        ''' 设置手动模式变化事件 '''
        if changed == 2:
            self.ui.stackedWidget.setCurrentIndex(1)
        elif changed == 0:
            self.ui.stackedWidget.setCurrentIndex(0)

    def console_output(self, text):
        """ 输出日志到控制台 """
        cursor = self.ui.text_console.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.ui.text_console.setTextCursor(cursor)
        self.ui.text_console.ensureCursorVisible()

    def task_is_run(self):
        ''' 判断线程是否正在运行 '''
        return self.run_thread.isRunning()

    def task_manage(self, task_info):
        ''' 任务管理 '''
        if self.task_is_run():
            self.show_message("已有任务在进行中")
            return False
        self.run_thread.func = task_info["name"]
        if "args" in task_info:
            self.run_thread.fun_args = task_info["args"]
        else:
            self.run_thread.fun_args = None
        self.run_thread.start()

    def show_message(self, text):
        ''' 显示状态栏消息 '''
        self.ui.statusbar.showMessage(text, 3000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_lightgreen.xml',
                     path=os.getcwd()+os.sep+"main.py")
    window = mainwindow()
    sys.exit(app.exec_())
