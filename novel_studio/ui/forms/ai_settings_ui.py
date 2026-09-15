# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ai_settings.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFontComboBox, QFormLayout, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSlider, QWidget)

class Ui_AISettingsDialog(object):
    def setupUi(self, AISettingsDialog):
        if not AISettingsDialog.objectName():
            AISettingsDialog.setObjectName(u"AISettingsDialog")
        AISettingsDialog.resize(845, 255)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AISettingsDialog.sizePolicy().hasHeightForWidth())
        AISettingsDialog.setSizePolicy(sizePolicy)
        AISettingsDialog.setMinimumSize(QSize(845, 255))
        self.gridLayout = QGridLayout(AISettingsDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(4)
        self.gridLayout.setVerticalSpacing(5)
        self.gridLayout.setContentsMargins(-1, -1, -1, 9)
        self.aiBox = QGroupBox(AISettingsDialog)
        self.aiBox.setObjectName(u"aiBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.aiBox.sizePolicy().hasHeightForWidth())
        self.aiBox.setSizePolicy(sizePolicy1)
        self.f = QFormLayout(self.aiBox)
        self.f.setObjectName(u"f")
        self.pLbl = QLabel(self.aiBox)
        self.pLbl.setObjectName(u"pLbl")

        self.f.setWidget(0, QFormLayout.ItemRole.LabelRole, self.pLbl)

        self.provider = QComboBox(self.aiBox)
        self.provider.setObjectName(u"provider")

        self.f.setWidget(0, QFormLayout.ItemRole.FieldRole, self.provider)

        self.urlLbl = QLabel(self.aiBox)
        self.urlLbl.setObjectName(u"urlLbl")

        self.f.setWidget(1, QFormLayout.ItemRole.LabelRole, self.urlLbl)

        self.urlEdit = QLineEdit(self.aiBox)
        self.urlEdit.setObjectName(u"urlEdit")

        self.f.setWidget(1, QFormLayout.ItemRole.FieldRole, self.urlEdit)

        self.modelLbl = QLabel(self.aiBox)
        self.modelLbl.setObjectName(u"modelLbl")

        self.f.setWidget(2, QFormLayout.ItemRole.LabelRole, self.modelLbl)

        self.modelEdit = QComboBox(self.aiBox)
        self.modelEdit.setObjectName(u"modelEdit")
        self.modelEdit.setEditable(True)

        self.f.setWidget(2, QFormLayout.ItemRole.FieldRole, self.modelEdit)

        self.keyLbl = QLabel(self.aiBox)
        self.keyLbl.setObjectName(u"keyLbl")

        self.f.setWidget(3, QFormLayout.ItemRole.LabelRole, self.keyLbl)

        self.keyEdit = QLineEdit(self.aiBox)
        self.keyEdit.setObjectName(u"keyEdit")
        self.keyEdit.setEchoMode(QLineEdit.EchoMode.Password)

        self.f.setWidget(3, QFormLayout.ItemRole.FieldRole, self.keyEdit)

        self.ab = QHBoxLayout()
        self.ab.setObjectName(u"ab")
        self.connStatus = QLabel(self.aiBox)
        self.connStatus.setObjectName(u"connStatus")

        self.ab.addWidget(self.connStatus)

        self.testBtn = QPushButton(self.aiBox)
        self.testBtn.setObjectName(u"testBtn")

        self.ab.addWidget(self.testBtn)

        self.saveBtn = QPushButton(self.aiBox)
        self.saveBtn.setObjectName(u"saveBtn")

        self.ab.addWidget(self.saveBtn)


        self.f.setLayout(4, QFormLayout.ItemRole.FieldRole, self.ab)


        self.gridLayout.addWidget(self.aiBox, 0, 0, 1, 1)

        self.editorBox = QGroupBox(AISettingsDialog)
        self.editorBox.setObjectName(u"editorBox")
        sizePolicy1.setHeightForWidth(self.editorBox.sizePolicy().hasHeightForWidth())
        self.editorBox.setSizePolicy(sizePolicy1)
        self.ef = QFormLayout(self.editorBox)
        self.ef.setObjectName(u"ef")
        self.fontLbl = QLabel(self.editorBox)
        self.fontLbl.setObjectName(u"fontLbl")

        self.ef.setWidget(0, QFormLayout.ItemRole.LabelRole, self.fontLbl)

        self.fontEdit = QFontComboBox(self.editorBox)
        self.fontEdit.setObjectName(u"fontEdit")

        self.ef.setWidget(0, QFormLayout.ItemRole.FieldRole, self.fontEdit)

        self.sizeLbl = QLabel(self.editorBox)
        self.sizeLbl.setObjectName(u"sizeLbl")

        self.ef.setWidget(1, QFormLayout.ItemRole.LabelRole, self.sizeLbl)

        self.fontSizeLayout = QHBoxLayout()
        self.fontSizeLayout.setObjectName(u"fontSizeLayout")
        self.fontSpin = QSlider(self.editorBox)
        self.fontSpin.setObjectName(u"fontSpin")
        self.fontSpin.setMinimum(8)
        self.fontSpin.setMaximum(60)
        self.fontSpin.setOrientation(Qt.Orientation.Horizontal)
        self.fontSpin.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.fontSpin.setTickInterval(4)

        self.fontSizeLayout.addWidget(self.fontSpin)

        self.fontSizeValue = QLabel(self.editorBox)
        self.fontSizeValue.setObjectName(u"fontSizeValue")
        self.fontSizeValue.setMinimumSize(QSize(55, 0))
        self.fontSizeValue.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.fontSizeLayout.addWidget(self.fontSizeValue)


        self.ef.setLayout(1, QFormLayout.ItemRole.FieldRole, self.fontSizeLayout)

        self.tcLbl = QLabel(self.editorBox)
        self.tcLbl.setObjectName(u"tcLbl")

        self.ef.setWidget(2, QFormLayout.ItemRole.LabelRole, self.tcLbl)

        self.textColor = QPushButton(self.editorBox)
        self.textColor.setObjectName(u"textColor")

        self.ef.setWidget(2, QFormLayout.ItemRole.FieldRole, self.textColor)

        self.bcLbl = QLabel(self.editorBox)
        self.bcLbl.setObjectName(u"bcLbl")

        self.ef.setWidget(3, QFormLayout.ItemRole.LabelRole, self.bcLbl)

        self.bgColor = QPushButton(self.editorBox)
        self.bgColor.setObjectName(u"bgColor")

        self.ef.setWidget(3, QFormLayout.ItemRole.FieldRole, self.bgColor)

        self.endStateCheck = QCheckBox(self.editorBox)
        self.endStateCheck.setObjectName(u"endStateCheck")

        self.ef.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.endStateCheck)


        self.gridLayout.addWidget(self.editorBox, 0, 1, 1, 1)

        self.note = QLabel(AISettingsDialog)
        self.note.setObjectName(u"note")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.note.sizePolicy().hasHeightForWidth())
        self.note.setSizePolicy(sizePolicy2)
        self.note.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.gridLayout.addWidget(self.note, 2, 0, 1, 2)


        self.retranslateUi(AISettingsDialog)

        QMetaObject.connectSlotsByName(AISettingsDialog)
    # setupUi

    def retranslateUi(self, AISettingsDialog):
        AISettingsDialog.setWindowTitle(QCoreApplication.translate("AISettingsDialog", u"AI / \ud3b8\uc9d1\uae30 \uc124\uc815", None))
        self.aiBox.setTitle(QCoreApplication.translate("AISettingsDialog", u"AI \uc5f0\uacb0", None))
        self.pLbl.setText(QCoreApplication.translate("AISettingsDialog", u"\uc81c\uacf5\uc790", None))
        self.urlLbl.setText(QCoreApplication.translate("AISettingsDialog", u"Base URL", None))
        self.modelLbl.setText(QCoreApplication.translate("AISettingsDialog", u"\ubaa8\ub378", None))
        self.keyLbl.setText(QCoreApplication.translate("AISettingsDialog", u"API Key", None))
#if QT_CONFIG(tooltip)
        self.connStatus.setToolTip(QCoreApplication.translate("AISettingsDialog", u"\uc5f0\uacb0 \ud14c\uc2a4\ud2b8\uc5d0 \uc131\uacf5\ud558\uba74 \ubaa8\ub378 \ubaa9\ub85d\uc744 \uc120\ud0dd\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.", None))
#endif // QT_CONFIG(tooltip)
        self.connStatus.setText(QCoreApplication.translate("AISettingsDialog", u"\uc5f0\uacb0 \uc548 \ub428", None))
        self.testBtn.setText(QCoreApplication.translate("AISettingsDialog", u"\uc5f0\uacb0 \ud14c\uc2a4\ud2b8", None))
        self.saveBtn.setText(QCoreApplication.translate("AISettingsDialog", u"\uc800\uc7a5", None))
        self.editorBox.setTitle(QCoreApplication.translate("AISettingsDialog", u"\uc6d0\uace0 \ud3b8\uc9d1\uae30", None))
        self.fontLbl.setText(QCoreApplication.translate("AISettingsDialog", u"\uae00\uaf34", None))
        self.sizeLbl.setText(QCoreApplication.translate("AISettingsDialog", u"\uae00\uc790 \ud06c\uae30", None))
        self.fontSizeValue.setText(QCoreApplication.translate("AISettingsDialog", u"18 pt", None))
        self.tcLbl.setText(QCoreApplication.translate("AISettingsDialog", u"\uae00\uc790 \uc0c9", None))
        self.textColor.setText(QCoreApplication.translate("AISettingsDialog", u"#E8E6E3", None))
        self.bcLbl.setText(QCoreApplication.translate("AISettingsDialog", u"\ubc30\uacbd \uc0c9", None))
        self.bgColor.setText(QCoreApplication.translate("AISettingsDialog", u"#2B2B2B", None))
#if QT_CONFIG(tooltip)
        self.endStateCheck.setToolTip(QCoreApplication.translate("AISettingsDialog", u"\ub044\uba74 \uc800\uc7a5\ud560 \ub54c AI\ub97c \ud638\ucd9c\ud558\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4. \ud544\uc694\ud560 \ub54c [\ud654 \uc885\ub8cc \uc0c1\ud0dc]\uc5d0\uc11c \uc9c1\uc811 \uc0dd\uc131\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.", None))
#endif // QT_CONFIG(tooltip)
        self.endStateCheck.setText(QCoreApplication.translate("AISettingsDialog", u"\uc6d0\uace0 \uc800\uc7a5 \ud6c4 AI\ub85c \ud654 \uc885\ub8cc \uc0c1\ud0dc \uc790\ub3d9 \uc0dd\uc131", None))
        self.note.setText(QCoreApplication.translate("AISettingsDialog", u"API Key\ub294 \uc6b4\uc601\uccb4\uc81c \ubcf4\uc548 \uc800\uc7a5\uc18c(keyring)\uc5d0 \uc800\uc7a5\ud569\ub2c8\ub2e4. \uae00\uaf34/\uae00\uc790 \ud06c\uae30/\uc0c9\uc0c1\uc740 \uc785\ub825\ub780 \uc5c6\uc774 \ub9c8\uc6b0\uc2a4\ub85c \uc120\ud0dd\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.", None))
    # retranslateUi

