# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plots.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpinBox, QVBoxLayout, QWidget)

class Ui_PlotsPage(object):
    def setupUi(self, PlotsPage):
        if not PlotsPage.objectName():
            PlotsPage.setObjectName(u"PlotsPage")
        self.l = QVBoxLayout(PlotsPage)
        self.l.setObjectName(u"l")
        self.top = QHBoxLayout()
        self.top.setObjectName(u"top")
        self.start = QSpinBox(PlotsPage)
        self.start.setObjectName(u"start")
        self.start.setValue(1)

        self.top.addWidget(self.start)

        self.dash = QLabel(PlotsPage)
        self.dash.setObjectName(u"dash")

        self.top.addWidget(self.dash)

        self.end = QSpinBox(PlotsPage)
        self.end.setObjectName(u"end")
        self.end.setValue(5)

        self.top.addWidget(self.end)

        self.generateBtn = QPushButton(PlotsPage)
        self.generateBtn.setObjectName(u"generateBtn")

        self.top.addWidget(self.generateBtn)

        self.allBtn = QPushButton(PlotsPage)
        self.allBtn.setObjectName(u"allBtn")

        self.top.addWidget(self.allBtn)

        self.improveBtn = QPushButton(PlotsPage)
        self.improveBtn.setObjectName(u"improveBtn")

        self.top.addWidget(self.improveBtn)


        self.l.addLayout(self.top)

        self.body = QHBoxLayout()
        self.body.setObjectName(u"body")
        self.list = QListWidget(PlotsPage)
        self.list.setObjectName(u"list")

        self.body.addWidget(self.list)

        self.detail = QPlainTextEdit(PlotsPage)
        self.detail.setObjectName(u"detail")

        self.body.addWidget(self.detail)


        self.l.addLayout(self.body)


        self.retranslateUi(PlotsPage)

        QMetaObject.connectSlotsByName(PlotsPage)
    # setupUi

    def retranslateUi(self, PlotsPage):
        self.dash.setText(QCoreApplication.translate("PlotsPage", u"~", None))
        self.generateBtn.setText(QCoreApplication.translate("PlotsPage", u"AI \ud654\ubcc4 \ud50c\ub86f \uc0dd\uc131", None))
        self.allBtn.setText(QCoreApplication.translate("PlotsPage", u"AI \uc804\uccb4 \ud654\ubcc4 \ud50c\ub86f \uc0dd\uc131", None))
        self.improveBtn.setText(QCoreApplication.translate("PlotsPage", u"AI \uc120\ud0dd \ud50c\ub86f \uac1c\uc120", None))
        pass
    # retranslateUi

