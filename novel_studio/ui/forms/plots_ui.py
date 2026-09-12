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

class Ui_QWidget(object):
    def setupUi(self, PlotsView):
        if not PlotsView.objectName():
            PlotsView.setObjectName(u"PlotsView")
        PlotsView.resize(1000, 700)
        self.root = QVBoxLayout(PlotsView)
        self.root.setObjectName(u"root")
        self.pageTitle = QLabel(PlotsView)
        self.pageTitle.setObjectName(u"pageTitle")

        self.root.addWidget(self.pageTitle)

        self.controls = QHBoxLayout()
        self.controls.setObjectName(u"controls")
        self.startLabel = QLabel(PlotsView)
        self.startLabel.setObjectName(u"startLabel")

        self.controls.addWidget(self.startLabel)

        self.startSpin = QSpinBox(PlotsView)
        self.startSpin.setObjectName(u"startSpin")
        self.startSpin.setMinimum(1)
        self.startSpin.setMaximum(9999)
        self.startSpin.setValue(1)

        self.controls.addWidget(self.startSpin)

        self.endLabel = QLabel(PlotsView)
        self.endLabel.setObjectName(u"endLabel")

        self.controls.addWidget(self.endLabel)

        self.endSpin = QSpinBox(PlotsView)
        self.endSpin.setObjectName(u"endSpin")
        self.endSpin.setMinimum(1)
        self.endSpin.setMaximum(9999)
        self.endSpin.setValue(5)

        self.controls.addWidget(self.endSpin)

        self.generateButton = QPushButton(PlotsView)
        self.generateButton.setObjectName(u"generateButton")

        self.controls.addWidget(self.generateButton)

        self.improveButton = QPushButton(PlotsView)
        self.improveButton.setObjectName(u"improveButton")

        self.controls.addWidget(self.improveButton)


        self.root.addLayout(self.controls)

        self.content = QHBoxLayout()
        self.content.setObjectName(u"content")
        self.plotList = QListWidget(PlotsView)
        self.plotList.setObjectName(u"plotList")

        self.content.addWidget(self.plotList)

        self.plotDetail = QPlainTextEdit(PlotsView)
        self.plotDetail.setObjectName(u"plotDetail")
        self.plotDetail.setReadOnly(True)

        self.content.addWidget(self.plotDetail)


        self.root.addLayout(self.content)


        self.retranslateUi(PlotsView)

        QMetaObject.connectSlotsByName(PlotsView)
    # setupUi

    def retranslateUi(self, PlotsView):
        self.pageTitle.setText(QCoreApplication.translate("QWidget", u"\ud654\ubcc4 \uac1c\ubcc4 \ud50c\ub86f", None))
        self.startLabel.setText(QCoreApplication.translate("QWidget", u"\uc2dc\uc791", None))
        self.endLabel.setText(QCoreApplication.translate("QWidget", u"\ub05d", None))
        self.generateButton.setText(QCoreApplication.translate("QWidget", u"AI \ud654\ubcc4 \ud50c\ub86f \uc0dd\uc131", None))
        self.improveButton.setText(QCoreApplication.translate("QWidget", u"AI \ud50c\ub86f \uac1c\uc120", None))
        pass
    # retranslateUi

