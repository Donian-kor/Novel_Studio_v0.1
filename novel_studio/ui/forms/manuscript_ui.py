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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLayout, QLineEdit, QListWidget,
    QListWidgetItem, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QSplitter, QVBoxLayout, QWidget)

class Ui_ManuscriptPage(object):
    def setupUi(self, ManuscriptPage):
        if not ManuscriptPage.objectName():
            ManuscriptPage.setObjectName(u"ManuscriptPage")
        ManuscriptPage.resize(905, 670)
        self.gridLayout = QGridLayout(ManuscriptPage)
        self.gridLayout.setObjectName(u"gridLayout")
        self.manuscriptHeader = QFrame(ManuscriptPage)
        self.manuscriptHeader.setObjectName(u"manuscriptHeader")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.manuscriptHeader.sizePolicy().hasHeightForWidth())
        self.manuscriptHeader.setSizePolicy(sizePolicy)
        self.manuscriptHeader.setFrameShape(QFrame.Shape.StyledPanel)
        self.top = QHBoxLayout(self.manuscriptHeader)
        self.top.setObjectName(u"top")
        self.titleEdit = QLineEdit(self.manuscriptHeader)
        self.titleEdit.setObjectName(u"titleEdit")

        self.top.addWidget(self.titleEdit)

        self.writeBtn = QPushButton(self.manuscriptHeader)
        self.writeBtn.setObjectName(u"writeBtn")

        self.top.addWidget(self.writeBtn)

        self.chatBtn = QPushButton(self.manuscriptHeader)
        self.chatBtn.setObjectName(u"chatBtn")

        self.top.addWidget(self.chatBtn)

        self.reviseBtn = QPushButton(self.manuscriptHeader)
        self.reviseBtn.setObjectName(u"reviseBtn")

        self.top.addWidget(self.reviseBtn)

        self.checkBtn = QPushButton(self.manuscriptHeader)
        self.checkBtn.setObjectName(u"checkBtn")

        self.top.addWidget(self.checkBtn)

        self.spellBtn = QPushButton(self.manuscriptHeader)
        self.spellBtn.setObjectName(u"spellBtn")

        self.top.addWidget(self.spellBtn)

        self.cleanBtn = QPushButton(self.manuscriptHeader)
        self.cleanBtn.setObjectName(u"cleanBtn")

        self.top.addWidget(self.cleanBtn)

        self.topSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.top.addItem(self.topSpacer)

        self.saveBtn = QPushButton(self.manuscriptHeader)
        self.saveBtn.setObjectName(u"saveBtn")

        self.top.addWidget(self.saveBtn)


        self.gridLayout.addWidget(self.manuscriptHeader, 0, 0, 1, 1)

        self.editorCard = QFrame(ManuscriptPage)
        self.editorCard.setObjectName(u"editorCard")
        self.editorCard.setFrameShape(QFrame.Shape.StyledPanel)
        self.editorLayout = QVBoxLayout(self.editorCard)
        self.editorLayout.setObjectName(u"editorLayout")
        self.editorHeader = QHBoxLayout()
        self.editorHeader.setSpacing(6)
        self.editorHeader.setObjectName(u"editorHeader")
        self.editorHeader.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.editorTitle = QLabel(self.editorCard)
        self.editorTitle.setObjectName(u"editorTitle")

        self.editorHeader.addWidget(self.editorTitle)

        self.editorSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.editorHeader.addItem(self.editorSpacer)

        self.countLabel = QLabel(self.editorCard)
        self.countLabel.setObjectName(u"countLabel")

        self.editorHeader.addWidget(self.countLabel)


        self.editorLayout.addLayout(self.editorHeader)

        self.manuscriptSplitter = QSplitter(self.editorCard)
        self.manuscriptSplitter.setObjectName(u"manuscriptSplitter")
        self.manuscriptSplitter.setOrientation(Qt.Orientation.Horizontal)
        self.manuscriptSplitter.setChildrenCollapsible(False)
        self.chapterList = QListWidget(self.manuscriptSplitter)
        self.chapterList.setObjectName(u"chapterList")
        self.manuscriptSplitter.addWidget(self.chapterList)
        self.editor = QPlainTextEdit(self.manuscriptSplitter)
        self.editor.setObjectName(u"editor")
        self.editor.setStyleSheet(u"")
        self.manuscriptSplitter.addWidget(self.editor)

        self.editorLayout.addWidget(self.manuscriptSplitter)

        self.editorLayout.setStretch(1, 2)

        self.gridLayout.addWidget(self.editorCard, 1, 0, 1, 1)


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
        self.editorTitle.setText(QCoreApplication.translate("ManuscriptPage", u"\uc6d0\uace0 \ud3b8\uc9d1\uae30", None))
        self.countLabel.setText(QCoreApplication.translate("ManuscriptPage", u"\ud604\uc7ac 0\uc790 / \ubaa9\ud45c 0\uc790", None))
        pass
    # retranslateUi

