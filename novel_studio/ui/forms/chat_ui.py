# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'chat.ui'
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

class Ui_AIChatWidget(object):
    def setupUi(self, AIChatWidget):
        if not AIChatWidget.objectName():
            AIChatWidget.setObjectName(u"AIChatWidget")
        AIChatWidget.resize(436, 472)
        self.l = QVBoxLayout(AIChatWidget)
        self.l.setObjectName(u"l")
        self.contextLabel = QLabel(AIChatWidget)
        self.contextLabel.setObjectName(u"contextLabel")

        self.l.addWidget(self.contextLabel)

        self.log = QPlainTextEdit(AIChatWidget)
        self.log.setObjectName(u"log")
        self.log.setReadOnly(True)

        self.l.addWidget(self.log)

        self.input = QPlainTextEdit(AIChatWidget)
        self.input.setObjectName(u"input")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.input.sizePolicy().hasHeightForWidth())
        self.input.setSizePolicy(sizePolicy)

        self.l.addWidget(self.input)

        self.a = QHBoxLayout()
        self.a.setObjectName(u"a")
        self.searchBtn = QPushButton(AIChatWidget)
        self.searchBtn.setObjectName(u"searchBtn")

        self.a.addWidget(self.searchBtn)

        self.sendBtn = QPushButton(AIChatWidget)
        self.sendBtn.setObjectName(u"sendBtn")

        self.a.addWidget(self.sendBtn)


        self.l.addLayout(self.a)


        self.retranslateUi(AIChatWidget)

        QMetaObject.connectSlotsByName(AIChatWidget)
    # setupUi

    def retranslateUi(self, AIChatWidget):
        AIChatWidget.setWindowTitle(QCoreApplication.translate("AIChatWidget", u"AI \uc791\ud488 \ube44\uc11c", None))
        self.contextLabel.setText(QCoreApplication.translate("AIChatWidget", u"DB \uae30\ubc18 \uc791\ud488 \ube44\uc11c \u2014 \uc9c8\ubb38\ud558\uba74 \uc791\ud488 DB\ub97c \uac80\uc0c9\ud574\uc11c \ub2f5\ud569\ub2c8\ub2e4.", None))
        self.input.setPlaceholderText(QCoreApplication.translate("AIChatWidget", u"\uc608: \ud55c\uccad\uc758 \ud604\uc7ac \uacbd\uc9c0\uac00 \ubb50\uc57c? / 37\ud654 \uc694\uc57d\ud574\uc918. / 1\ud654 \uc368\uc918.", None))
        self.searchBtn.setText(QCoreApplication.translate("AIChatWidget", u"DB \uac80\uc0c9", None))
        self.sendBtn.setText(QCoreApplication.translate("AIChatWidget", u"\uc804\uc1a1( Ctrl+Enter )", None))
#if QT_CONFIG(shortcut)
        self.sendBtn.setShortcut(QCoreApplication.translate("AIChatWidget", u"Ctrl+Return", None))
#endif // QT_CONFIG(shortcut)
    # retranslateUi

