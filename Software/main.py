from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, QCoreApplication, QEventLoop
from Ui_Holo_Bin import Ui_MainWindow
import sys, os, time, os.path
import serial
import serial.tools.list_ports
from image_rc import *
from convertor.core import Convertor
import esptool
from updata import WorkThraed
from imagebin import WorkImage

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        
        # 设置应用程序的窗口图标
        self.setWindowIcon(QIcon(":/image/image/Holo logo.png"))
        
            
        #串口无效
        self.ser = None
        self.send_num = 0
        self.receive_num = 0

        #记录最后发送的回车字符的变量
        self.rcv_enter = ''
        
        #判断路径是否为空
        self.pach_ok = 0

        #判断拖入的路径是否包含别的文件
        self.judgment = 0

        #显示发送与接收的字符数量
        self.label_3.setText(str(self.send_num))
        self.label_11.setText(str(self.receive_num))

        #刷新一下串口的列表
        self.refresh()
        
        #波特率
        self.comboBox_2.addItem('115200')
        self.comboBox_2.addItem('57600')
        self.comboBox_2.addItem('56000')
        self.comboBox_2.addItem('38400')
        self.comboBox_2.addItem('19200')
        self.comboBox_2.addItem('14400')
        self.comboBox_2.addItem('9600')
        self.comboBox_2.addItem('4800')
        self.comboBox_2.addItem('2400')
        self.comboBox_2.addItem('1200')

        #数据位
        self.comboBox_3.addItem('8')
        self.comboBox_3.addItem('7')
        self.comboBox_3.addItem('6')
        self.comboBox_3.addItem('5')

        #停止位
        self.comboBox_4.addItem('1')
        self.comboBox_4.addItem('1.5')
        self.comboBox_4.addItem('2')

        #校验位
        self.comboBox_5.addItem('NONE')
        self.comboBox_5.addItem('ODD')
        self.comboBox_5.addItem('EVEN')

        #对testEdit进行事件过滤
        self.textEdit.installEventFilter(self)

        #实例化一个定时器
        self.timer = QTimer(self)

        self.timer_send= QTimer(self)
        #定时器调用读取串口接收数据
        self.timer.timeout.connect(self.recv)

        #定时发送
        self.timer_send.timeout.connect(self.send)
        
        #发送数据按钮
        self.pushButton.clicked.connect(self.send)

        #打开关闭串口按钮
        self.pushButton_2.clicked.connect(self.open_close)

        #刷新串口外设按钮
        self.pushButton_4.clicked.connect(self.refresh)

        #清除窗口
        self.pushButton_3.clicked.connect(self.clear)

        #定时发送
        self.checkBox_4.clicked.connect(self.send_timer_box)

        #波特率修改
        self.comboBox_2.activated.connect(self.baud_modify)

        #串口号修改
        self.comboBox.activated.connect(self.com_modify)

        #img转bin路径选择
        self.pushButton1.clicked.connect(self.img_path)

        #固件路径选择
        self.pushButton_9.clicked.connect(self.bin_path)
        
        #检测拖进的img路径
        self.textEdit_2.textChanged.connect(self.editchange)
        
        #检测保存的img路径是否被选择
        self.pushButton_8.clicked.connect(self.flash_bin)

        
        #执行一下打开串口
        if len(self.comboBox.currentText()) > 1:
            self.open_close(True)
            self.pushButton_2.setChecked(True)

        self.sercolse = 1
        

    #img转bin保存路径
    def img_path(self):
        self.m = QtWidgets.QFileDialog.getExistingDirectory(None, "选择文件夹", "")
        if len(self.m) == 0:
            self.pach_ok = 0
        else:
            self.lineEdit6.setText(self.m)
            self.pach_ok = 1


    #固件路径选择
    def bin_path(self):
        s = QtWidgets.QFileDialog.getOpenFileName(None,  "选取文件","./", "Bin Files (*.bin)")   #All Files (*);;
        self.lineEdit_5.setText(str(s[0]))

    #拖入的img路径检测
    def editchange(self):
        if len(self.textEdit_2.toPlainText()) > 1:
            if self.pach_ok == 1:
                data = self.textEdit_2.toPlainText()
                data = data.replace('\r','').replace('\n','|').replace('\t','').replace('file:///','')
                self.data1 = data.split('|')
                if len(self.data1) > 1:
                    self.data1.remove('')
                # if :
                #     self.data1.remove('')
                for ch in self.data1:
                    ext = ['.jpg', '.png', '.bmp']
                    if ch.endswith (tuple(ext)):
                        self.judgment = 1
                    else:
                        self.judgment = 0
                        QtWidgets.QMessageBox.warning(self,'文件格式错误', '请拖入JPG/PGN/BMP格式文件', QtWidgets.QMessageBox.Ok)
                        self.textEdit_2.clear()
                        break
                if self.judgment == 1:
                    # img-bin转换中
                    if len(self.textEdit_2.toPlainText()) > 1:
                        self.label_12.setText('图片转换中....')
                        self.xianchen1()


            elif self.pach_ok == 0:
                QtWidgets.QMessageBox.warning(self,'警告', '保存的路径为空', QtWidgets.QMessageBox.Ok)
                self.textEdit_2.clear()



    #刷新一下串口
    def refresh(self):
        #查询可用的串口
        self.comboBox.clear()
        plist=list(serial.tools.list_ports.comports())

        if len(plist) <= 0:
            print("No used com!")
            #self.statusBar.showMessage('没有可用的串口')
            

        else:
            #把所有的可用的串口输出到comboBox中去
            self.comboBox.clear()
            
            for i in range(0, len(plist)):
                plist_0 = list(plist[i])
                self.comboBox.addItem(str(plist_0[0]))

       
    #事件过滤
    def eventFilter(self, obj, event):
        #处理textEdit的键盘按下事件
        if event.type() == event.KeyPress:
            
            if self.ser != None:
                if event.key() == QtCore.Qt.Key_Up:
                    
                    #up 0x1b5b41 向上箭头
                    send_list = []
                    send_list.append(0x1b)
                    send_list.append(0x5b)
                    send_list.append(0x41)
                    input_s = bytes(send_list)

                    num = self.ser.write(input_s)
                elif event.key() == QtCore.Qt.Key_Down:
                    #down 0x1b5b42 向下箭头
                    send_list = []
                    send_list.append(0x1b)
                    send_list.append(0x5b)
                    send_list.append(0x42)
                    input_s = bytes(send_list)

                    num = self.ser.write(input_s)
                else:    
                    #获取按键对应的字符
                    char = event.text()
                    num = self.ser.write(char.encode('utf-8'))
                self.send_num = self.send_num + num
                self.label_3.setText(str(self.send_num))
                self.label_11.setText(str(self.receive_num))
            else:
                pass
            return True
        else:
            
            return False
        
        
    #重载窗口关闭事件
    def closeEvent(self,e):

        #关闭定时器，停止读取接收数据
        self.timer_send.stop()
        self.timer.stop()

        #关闭串口
        if self.ser != None:
            self.ser.close()
            self.sercolse = 1

    #定时发送数据
    def send_timer_box(self):
        if self.checkBox_4.checkState():
            time = self.lineEdit_2.text()

            try:
                time_val = int(time, 10)
            except ValueError:
                QMessageBox.critical(self, 'HoloTool','请输入有效的定时时间!')
                return None

            if time_val == 0:
                QMessageBox.critical(self, 'HoloTool','定时时间必须大于零!')
                return None
            #定时间隔发送
            self.timer_send.start(time_val)
            
        else:
            self.timer_send.stop()
            

    #清除窗口操作
    def clear(self):
        self.textEdit.clear()
        self.send_num = 0
        self.receive_num = 0
        self.label_3.setText(str(self.send_num))
        self.label_11.setText(str(self.receive_num))
        

    #串口接收数据处理
    def recv(self):
        
        try:
            num = self.ser.inWaiting()
        except:

            self.timer_send.stop()
            self.timer.stop()
            #串口拔出错误，关闭定时器
            self.ser.close()
            self.sercolse = 1
            self.ser = None

            
            #设置为打开按钮状态
            self.pushButton_2.setChecked(False)
            self.pushButton_2.setText("打开串口")
            print('serial error!')
            return None
        if(num > 0):
            #有时间会出现少读到一个字符的情况，还得进行读取第二次，所以多读一个
            data = self.ser.read(num)
            
            #调试打印输出数据
            num = len(data)
            #十六进制显示
            if self.checkBox_3.checkState():
                out_s=''
                for i in range(0, len(data)):
                    out_s = out_s + '{:02X}'.format(data[i]) + ' '
                
                
                  
            else:    	
                #串口接收到的字符串为b'123',要转化成unicode字符串才能输出到窗口中去
                out_s = data.decode('iso-8859-1')
                
                if self.rcv_enter == '\r':
                    #上次有回车未显示，与本次一起显示
                    out_s = '\r' + out_s
                    self.rcv_enter =''
                
                if out_s[-1] == '\r':
                    #如果末尾有回车，留下与下次可能出现的换行一起显示，解决textEdit控件分开2次输入回车与换行出现2次换行的问题
                    out_s = out_s[0:-1]
                    self.rcv_enter = '\r'
                    
            #先把光标移到到最后
            cursor = self.textEdit.textCursor()
            if(cursor != cursor.End):
                cursor.movePosition(cursor.End)
                self.textEdit.setTextCursor(cursor)
            
            #把字符串显示到窗口中去    
            self.textEdit.insertPlainText(out_s)
                
            
            #统计接收字符的数量
            self.receive_num = self.receive_num + num
            self.label_3.setText(str(self.send_num))
            self.label_11.setText(str(self.receive_num))
            if self.receive_num > 20000:
                self.textEdit.clear()
                self.send_num = 0
                self.receive_num = 0
                self.label_3.setText(str(self.send_num))
                self.label_11.setText(str(self.receive_num))    
            
            #获取到text光标
            textCursor = self.textEdit.textCursor()
            #滚动到底部
            textCursor.movePosition(textCursor.End)
            #设置光标到text中去
            self.textEdit.setTextCursor(textCursor)
        else:
            #此时回车后面没有收到换行，就把回车发出去
            if self.rcv_enter == '\r':
                #先把光标移到到最后
                cursor = self.textEdit.textCursor()
                if(cursor != cursor.End):
                    cursor.movePosition(cursor.End)
                    self.textEdit.setTextCursor(cursor)
                self.textEdit.insertPlainText('\r')
                self.rcv_enter =''
               
        
    #串口发送数据处理
    def send(self):
        if self.ser != None:
            input_s = self.lineEdit.text()
            if input_s != "":

                #发送字符
                if (self.checkBox.checkState() == False):
                    if self.checkBox_2.checkState():
                        #发送新行
                        input_s = input_s + '\r\n'
                    input_s = input_s.encode('utf-8')    
                    
                else:
                    #发送十六进制数据
                    input_s = input_s.strip() #删除前后的空格
                    send_list=[]
                    while input_s != '':
                        try:
                            num = int(input_s[0:2], 16)
                            
                        except ValueError:
                            print('input hex data!')
                            QMessageBox.critical(self, 'HoloTool','请输入十六进制数据，以空格分开!')
                            return None
                        
                        input_s = input_s[2:]
                        input_s = input_s.strip()
                        
                        #添加到发送列表中
                        send_list.append(num)
                    input_s = bytes(send_list)
                print(input_s)
                #发送数据    
                try:
                    num = self.ser.write(input_s)
                except:

                    self.timer_send.stop()
                    self.timer.stop()
                    #串口拔出错误，关闭定时器
                    self.ser.close()
                    self.sercolse = 1
                    self.ser = None

                    
                    #设置为打开按钮状态
                    self.pushButton_2.setChecked(False)
                    self.pushButton_2.setText("打开串口")
                    print('serial error send!')
                    return None
                    
                
                
                self.send_num = self.send_num + num
                self.label_3.setText(str(self.send_num))
                self.label_11.setText(str(self.receive_num))
            else:
                print('none data input!')
            
        else:
            #停止发送定时器
            self.timer_send.stop()
            QMessageBox.critical(self, 'HoloTool','请打开串口')

    #波特率修改
    def baud_modify(self):
        if self.ser != None:
            self.ser.baudrate = int(self.comboBox_2.currentText())
            
    #串口号修改
    def com_modify(self):
        if self.ser != None:
            self.ser.port = self.comboBox.currentText()
        
    #打开关闭串口        
    def open_close(self, btn_sta):
        
        self.btn_sta = btn_sta
        if len(self.comboBox.currentText()) > 1:
            if self.btn_sta == True:
                try:
                    #输入参数'COM13',115200
                    self.ser = serial.Serial(self.comboBox.currentText(), int(self.comboBox_2.currentText()), timeout=0.2)
                except:
                    return None
                #字符间隔超时时间设置
                self.ser.interCharTimeout = 0.001    
                #1ms的测试周期
                self.timer.start(2)
                self.pushButton_2.setText("关闭串口")
                print('open')
            else:
                #关闭定时器，停止读取接收数据
                self.timer_send.stop()
                self.timer.stop()
                
                try:
                    #关闭串口
                    self.ser.close()
                    self.sercolse = 1
                except:
                    QMessageBox.critical(self, 'HoloTool','关闭串口失败')
                    return None
                    
                self.ser = None
                
                self.pushButton_2.setText("打开串口")
                print('close!')
        else:
            QtWidgets.QMessageBox.warning(self,'警告', '没有可用的串口!', QtWidgets.QMessageBox.Ok)
            self.btn_sta == True
    


    #bin固件烧写
    def flash_bin(self):
        
        self.com = self.comboBox.currentText()
        self.firmware = self.lineEdit_5.text()
        if len(self.firmware) == 0:
            print("--s--")
            QtWidgets.QMessageBox.warning(self,'文件路径错误', '请选择Bin固件路径', QtWidgets.QMessageBox.Ok)
            
        else:
            self.timer_send.stop()
            self.timer.stop()
            if self.sercolse == 1:
                pass
            else:
                self.ser.close()
            self.ser = None
            self.pushButton_2.setText("打开串口")

            self.textEdit.setText("正在上传固件......")

            #上传时设置按钮禁用状态
            self.pushButton.setEnabled(False)
            self.pushButton_2.setEnabled(False)
            self.pushButton_3.setEnabled(False)
            self.pushButton_4.setEnabled(False)
            self.pushButton_8.setEnabled(False)
            self.pushButton_9.setEnabled(False)
            self.comboBox.setEnabled(False)
            self.comboBox_2.setEnabled(False)
            self.comboBox_3.setEnabled(False)
            self.comboBox_4.setEnabled(False)
            self.comboBox_5.setEnabled(False)
            self.checkBox.setEnabled(False)
            self.checkBox_2.setEnabled(False)
            self.checkBox_3.setEnabled(False)
            self.checkBox_4.setEnabled(False)
            self.lineEdit.setEnabled(False)
            self.lineEdit_2.setEnabled(False)
            self.label_8.setEnabled(False)
            
            self.xianchen()


    
    def close_com (self,msg):
        if msg == 1:
            self.textEdit.setText("固件上传成功")
            self.btn_sta == True
        else:
            self.textEdit.setText("固件上传失败")
            self.btn_sta == True
            QtWidgets.QMessageBox.warning(self,'警告', '固件上传失败！', QtWidgets.QMessageBox.Ok)
        #上传时设置按钮禁用状态
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(True)
        self.pushButton_3.setEnabled(True)
        self.pushButton_4.setEnabled(True)
        self.pushButton_8.setEnabled(True)
        self.pushButton_9.setEnabled(True)
        self.comboBox.setEnabled(True)
        self.comboBox_2.setEnabled(True)
        self.comboBox_3.setEnabled(True)
        self.comboBox_4.setEnabled(True)
        self.comboBox_5.setEnabled(True)
        self.checkBox.setEnabled(True)
        self.checkBox_2.setEnabled(True)
        self.checkBox_3.setEnabled(True)
        self.checkBox_4.setEnabled(True)
        self.lineEdit.setEnabled(True)
        self.lineEdit_2.setEnabled(True)
        self.label_8.setEnabled(True)

        self.open_close(True)
        self.pushButton_2.setChecked(True)

    def image_ok (self,msg):
        if msg == 1:
            self.label_12.setText('图片转换成功！')
            folder = self.m
            os.startfile(folder)
            self.textEdit_2.clear()
        else:
            self.label_12.setText('图片转换失败！')
            QtWidgets.QMessageBox.warning(self,'警告', '图片文件太大转换失败！', QtWidgets.QMessageBox.Ok)
            self.textEdit_2.clear()


    def xianchen (self):
        #线程通信
        self.th = WorkThraed(self.com,self.firmware)
        self.th.finishSignal.connect(self.close_com)
        self.th.start()

    def xianchen1 (self):
        #线程通信
        self.th1 = WorkImage(self.data1,self.m)
        self.th1.finishSignal.connect(self.image_ok)
        self.th1.start()
        




if __name__ == "__main__":
    QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
