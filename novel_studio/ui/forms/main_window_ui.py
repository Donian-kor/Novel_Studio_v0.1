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
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QMenu, QMenuBar, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QStackedWidget, QStatusBar,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1600, 980)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName(u"actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionBackup = QAction(MainWindow)
        self.actionBackup.setObjectName(u"actionBackup")
        self.actionAISettings = QAction(MainWindow)
        self.actionAISettings.setObjectName(u"actionAISettings")
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        self.root = QVBoxLayout(self.centralWidget)
        self.root.setObjectName(u"root")
        self.top = QHBoxLayout()
        self.top.setObjectName(u"top")
        self.appLabel = QLabel(self.centralWidget)
        self.appLabel.setObjectName(u"appLabel")

        self.top.addWidget(self.appLabel)

        self.projectLabel = QLabel(self.centralWidget)
        self.projectLabel.setObjectName(u"projectLabel")

        self.top.addWidget(self.projectLabel)

        self.topSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.top.addItem(self.topSpacer)

        self.aiStatusLabel = QLabel(self.centralWidget)
        self.aiStatusLabel.setObjectName(u"aiStatusLabel")

        self.top.addWidget(self.aiStatusLabel)

        self.aiSettingsButton = QPushButton(self.centralWidget)
        self.aiSettingsButton.setObjectName(u"aiSettingsButton")

        self.top.addWidget(self.aiSettingsButton)


        self.root.addLayout(self.top)

        self.body = QHBoxLayout()
        self.body.setObjectName(u"body")
        self.leftPanel = QFrame(self.centralWidget)
        self.leftPanel.setObjectName(u"leftPanel")
        self.leftPanel.setMinimumSize(QSize(220, 0))
        self.leftPanel.setMaximumSize(QSize(380, 16777215))
        self.leftLayout = QVBoxLayout(self.leftPanel)
        self.leftLayout.setObjectName(u"leftLayout")
        self.leftCollapseButton = QPushButton(self.leftPanel)
        self.leftCollapseButton.setObjectName(u"leftCollapseButton")

        self.leftLayout.addWidget(self.leftCollapseButton)

        self.navigationList = QListWidget(self.leftPanel)
        self.navigationList.setObjectName(u"navigationList")

        self.leftLayout.addWidget(self.navigationList)


        self.body.addWidget(self.leftPanel)

        self.leftHandle = QFrame(self.centralWidget)
        self.leftHandle.setObjectName(u"leftHandle")
        self.leftHandle.setMinimumSize(QSize(28, 0))
        self.leftHandle.setMaximumSize(QSize(28, 16777215))
        self.leftHandleLayout = QVBoxLayout(self.leftHandle)
        self.leftHandleLayout.setObjectName(u"leftHandleLayout")
        self.leftExpandButton = QPushButton(self.leftHandle)
        self.leftExpandButton.setObjectName(u"leftExpandButton")

        self.leftHandleLayout.addWidget(self.leftExpandButton)

        self.leftHandleSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.leftHandleLayout.addItem(self.leftHandleSpacer)


        self.body.addWidget(self.leftHandle)

        self.centerPanel = QFrame(self.centralWidget)
        self.centerPanel.setObjectName(u"centerPanel")
        self.centerLayout = QVBoxLayout(self.centerPanel)
        self.centerLayout.setObjectName(u"centerLayout")
        self.pageStack = QStackedWidget(self.centerPanel)
        self.pageStack.setObjectName(u"pageStack")

        self.centerLayout.addWidget(self.pageStack)


        self.body.addWidget(self.centerPanel)

        self.rightHandle = QFrame(self.centralWidget)
        self.rightHandle.setObjectName(u"rightHandle")
        self.rightHandle.setMinimumSize(QSize(28, 0))
        self.rightHandle.setMaximumSize(QSize(28, 16777215))
        self.rightHandleLayout = QVBoxLayout(self.rightHandle)
        self.rightHandleLayout.setObjectName(u"rightHandleLayout")
        self.rightExpandButton = QPushButton(self.rightHandle)
        self.rightExpandButton.setObjectName(u"rightExpandButton")

        self.rightHandleLayout.addWidget(self.rightExpandButton)

        self.rightHandleSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.rightHandleLayout.addItem(self.rightHandleSpacer)


        self.body.addWidget(self.rightHandle)

        self.rightPanel = QFrame(self.centralWidget)
        self.rightPanel.setObjectName(u"rightPanel")
        self.rightPanel.setMinimumSize(QSize(280, 0))
        self.rightPanel.setMaximumSize(QSize(460, 16777215))
        self.rightLayout = QVBoxLayout(self.rightPanel)
        self.rightLayout.setObjectName(u"rightLayout")
        self.rightCollapseButton = QPushButton(self.rightPanel)
        self.rightCollapseButton.setObjectName(u"rightCollapseButton")

        self.rightLayout.addWidget(self.rightCollapseButton)

        self.stateTitle = QLabel(self.rightPanel)
        self.stateTitle.setObjectName(u"stateTitle")

        self.rightLayout.addWidget(self.stateTitle)

        self.stateForm = QFormLayout()
        self.stateForm.setObjectName(u"stateForm")
        self.stateChapterLabel = QLabel(self.rightPanel)
        self.stateChapterLabel.setObjectName(u"stateChapterLabel")

        self.stateForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.stateChapterLabel)

        self.stateChapterValue = QLabel(self.rightPanel)
        self.stateChapterValue.setObjectName(u"stateChapterValue")

        self.stateForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.stateChapterValue)

        self.stateTimeLabel = QLabel(self.rightPanel)
        self.stateTimeLabel.setObjectName(u"stateTimeLabel")

        self.stateForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.stateTimeLabel)

        self.stateTimeValue = QLabel(self.rightPanel)
        self.stateTimeValue.setObjectName(u"stateTimeValue")

        self.stateForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.stateTimeValue)

        self.stateLocationLabel = QLabel(self.rightPanel)
        self.stateLocationLabel.setObjectName(u"stateLocationLabel")

        self.stateForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.stateLocationLabel)

        self.stateLocationValue = QLabel(self.rightPanel)
        self.stateLocationValue.setObjectName(u"stateLocationValue")

        self.stateForm.setWidget(2, QFormLayout.ItemRole.FieldRole, self.stateLocationValue)

        self.stateProtagonistLabel = QLabel(self.rightPanel)
        self.stateProtagonistLabel.setObjectName(u"stateProtagonistLabel")

        self.stateForm.setWidget(3, QFormLayout.ItemRole.LabelRole, self.stateProtagonistLabel)

        self.stateProtagonistValue = QLabel(self.rightPanel)
        self.stateProtagonistValue.setObjectName(u"stateProtagonistValue")

        self.stateForm.setWidget(3, QFormLayout.ItemRole.FieldRole, self.stateProtagonistValue)

        self.stateCultivationLabel = QLabel(self.rightPanel)
        self.stateCultivationLabel.setObjectName(u"stateCultivationLabel")

        self.stateForm.setWidget(4, QFormLayout.ItemRole.LabelRole, self.stateCultivationLabel)

        self.stateCultivationValue = QLabel(self.rightPanel)
        self.stateCultivationValue.setObjectName(u"stateCultivationValue")

        self.stateForm.setWidget(4, QFormLayout.ItemRole.FieldRole, self.stateCultivationValue)


        self.rightLayout.addLayout(self.stateForm)

        self.memoryPanel = QPlainTextEdit(self.rightPanel)
        self.memoryPanel.setObjectName(u"memoryPanel")
        self.memoryPanel.setReadOnly(True)

        self.rightLayout.addWidget(self.memoryPanel)


        self.body.addWidget(self.rightPanel)


        self.root.addLayout(self.body)

        self.bottom = QHBoxLayout()
        self.bottom.setObjectName(u"bottom")
        self.charCountLabel = QLabel(self.centralWidget)
        self.charCountLabel.setObjectName(u"charCountLabel")

        self.bottom.addWidget(self.charCountLabel)

        self.bottomSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.bottom.addItem(self.bottomSpacer)

        self.saveButton = QPushButton(self.centralWidget)
        self.saveButton.setObjectName(u"saveButton")

        self.bottom.addWidget(self.saveButton)

        self.writeButton = QPushButton(self.centralWidget)
        self.writeButton.setObjectName(u"writeButton")

        self.bottom.addWidget(self.writeButton)

        self.reviseButton = QPushButton(self.centralWidget)
        self.reviseButton.setObjectName(u"reviseButton")

        self.bottom.addWidget(self.reviseButton)

        self.checkButton = QPushButton(self.centralWidget)
        self.checkButton.setObjectName(u"checkButton")

        self.bottom.addWidget(self.checkButton)


        self.root.addLayout(self.bottom)

        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuProject = QMenu(self.menuBar)
        self.menuProject.setObjectName(u"menuProject")
        self.menuSettings = QMenu(self.menuBar)
        self.menuSettings.setObjectName(u"menuSettings")
        MainWindow.setMenuBar(self.menuBar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.menuProject.addAction(self.actionNew)
        self.menuProject.addAction(self.actionOpen)
        self.menuProject.addAction(self.actionBackup)
        self.menuSettings.addAction(self.actionAISettings)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        self.actionNew.setText(QCoreApplication.translate("MainWindow", u"\uc0c8 \uc791\ud488", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"\uc791\ud488 \uc5f4\uae30", None))
        self.actionBackup.setText(QCoreApplication.translate("MainWindow", u"\ud504\ub85c\uc81d\ud2b8 \ubc31\uc5c5", None))
        self.actionAISettings.setText(QCoreApplication.translate("MainWindow", u"AI / \ud3b8\uc9d1\uae30 \uc124\uc815", None))
        self.appLabel.setText(QCoreApplication.translate("MainWindow", u"Novel Studio", None))
        self.projectLabel.setText(QCoreApplication.translate("MainWindow", u"\ud504\ub85c\uc81d\ud2b8 \uc5c6\uc74c", None))
        self.aiStatusLabel.setText(QCoreApplication.translate("MainWindow", u"AI \u25cf \ubbf8\uc5f0\uacb0", None))
        self.aiSettingsButton.setText(QCoreApplication.translate("MainWindow", u"AI / \ud3b8\uc9d1\uae30 \uc124\uc815", None))
        self.leftCollapseButton.setText(QCoreApplication.translate("MainWindow", u"\uc67c\ucabd \uc0ac\uc774\ub4dc\ubc14 \uc811\uae30 \u25c0", None))
        self.leftExpandButton.setText(QCoreApplication.translate("MainWindow", u"\u25b6", None))
        self.rightExpandButton.setText(QCoreApplication.translate("MainWindow", u"\u25c0", None))
        self.rightCollapseButton.setText(QCoreApplication.translate("MainWindow", u"\uc624\ub978\ucabd \uc0ac\uc774\ub4dc\ubc14 \uc811\uae30 \u25b6", None))
        self.stateTitle.setText(QCoreApplication.translate("MainWindow", u"\ud604\uc7ac \uc791\ud488 \uc0c1\ud0dc", None))
        self.stateChapterLabel.setText(QCoreApplication.translate("MainWindow", u"\ud654", None))
        self.stateChapterValue.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.stateTimeLabel.setText(QCoreApplication.translate("MainWindow", u"\uc2dc\uac04", None))
        self.stateTimeValue.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.stateLocationLabel.setText(QCoreApplication.translate("MainWindow", u"\uc7a5\uc18c", None))
        self.stateLocationValue.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.stateProtagonistLabel.setText(QCoreApplication.translate("MainWindow", u"\uc8fc\uc778\uacf5", None))
        self.stateProtagonistValue.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.stateCultivationLabel.setText(QCoreApplication.translate("MainWindow", u"\uacbd\uc9c0", None))
        self.stateCultivationValue.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.charCountLabel.setText(QCoreApplication.translate("MainWindow", u"\ud604\uc7ac 0\uc790 / \ubaa9\ud45c 0\uc790", None))
        self.saveButton.setText(QCoreApplication.translate("MainWindow", u"\uc800\uc7a5", None))
        self.writeButton.setText(QCoreApplication.translate("MainWindow", u"AI \uc9d1\ud544", None))
        self.reviseButton.setText(QCoreApplication.translate("MainWindow", u"AI \uc724\ubb38", None))
        self.checkButton.setText(QCoreApplication.translate("MainWindow", u"AI \uac80\uc99d", None))
        self.menuProject.setTitle(QCoreApplication.translate("MainWindow", u"\ud504\ub85c\uc81d\ud2b8", None))
        self.menuSettings.setTitle(QCoreApplication.translate("MainWindow", u"\uc124\uc815", None))
        pass
    # retranslateUi

