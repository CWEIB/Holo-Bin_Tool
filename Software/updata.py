from PyQt5.QtCore import QThread , pyqtSignal
import time
import esptool

class WorkThraed(QThread):
    
    finishSignal = pyqtSignal(int)

    def __init__(self ,com, firmware, parent = None):

        super(WorkThraed, self).__init__(parent)

        self.com = com
        self.firmware = firmware

    def run(self):
        try:
            command = ['--port' , self.com , 'write_flash' , '0x00010000', self.firmware]
            print('Using command %s' % ' '.join(command))
            esptool.main(command)
            self.finishSignal.emit(1)
        except:
            print('---ESPTOOL ERROR---')
            self.finishSignal.emit(2)
        return

