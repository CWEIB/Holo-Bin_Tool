from PyQt5.QtCore import QThread , pyqtSignal
import time, os
from convertor.core import Convertor

class WorkImage(QThread):
    
    finishSignal = pyqtSignal(int)

    def __init__(self ,data1, m ,parent = None):

        super(WorkImage, self).__init__(parent)

        self.image_path = data1
        self.m = m

    def run(self):
        try:
            for i in self.image_path:
                print("正在转换图片{} ...".format(os.path.basename(i)))
                c = Convertor(i, img_path = self.m)
                c.get_bin_file()
                self.finishSignal.emit(1)
        except:
            print('---image ERROR---')
            self.finishSignal.emit(2)
        return

