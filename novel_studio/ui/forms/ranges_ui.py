# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ranges.ui'
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
    def setupUi(self, RangesView):
        if not RangesView.objectName():
            RangesView.setObjectName(u"RangesView")
        RangesView.resize(1000, 700)
        self.root = QVBoxLayout(RangesView)
        self.root.setObjectName(u"root")
        self.pageTitle = QLabel(RangesView)
        self.pageTitle.setObjectName(u"pageTitle")

        self.root.addWidget(self.pageTitle)

        self.controls = QHBoxLayout()
        self.controls.setObjectName(u"controls")
        self.sizeLabel = QLabel(RangesView)
        self.sizeLabel.setObjectName(u"sizeLabel")

        self.controls.addWidget(self.sizeLabel)

        self.sizeSpin = QSpinBox(RangesView)
        self.sizeSpin.setObjectName(u"sizeSpin")
        self.sizeSpin.setMinimum(1)
        self.sizeSpin.setMaximum(30)
        self.sizeSpin.setValue(5)

        self.controls.addWidget(self.sizeSpin)

        self.generateButton = QPushButton(RangesView)
        self.generateButton.setObjectName(u"generateButton")

        self.controls.addWidget(self.generateButton)

        self.snapshotButton = QPushButton(RangesView)
        self.snapshotButton.setObjectName(u"snapshotButton")

        self.controls.addWidget(self.snapshotButton)


        self.root.addLayout(self.controls)

        self.content = QHBoxLayout()
        self.content.setObjectName(u"content")
        self.rangeList = QListWidget(RangesView)
        self.rangeList.setObjectName(u"rangeList")

        self.content.addWidget(self.rangeList)

        self.rangeDetail = QPlainTextEdit(RangesView)
        self.rangeDetail.setObjectName(u"rangeDetail")
        self.rangeDetail.setReadOnly(True)

        self.content.addWidget(self.rangeDetail)


        self.root.addLayout(self.content)


        self.retranslateUi(RangesView)

        QMetaObject.connectSlotsByName(RangesView)
    # setupUi

    def retranslateUi(self, RangesView):
        self.pageTitle.setText(QCoreApplication.translate("QWidget", u"\uc2a4\ud1a0\ub9ac \uad6c\uac04", None))
        self.sizeLabel.setText(QCoreApplication.translate("QWidget", u"\uad6c\uac04 \ud06c\uae30", None))
        self.generateButton.setText(QCoreApplication.translate("QWidget", u"AI \uc2a4\ud1a0\ub9ac \uad6c\uac04 \uc0dd\uc131", None))
        self.snapshotButton.setText(QCoreApplication.translate("QWidget", u"\uc120\ud0dd \uad6c\uac04 \uc0c1\ud0dc \uc800\uc7a5", None))
        pass
    # retranslateUi

