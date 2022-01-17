import os
import threading
from pathlib import Path
from PIL import ImageFont, ImageDraw

from PySide6 import QtGui
from PySide6.QtWidgets import QGridLayout, QMainWindow, QLabel, QDialogButtonBox
from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QImage, QPixmap

from widgets import ClickedQLabel
import utils


class CategorysChooser(QMainWindow):
    def __init__(self,parent=None):
        super(CategorysChooser, self).__init__()
        self.load_ui()

        self.img_loaded = False

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "categorys_chooser.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window = loader.load(ui_file)
        ui_file.close()
        self.setCentralWidget(self.window)
        self.setWindowTitle(self.window.windowTitle())
        self.resize(self.window.size())
        
        self.gridLayout = self.findChild(QGridLayout,'gridLayout_2')
        assert type(self.gridLayout) is QGridLayout

        ori_labels = [self.window.findChild(QLabel,'label_'+str(i))
                       for i in range(1,14+1)]
        self.labels = [ClickedQLabel(oril) for oril in ori_labels]
        for idx,(oril,l) in enumerate(zip(ori_labels,self.labels)):
            self.gridLayout.replaceWidget(oril,l)
            l.label_idx = idx
            
        self.btnbox = self.window.findChild(QDialogButtonBox,'buttonBox')

    def load_img(self,idx,text=None):
        img = utils.getImageFromUrl(self.categorys[idx]['cover'])
        if text is not None:
            draw = ImageDraw.Draw(img)
            setFont = ImageFont.truetype('source/令东齐伋体(QIJIFALLBACK).ttf',200)
            draw.text((40,40),text,font=setFont,fill='#000000',direction=None)
        img = QImage(img.tobytes(),img.size[0],img.size[1],QImage.Format_RGB888)
        # img = QPixmap(img).scaled(self.labels[0].size(),Qt.AspectRatioMode.KeepAspectRatio)
        img = QPixmap(img).scaledToHeight(180)
        self.labels[idx].setPixmap(img)

    def load_data(self):
        self.categorys = utils.getCategorys()
        imgload_th = [threading.Thread(target=self.load_img,args=(i,self.categorys[i]['rname'])) for i in range(len(self.categorys))]
        for idx in range(len(self.categorys)):
            imgload_th[idx].start()

    def showEvent(self, event: QtGui.QShowEvent):
        if not self.img_loaded:
            self.load_data()
            self.img_loaded = True
        return super().showEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent):
        if not self.isHidden():
            event.ignore()
            self.hide()
        else:
            event.accept()
