# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QPlainTextEdit,
    QPushButton, QSizePolicy, QSpacerItem, QStackedWidget,
    QVBoxLayout, QWidget)

class Ui_MainWidget(object):
    def setupUi(self, MainWidget):
        if not MainWidget.objectName():
            MainWidget.setObjectName(u"MainWidget")
        self.root = QVBoxLayout(MainWidget)
        self.root.setObjectName(u"root")
        self.top = QHBoxLayout()
        self.top.setObjectName(u"top")
        self.appTitle = QLabel(MainWidget)
        self.appTitle.setObjectName(u"appTitle")

        self.top.addWidget(self.appTitle)

        self.projectLabel = QLabel(MainWidget)
        self.projectLabel.setObjectName(u"projectLabel")

        self.top.addWidget(self.projectLabel)

        self.topSpace = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.top.addItem(self.topSpace)

        self.aiStatus = QLabel(MainWidget)
        self.aiStatus.setObjectName(u"aiStatus")

        self.top.addWidget(self.aiStatus)

        self.settingsBtn = QPushButton(MainWidget)
        self.settingsBtn.setObjectName(u"settingsBtn")

        self.top.addWidget(self.settingsBtn)

        self.stopBtn = QPushButton(MainWidget)
        self.stopBtn.setObjectName(u"stopBtn")

        self.top.addWidget(self.stopBtn)


        self.root.addLayout(self.top)

        self.body = QHBoxLayout()
        self.body.setObjectName(u"body")
        self.leftPanel = QFrame(MainWidget)
        self.leftPanel.setObjectName(u"leftPanel")
        self.leftPanel.setMinimumSize(QSize(220, 0))
        self.leftPanel.setMaximumSize(QSize(360, 16777215))
        self.leftLayout = QVBoxLayout(self.leftPanel)
        self.leftLayout.setObjectName(u"leftLayout")
        self.leftCollapse = QPushButton(self.leftPanel)
        self.leftCollapse.setObjectName(u"leftCollapse")

        self.leftLayout.addWidget(self.leftCollapse)

        self.navList = QListWidget(self.leftPanel)
        self.navList.setObjectName(u"navList")

        self.leftLayout.addWidget(self.navList)


        self.body.addWidget(self.leftPanel)

        self.leftHandle = QFrame(MainWidget)
        self.leftHandle.setObjectName(u"leftHandle")
        self.leftHandle.setMinimumSize(QSize(26, 0))
        self.leftHandle.setMaximumSize(QSize(26, 16777215))
        self.lh = QVBoxLayout(self.leftHandle)
        self.lh.setObjectName(u"lh")
        self.leftExpand = QPushButton(self.leftHandle)
        self.leftExpand.setObjectName(u"leftExpand")

        self.lh.addWidget(self.leftExpand)


        self.body.addWidget(self.leftHandle)

        self.centerPanel = QFrame(MainWidget)
        self.centerPanel.setObjectName(u"centerPanel")
        self.centerLayout = QVBoxLayout(self.centerPanel)
        self.centerLayout.setObjectName(u"centerLayout")
        self.pageStack = QStackedWidget(self.centerPanel)
        self.pageStack.setObjectName(u"pageStack")

        self.centerLayout.addWidget(self.pageStack)


        self.body.addWidget(self.centerPanel)

        self.rightHandle = QFrame(MainWidget)
        self.rightHandle.setObjectName(u"rightHandle")
        self.rightHandle.setMinimumSize(QSize(26, 0))
        self.rightHandle.setMaximumSize(QSize(26, 16777215))
        self.rh = QVBoxLayout(self.rightHandle)
        self.rh.setObjectName(u"rh")
        self.rightExpand = QPushButton(self.rightHandle)
        self.rightExpand.setObjectName(u"rightExpand")

        self.rh.addWidget(self.rightExpand)


        self.body.addWidget(self.rightHandle)

        self.rightPanel = QFrame(MainWidget)
        self.rightPanel.setObjectName(u"rightPanel")
        self.rightPanel.setMinimumSize(QSize(290, 0))
        self.rightPanel.setMaximumSize(QSize(460, 16777215))
        self.rightLayout = QVBoxLayout(self.rightPanel)
        self.rightLayout.setObjectName(u"rightLayout")
        self.rightCollapse = QPushButton(self.rightPanel)
        self.rightCollapse.setObjectName(u"rightCollapse")

        self.rightLayout.addWidget(self.rightCollapse)

        self.stateTitle = QLabel(self.rightPanel)
        self.stateTitle.setObjectName(u"stateTitle")

        self.rightLayout.addWidget(self.stateTitle)

        self.stateText = QPlainTextEdit(self.rightPanel)
        self.stateText.setObjectName(u"stateText")
        self.stateText.setReadOnly(True)

        self.rightLayout.addWidget(self.stateText)


        self.body.addWidget(self.rightPanel)


        self.root.addLayout(self.body)

        self.bottom = QHBoxLayout()
        self.bottom.setObjectName(u"bottom")
        self.countLabel = QLabel(MainWidget)
        self.countLabel.setObjectName(u"countLabel")

        self.bottom.addWidget(self.countLabel)

        self.bottomSpace = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.bottom.addItem(self.bottomSpace)

        self.autoSaveCombo = QComboBox(MainWidget)
        self.autoSaveCombo.setObjectName(u"autoSaveCombo")

        self.bottom.addWidget(self.autoSaveCombo)

        self.cleanAllBtn = QPushButton(MainWidget)
        self.cleanAllBtn.setObjectName(u"cleanAllBtn")

        self.bottom.addWidget(self.cleanAllBtn)

        self.saveAllBtn = QPushButton(MainWidget)
        self.saveAllBtn.setObjectName(u"saveAllBtn")

        self.bottom.addWidget(self.saveAllBtn)

        self.chatBtn = QPushButton(MainWidget)
        self.chatBtn.setObjectName(u"chatBtn")

        self.bottom.addWidget(self.chatBtn)


        self.root.addLayout(self.bottom)


        self.retranslateUi(MainWidget)

        QMetaObject.connectSlotsByName(MainWidget)
    # setupUi

    def retranslateUi(self, MainWidget):
        self.appTitle.setText(QCoreApplication.translate("MainWidget", u"Novel Studio", None))
        self.projectLabel.setText(QCoreApplication.translate("MainWidget", u"\uc791\ud488", None))
        self.aiStatus.setText(QCoreApplication.translate("MainWidget", u"AI \u25cf \ud655\uc778 \ud544\uc694", None))
        self.settingsBtn.setText(QCoreApplication.translate("MainWidget", u"\uc124\uc815", None))
        self.stopBtn.setText(QCoreApplication.translate("MainWidget", u"\u23f9 \uc815\uc9c0", None))
        self.leftCollapse.setText(QCoreApplication.translate("MainWidget", u"\uc67c\ucabd \uc0ac\uc774\ub4dc\ubc14 \uc811\uae30 \u25c0", None))
        self.leftExpand.setText(QCoreApplication.translate("MainWidget", u"\u25b6", None))
        self.rightExpand.setText(QCoreApplication.translate("MainWidget", u"\u25c0", None))
        self.rightCollapse.setText(QCoreApplication.translate("MainWidget", u"\uc624\ub978\ucabd \uc0ac\uc774\ub4dc\ubc14 \uc811\uae30 \u25b6", None))
        self.stateTitle.setText(QCoreApplication.translate("MainWidget", u"\ud604\uc7ac \uc791\ud488 \uc0c1\ud0dc", None))
        self.countLabel.setText(QCoreApplication.translate("MainWidget", u"\ud604\uc7ac 0\uc790 / \ubaa9\ud45c 0\uc790", None))
        self.cleanAllBtn.setText(QCoreApplication.translate("MainWidget", u"AI \uae30\ud638 \uc0ad\uc81c", None))
        self.saveAllBtn.setText(QCoreApplication.translate("MainWidget", u"\uc804\uccb4 \uc800\uc7a5", None))
        self.chatBtn.setText(QCoreApplication.translate("MainWidget", u"AI \uc791\ud488 \ube44\uc11c", None))
        pass
    # retranslateUi

