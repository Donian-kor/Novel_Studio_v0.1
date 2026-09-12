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
    QVBoxLayout, QWidget)

class Ui_RangesPage(object):
    def setupUi(self, RangesPage):
        if not RangesPage.objectName():
            RangesPage.setObjectName(u"RangesPage")
        self.l = QVBoxLayout(RangesPage)
        self.l.setObjectName(u"l")
        self.hint = QLabel(RangesPage)
        self.hint.setObjectName(u"hint")

        self.l.addWidget(self.hint)

        self.list = QListWidget(RangesPage)
        self.list.setObjectName(u"list")

        self.l.addWidget(self.list)

        self.a = QHBoxLayout()
        self.a.setObjectName(u"a")
        self.generateBtn = QPushButton(RangesPage)
        self.generateBtn.setObjectName(u"generateBtn")

        self.a.addWidget(self.generateBtn)

        self.snapshotBtn = QPushButton(RangesPage)
        self.snapshotBtn.setObjectName(u"snapshotBtn")

        self.a.addWidget(self.snapshotBtn)


        self.l.addLayout(self.a)

        self.detail = QPlainTextEdit(RangesPage)
        self.detail.setObjectName(u"detail")

        self.l.addWidget(self.detail)


        self.retranslateUi(RangesPage)

        QMetaObject.connectSlotsByName(RangesPage)
    # setupUi

    def retranslateUi(self, RangesPage):
        self.hint.setText(QCoreApplication.translate("RangesPage", u"\uc2a4\ud1a0\ub9ac \uad6c\uac04: \uae34 \uc7a5\ud3b8 \ud50c\ub86f\uc744 \uc791\uc740 \uc791\uc5c5 \uad6c\uac04\uc73c\ub85c \ub098\ub204\uc5b4 \uc21c\uc11c\ub300\ub85c \uc0dd\uc131\ud569\ub2c8\ub2e4.", None))
        self.generateBtn.setText(QCoreApplication.translate("RangesPage", u"AI \uc804\uccb4 \uc2a4\ud1a0\ub9ac \uad6c\uac04 \uc0dd\uc131 / \uc774\uc5b4\ud558\uae30", None))
        self.snapshotBtn.setText(QCoreApplication.translate("RangesPage", u"\uc120\ud0dd \uad6c\uac04 \uae30\uc5b5 \uac31\uc2e0", None))
        pass
    # retranslateUi

