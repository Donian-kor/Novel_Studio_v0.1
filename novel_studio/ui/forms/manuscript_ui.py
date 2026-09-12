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
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton,
    QSizePolicy, QSplitter, QVBoxLayout, QWidget)

class Ui_ManuscriptPage(object):
    def setupUi(self, ManuscriptPage):
        if not ManuscriptPage.objectName():
            ManuscriptPage.setObjectName(u"ManuscriptPage")
        ManuscriptPage.resize(905, 921)
        self.l = QVBoxLayout(ManuscriptPage)
        self.l.setObjectName(u"l")
        self.top = QHBoxLayout()
        self.top.setObjectName(u"top")
        self.titleEdit = QLineEdit(ManuscriptPage)
        self.titleEdit.setObjectName(u"titleEdit")

        self.top.addWidget(self.titleEdit)

        self.writeBtn = QPushButton(ManuscriptPage)
        self.writeBtn.setObjectName(u"writeBtn")

        self.top.addWidget(self.writeBtn)

        self.chatBtn = QPushButton(ManuscriptPage)
        self.chatBtn.setObjectName(u"chatBtn")

        self.top.addWidget(self.chatBtn)

        self.reviseBtn = QPushButton(ManuscriptPage)
        self.reviseBtn.setObjectName(u"reviseBtn")

        self.top.addWidget(self.reviseBtn)

        self.checkBtn = QPushButton(ManuscriptPage)
        self.checkBtn.setObjectName(u"checkBtn")

        self.top.addWidget(self.checkBtn)

        self.spellBtn = QPushButton(ManuscriptPage)
        self.spellBtn.setObjectName(u"spellBtn")

        self.top.addWidget(self.spellBtn)

        self.cleanBtn = QPushButton(ManuscriptPage)
        self.cleanBtn.setObjectName(u"cleanBtn")

        self.top.addWidget(self.cleanBtn)

        self.saveBtn = QPushButton(ManuscriptPage)
        self.saveBtn.setObjectName(u"saveBtn")

        self.top.addWidget(self.saveBtn)


        self.l.addLayout(self.top)

        self.manuscriptSplitter = QSplitter(ManuscriptPage)
        self.manuscriptSplitter.setObjectName(u"manuscriptSplitter")
        self.manuscriptSplitter.setOrientation(Qt.Orientation.Horizontal)
        self.chapterList = QListWidget(self.manuscriptSplitter)
        self.chapterList.setObjectName(u"chapterList")
        self.manuscriptSplitter.addWidget(self.chapterList)
        self.editor = QPlainTextEdit(self.manuscriptSplitter)
        self.editor.setObjectName(u"editor")
        self.editor.setStyleSheet(u"")
        self.manuscriptSplitter.addWidget(self.editor)

        self.l.addWidget(self.manuscriptSplitter)

        self.countLabel = QLabel(ManuscriptPage)
        self.countLabel.setObjectName(u"countLabel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.countLabel.sizePolicy().hasHeightForWidth())
        self.countLabel.setSizePolicy(sizePolicy)

        self.l.addWidget(self.countLabel)


        self.retranslateUi(ManuscriptPage)

        QMetaObject.connectSlotsByName(ManuscriptPage)
    # setupUi

    def retranslateUi(self, ManuscriptPage):
        self.titleEdit.setPlaceholderText(QCoreApplication.translate("ManuscriptPage", u"\ud654 \uc81c\ubaa9", None))
        self.writeBtn.setText(QCoreApplication.translate("ManuscriptPage", u"AI \uc9d1\ud544", None))
        self.chatBtn.setText(QCoreApplication.translate("ManuscriptPage", u"AI \uc791\ud488 \ube44\uc11c", None))
        self.reviseBtn.setText(QCoreApplication.translate("ManuscriptPage", u"AI \ubb38\uc7a5 \ub2e4\ub4ec\uae30", None))
        self.checkBtn.setText(QCoreApplication.translate("ManuscriptPage", u"\uc124\uc815 \ucda9\ub3cc \uac80\uc0ac", None))
        self.spellBtn.setText(QCoreApplication.translate("ManuscriptPage", u"\ub9de\ucda4\ubc95 \uac80\uc0ac", None))
        self.cleanBtn.setText(QCoreApplication.translate("ManuscriptPage", u"AI \uae30\ud638 \uc0ad\uc81c", None))
        self.saveBtn.setText(QCoreApplication.translate("ManuscriptPage", u"\uc800\uc7a5", None))
        self.countLabel.setText(QCoreApplication.translate("ManuscriptPage", u"\ud604\uc7ac 0\uc790 / \ubaa9\ud45c 0\uc790", None))
        pass
    # retranslateUi

