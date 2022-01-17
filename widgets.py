from PySide6 import QtCore
from PySide6.QtGui import QMouseEvent, Qt
from PySide6.QtWidgets import QLabel, QSizePolicy


class ClickedQLabel(QLabel):
    
    leftbutton_clicked = QtCore.Signal()
    rightbutton_clicked = QtCore.Signal()
    
    def __init__(self,parent:QLabel=None):
        super(ClickedQLabel,self).__init__(parent)
        self.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)
        
    def mouseReleaseEvent(self, event:QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.leftbutton_clicked.emit()
        elif event.button() == Qt.RightButton:
            self.rightbutton_clicked.emit()
