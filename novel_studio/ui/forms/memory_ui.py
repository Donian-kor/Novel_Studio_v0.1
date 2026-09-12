# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'memory.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_QWidget(object):
    def setupUi(self, MemoryView):
        if not MemoryView.objectName():
            MemoryView.setObjectName(u"MemoryView")
        MemoryView.resize(1000, 700)
        self.root = QVBoxLayout(MemoryView)
        self.root.setObjectName(u"root")
        self.pageTitle = QLabel(MemoryView)
        self.pageTitle.setObjectName(u"pageTitle")

        self.root.addWidget(self.pageTitle)

        self.memoryEdit = QPlainTextEdit(MemoryView)
        self.memoryEdit.setObjectName(u"memoryEdit")
        self.memoryEdit.setReadOnly(True)

        self.root.addWidget(self.memoryEdit)

        self.buttons = QHBoxLayout()
        self.buttons.setObjectName(u"buttons")
        self.summarizeButton = QPushButton(MemoryView)
        self.summarizeButton.setObjectName(u"summarizeButton")

        self.buttons.addWidget(self.summarizeButton)

        self.checkButton = QPushButton(MemoryView)
        self.checkButton.setObjectName(u"checkButton")

        self.buttons.addWidget(self.checkButton)


        self.root.addLayout(self.buttons)


        self.retranslateUi(MemoryView)

        QMetaObject.connectSlotsByName(MemoryView)
    # setupUi

    def retranslateUi(self, MemoryView):
        self.pageTitle.setText(QCoreApplication.translate("QWidget", u"\uae30\uc5b5 / \uc5f0\uc18d\uc131", None))
        self.summarizeButton.setText(QCoreApplication.translate("QWidget", u"AI \uae30\uc5b5 \uc0dd\uc131", None))
        self.checkButton.setText(QCoreApplication.translate("QWidget", u"AI \uc5f0\uc18d\uc131 \uac80\uc99d", None))
        pass
    # retranslateUi

