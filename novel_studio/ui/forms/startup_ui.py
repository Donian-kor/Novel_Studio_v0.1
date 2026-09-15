# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'startup.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_StartupDialog(object):
    def setupUi(self, StartupDialog):
        if not StartupDialog.objectName():
            StartupDialog.setObjectName(u"StartupDialog")
        StartupDialog.setMinimumSize(QSize(780, 620))
        self.root = QVBoxLayout(StartupDialog)
        self.root.setObjectName(u"root")
        self.welcome = QLabel(StartupDialog)
        self.welcome.setObjectName(u"welcome")

        self.root.addWidget(self.welcome)

        self.desc = QLabel(StartupDialog)
        self.desc.setObjectName(u"desc")

        self.root.addWidget(self.desc)

        self.newBox = QGroupBox(StartupDialog)
        self.newBox.setObjectName(u"newBox")
        self.newForm = QFormLayout(self.newBox)
        self.newForm.setObjectName(u"newForm")
        self.titleLabel = QLabel(self.newBox)
        self.titleLabel.setObjectName(u"titleLabel")

        self.newForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.titleLabel)

        self.titleEdit = QLineEdit(self.newBox)
        self.titleEdit.setObjectName(u"titleEdit")

        self.newForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.titleEdit)

        self.genreLabel = QLabel(self.newBox)
        self.genreLabel.setObjectName(u"genreLabel")

        self.newForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.genreLabel)

        self.genreEdit = QComboBox(self.newBox)
        self.genreEdit.addItem("")
        self.genreEdit.addItem("")
        self.genreEdit.addItem("")
        self.genreEdit.addItem("")
        self.genreEdit.addItem("")
        self.genreEdit.addItem("")
        self.genreEdit.addItem("")
        self.genreEdit.addItem("")
        self.genreEdit.addItem("")
        self.genreEdit.addItem("")
        self.genreEdit.setObjectName(u"genreEdit")
        self.genreEdit.setEditable(True)

        self.newForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.genreEdit)

        self.moodLabel = QLabel(self.newBox)
        self.moodLabel.setObjectName(u"moodLabel")

        self.newForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.moodLabel)

        self.moodEdit = QLineEdit(self.newBox)
        self.moodEdit.setObjectName(u"moodEdit")

        self.newForm.setWidget(2, QFormLayout.ItemRole.FieldRole, self.moodEdit)

        self.totalLabel = QLabel(self.newBox)
        self.totalLabel.setObjectName(u"totalLabel")

        self.newForm.setWidget(3, QFormLayout.ItemRole.LabelRole, self.totalLabel)

        self.totalSpin = QSpinBox(self.newBox)
        self.totalSpin.setObjectName(u"totalSpin")
        self.totalSpin.setValue(500)
        self.totalSpin.setMinimum(1)
        self.totalSpin.setMaximum(5000)

        self.newForm.setWidget(3, QFormLayout.ItemRole.FieldRole, self.totalSpin)

        self.charsLabel = QLabel(self.newBox)
        self.charsLabel.setObjectName(u"charsLabel")

        self.newForm.setWidget(4, QFormLayout.ItemRole.LabelRole, self.charsLabel)

        self.charSpin = QSpinBox(self.newBox)
        self.charSpin.setObjectName(u"charSpin")
        self.charSpin.setValue(5000)
        self.charSpin.setMinimum(500)
        self.charSpin.setMaximum(30000)

        self.newForm.setWidget(4, QFormLayout.ItemRole.FieldRole, self.charSpin)

        self.tolLabel = QLabel(self.newBox)
        self.tolLabel.setObjectName(u"tolLabel")

        self.newForm.setWidget(5, QFormLayout.ItemRole.LabelRole, self.tolLabel)

        self.tolSpin = QSpinBox(self.newBox)
        self.tolSpin.setObjectName(u"tolSpin")
        self.tolSpin.setValue(300)
        self.tolSpin.setMinimum(0)
        self.tolSpin.setMaximum(5000)

        self.newForm.setWidget(5, QFormLayout.ItemRole.FieldRole, self.tolSpin)

        self.sectionLabel = QLabel(self.newBox)
        self.sectionLabel.setObjectName(u"sectionLabel")

        self.newForm.setWidget(6, QFormLayout.ItemRole.LabelRole, self.sectionLabel)

        self.sectionSpin = QSpinBox(self.newBox)
        self.sectionSpin.setObjectName(u"sectionSpin")
        self.sectionSpin.setValue(5)
        self.sectionSpin.setMinimum(1)
        self.sectionSpin.setMaximum(50)

        self.newForm.setWidget(6, QFormLayout.ItemRole.FieldRole, self.sectionSpin)


        self.root.addWidget(self.newBox)

        self.tolHelp = QLabel(StartupDialog)
        self.tolHelp.setObjectName(u"tolHelp")
        self.tolHelp.setWordWrap(True)

        self.root.addWidget(self.tolHelp)

        self.sectionHelp = QLabel(StartupDialog)
        self.sectionHelp.setObjectName(u"sectionHelp")
        self.sectionHelp.setWordWrap(True)

        self.root.addWidget(self.sectionHelp)

        self.actions = QHBoxLayout()
        self.actions.setObjectName(u"actions")
        self.createBtn = QPushButton(StartupDialog)
        self.createBtn.setObjectName(u"createBtn")

        self.actions.addWidget(self.createBtn)

        self.openBtn = QPushButton(StartupDialog)
        self.openBtn.setObjectName(u"openBtn")

        self.actions.addWidget(self.openBtn)

        self.settingsBtn = QPushButton(StartupDialog)
        self.settingsBtn.setObjectName(u"settingsBtn")

        self.actions.addWidget(self.settingsBtn)

        self.exitBtn = QPushButton(StartupDialog)
        self.exitBtn.setObjectName(u"exitBtn")

        self.actions.addWidget(self.exitBtn)


        self.root.addLayout(self.actions)


        self.retranslateUi(StartupDialog)

        QMetaObject.connectSlotsByName(StartupDialog)
    # setupUi

    def retranslateUi(self, StartupDialog):
        StartupDialog.setWindowTitle(QCoreApplication.translate("StartupDialog", u"Novel Studio - \ud504\ub85c\uc81d\ud2b8 \uc2dc\uc791", None))
        self.welcome.setText(QCoreApplication.translate("StartupDialog", u"Novel Studio", None))
        self.desc.setText(QCoreApplication.translate("StartupDialog", u"\uc0c8 \uc791\ud488\uc744 \ub9cc\ub4e4\uac70\ub098 \uae30\uc874 \uc791\ud488\uc744 \ubd88\ub7ec\uc640 \uc2dc\uc791\ud558\uc138\uc694.", None))
        self.newBox.setTitle(QCoreApplication.translate("StartupDialog", u"\uc0c8 \ud504\ub85c\uc81d\ud2b8", None))
        self.titleLabel.setText(QCoreApplication.translate("StartupDialog", u"\uc791\ud488\uba85", None))
        self.genreLabel.setText(QCoreApplication.translate("StartupDialog", u"\uc7a5\ub974", None))
        self.genreEdit.setItemText(0, QCoreApplication.translate("StartupDialog", u"\uc120\ud611", None))
        self.genreEdit.setItemText(1, QCoreApplication.translate("StartupDialog", u"\ubb34\ud611", None))
        self.genreEdit.setItemText(2, QCoreApplication.translate("StartupDialog", u"\ud310\ud0c0\uc9c0", None))
        self.genreEdit.setItemText(3, QCoreApplication.translate("StartupDialog", u"\ub85c\ub9e8\uc2a4", None))
        self.genreEdit.setItemText(4, QCoreApplication.translate("StartupDialog", u"\ud604\ub300", None))
        self.genreEdit.setItemText(5, QCoreApplication.translate("StartupDialog", u"\uc2a4\ub9b4\ub7ec", None))
        self.genreEdit.setItemText(6, QCoreApplication.translate("StartupDialog", u"\ud638\ub7ec", None))
        self.genreEdit.setItemText(7, QCoreApplication.translate("StartupDialog", u"SF", None))
        self.genreEdit.setItemText(8, QCoreApplication.translate("StartupDialog", u"\uc5ed\uc0ac", None))
        self.genreEdit.setItemText(9, QCoreApplication.translate("StartupDialog", u"\uac8c\uc784", None))

        self.moodLabel.setText(QCoreApplication.translate("StartupDialog", u"\ubd84\uc704\uae30", None))
        self.moodEdit.setText(QCoreApplication.translate("StartupDialog", u"\uc9c4\uc911\ud558\uace0 \uc5b4\ub450\uc6b4 \ubd84\uc704\uae30", None))
        self.totalLabel.setText(QCoreApplication.translate("StartupDialog", u"\ucd1d \ud654\uc218", None))
        self.charsLabel.setText(QCoreApplication.translate("StartupDialog", u"\ud654\ub2f9 \ubaa9\ud45c \uae00\uc790\uc218", None))
        self.tolLabel.setText(QCoreApplication.translate("StartupDialog", u"\ud5c8\uc6a9 \uc624\ucc28", None))
        self.sectionLabel.setText(QCoreApplication.translate("StartupDialog", u"\uc2a4\ud1a0\ub9ac \uad6c\uac04 \ud06c\uae30", None))
        self.tolHelp.setText(QCoreApplication.translate("StartupDialog", u"\ud5c8\uc6a9 \uc624\ucc28: AI \uc9d1\ud544 \uc2dc \ubaa9\ud45c \uae00\uc790\uc218 \u00b1 \ubc94\uc704. \uc608) \ubaa9\ud45c 5000\uc790\u00b7\uc624\ucc28 300 \u2192 4700~5300\uc790 \ud5c8\uc6a9", None))
        self.sectionHelp.setText(QCoreApplication.translate("StartupDialog", u"\uc2a4\ud1a0\ub9ac \uad6c\uac04 \ud06c\uae30: \ud55c \uad6c\uac04\uc5d0 \ubb36\uc744 \ud654 \uc218. \uc608) 5 \u2192 1~5\ud654, 6~10\ud654 \uad6c\uac04\uc73c\ub85c \ub098\ub268", None))
        self.createBtn.setText(QCoreApplication.translate("StartupDialog", u"\uc0c8 \ud504\ub85c\uc81d\ud2b8 \ub9cc\ub4e4\uae30", None))
        self.openBtn.setText(QCoreApplication.translate("StartupDialog", u"\uae30\uc874 \ud504\ub85c\uc81d\ud2b8 \ubd88\ub7ec\uc624\uae30", None))
        self.settingsBtn.setText(QCoreApplication.translate("StartupDialog", u"AI / \ud3b8\uc9d1\uae30 \uc124\uc815", None))
        self.exitBtn.setText(QCoreApplication.translate("StartupDialog", u"\uc885\ub8cc", None))
    # retranslateUi

