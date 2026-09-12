# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'manuscript.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QVBoxLayout, QWidget)

class Ui_QWidget(object):
    def setupUi(self, ManuscriptView):
        if not ManuscriptView.objectName():
            ManuscriptView.setObjectName(u"ManuscriptView")
        ManuscriptView.resize(1000, 700)
        self.root = QVBoxLayout(ManuscriptView)
        self.root.setObjectName(u"root")
        self.top = QHBoxLayout()
        self.top.setObjectName(u"top")
        self.chapterLabel = QLabel(ManuscriptView)
        self.chapterLabel.setObjectName(u"chapterLabel")

        self.top.addWidget(self.chapterLabel)

        self.chapterSpin = QSpinBox(ManuscriptView)
        self.chapterSpin.setObjectName(u"chapterSpin")
        self.chapterSpin.setMinimum(1)
        self.chapterSpin.setMaximum(9999)

        self.top.addWidget(self.chapterSpin)

        self.titleEdit = QLineEdit(ManuscriptView)
        self.titleEdit.setObjectName(u"titleEdit")

        self.top.addWidget(self.titleEdit)

        self.chatButton = QPushButton(ManuscriptView)
        self.chatButton.setObjectName(u"chatButton")

        self.top.addWidget(self.chatButton)


        self.root.addLayout(self.top)

        self.editor = QPlainTextEdit(ManuscriptView)
        self.editor.setObjectName(u"editor")
        self.editor.setReadOnly(False)

        self.root.addWidget(self.editor)

        self.bottom = QHBoxLayout()
        self.bottom.setObjectName(u"bottom")
        self.countLabel = QLabel(ManuscriptView)
        self.countLabel.setObjectName(u"countLabel")

        self.bottom.addWidget(self.countLabel)

        self.s = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.bottom.addItem(self.s)

        self.saveButton = QPushButton(ManuscriptView)
        self.saveButton.setObjectName(u"saveButton")

        self.bottom.addWidget(self.saveButton)

        self.writeButton = QPushButton(ManuscriptView)
        self.writeButton.setObjectName(u"writeButton")

        self.bottom.addWidget(self.writeButton)

        self.reviseButton = QPushButton(ManuscriptView)
        self.reviseButton.setObjectName(u"reviseButton")

        self.bottom.addWidget(self.reviseButton)

        self.checkButton = QPushButton(ManuscriptView)
        self.checkButton.setObjectName(u"checkButton")

        self.bottom.addWidget(self.checkButton)


        self.root.addLayout(self.bottom)


        self.retranslateUi(ManuscriptView)

        QMetaObject.connectSlotsByName(ManuscriptView)
    # setupUi

    def retranslateUi(self, ManuscriptView):
        self.chapterLabel.setText(QCoreApplication.translate("QWidget", u"\ud654", None))
        self.chatButton.setText(QCoreApplication.translate("QWidget", u"AI \ucc44\ud305", None))
        self.countLabel.setText(QCoreApplication.translate("QWidget", u"0\uc790", None))
        self.saveButton.setText(QCoreApplication.translate("QWidget", u"\uc800\uc7a5", None))
        self.writeButton.setText(QCoreApplication.translate("QWidget", u"AI \uc9d1\ud544", None))
        self.reviseButton.setText(QCoreApplication.translate("QWidget", u"AI \uc724\ubb38", None))
        self.checkButton.setText(QCoreApplication.translate("QWidget", u"AI \uac80\uc99d", None))
        pass
    # retranslateUi

