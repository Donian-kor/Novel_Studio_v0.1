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

class Ui_QWidget(object):
    def setupUi(self, ChatView):
        if not ChatView.objectName():
            ChatView.setObjectName(u"ChatView")
        ChatView.resize(1000, 700)
        self.root = QVBoxLayout(ChatView)
        self.root.setObjectName(u"root")
        self.pageTitle = QLabel(ChatView)
        self.pageTitle.setObjectName(u"pageTitle")

        self.root.addWidget(self.pageTitle)

        self.chatLog = QPlainTextEdit(ChatView)
        self.chatLog.setObjectName(u"chatLog")
        self.chatLog.setReadOnly(True)

        self.root.addWidget(self.chatLog)

        self.chatInput = QPlainTextEdit(ChatView)
        self.chatInput.setObjectName(u"chatInput")
        self.chatInput.setReadOnly(False)

        self.root.addWidget(self.chatInput)

        self.buttons = QHBoxLayout()
        self.buttons.setObjectName(u"buttons")
        self.sendButton = QPushButton(ChatView)
        self.sendButton.setObjectName(u"sendButton")

        self.buttons.addWidget(self.sendButton)

        self.clearButton = QPushButton(ChatView)
        self.clearButton.setObjectName(u"clearButton")

        self.buttons.addWidget(self.clearButton)


        self.root.addLayout(self.buttons)


        self.retranslateUi(ChatView)

        QMetaObject.connectSlotsByName(ChatView)
    # setupUi

    def retranslateUi(self, ChatView):
        self.pageTitle.setText(QCoreApplication.translate("QWidget", u"AI \ucc44\ud305", None))
        self.sendButton.setText(QCoreApplication.translate("QWidget", u"\uc804\uc1a1", None))
        self.clearButton.setText(QCoreApplication.translate("QWidget", u"\ub300\ud654 \uc9c0\uc6b0\uae30", None))
        pass
    # retranslateUi

