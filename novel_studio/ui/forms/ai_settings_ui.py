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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QSpinBox, QWidget)

class Ui_QDialog(object):
    def setupUi(self, AISettingsDialog):
        if not AISettingsDialog.objectName():
            AISettingsDialog.setObjectName(u"AISettingsDialog")
        AISettingsDialog.resize(720, 760)
        self.root = QFormLayout(AISettingsDialog)
        self.root.setObjectName(u"root")
        self.urlLabel = QLabel(AISettingsDialog)
        self.urlLabel.setObjectName(u"urlLabel")

        self.root.setWidget(0, QFormLayout.ItemRole.LabelRole, self.urlLabel)

        self.urlEdit = QLineEdit(AISettingsDialog)
        self.urlEdit.setObjectName(u"urlEdit")

        self.root.setWidget(0, QFormLayout.ItemRole.FieldRole, self.urlEdit)

        self.modelLabel = QLabel(AISettingsDialog)
        self.modelLabel.setObjectName(u"modelLabel")

        self.root.setWidget(1, QFormLayout.ItemRole.LabelRole, self.modelLabel)

        self.modelEdit = QLineEdit(AISettingsDialog)
        self.modelEdit.setObjectName(u"modelEdit")

        self.root.setWidget(1, QFormLayout.ItemRole.FieldRole, self.modelEdit)

        self.mb = QHBoxLayout()
        self.mb.setObjectName(u"mb")
        self.refreshButton = QPushButton(AISettingsDialog)
        self.refreshButton.setObjectName(u"refreshButton")

        self.mb.addWidget(self.refreshButton)

        self.testButton = QPushButton(AISettingsDialog)
        self.testButton.setObjectName(u"testButton")

        self.mb.addWidget(self.testButton)


        self.root.setLayout(2, QFormLayout.ItemRole.FieldRole, self.mb)

        self.modelsList = QListWidget(AISettingsDialog)
        self.modelsList.setObjectName(u"modelsList")

        self.root.setWidget(3, QFormLayout.ItemRole.FieldRole, self.modelsList)

        self.tempLabel = QLabel(AISettingsDialog)
        self.tempLabel.setObjectName(u"tempLabel")

        self.root.setWidget(4, QFormLayout.ItemRole.LabelRole, self.tempLabel)

        self.tempSpin = QDoubleSpinBox(AISettingsDialog)
        self.tempSpin.setObjectName(u"tempSpin")
        self.tempSpin.setMaximum(2.000000000000000)
        self.tempSpin.setSingleStep(0.050000000000000)

        self.root.setWidget(4, QFormLayout.ItemRole.FieldRole, self.tempSpin)

        self.topLabel = QLabel(AISettingsDialog)
        self.topLabel.setObjectName(u"topLabel")

        self.root.setWidget(5, QFormLayout.ItemRole.LabelRole, self.topLabel)

        self.topSpin = QDoubleSpinBox(AISettingsDialog)
        self.topSpin.setObjectName(u"topSpin")
        self.topSpin.setMaximum(1.000000000000000)
        self.topSpin.setSingleStep(0.050000000000000)

        self.root.setWidget(5, QFormLayout.ItemRole.FieldRole, self.topSpin)

        self.maxLabel = QLabel(AISettingsDialog)
        self.maxLabel.setObjectName(u"maxLabel")

        self.root.setWidget(6, QFormLayout.ItemRole.LabelRole, self.maxLabel)

        self.maxTokensSpin = QSpinBox(AISettingsDialog)
        self.maxTokensSpin.setObjectName(u"maxTokensSpin")
        self.maxTokensSpin.setMinimum(500)
        self.maxTokensSpin.setMaximum(50000)

        self.root.setWidget(6, QFormLayout.ItemRole.FieldRole, self.maxTokensSpin)

        self.fontLabel = QLabel(AISettingsDialog)
        self.fontLabel.setObjectName(u"fontLabel")

        self.root.setWidget(7, QFormLayout.ItemRole.LabelRole, self.fontLabel)

        self.fontEdit = QLineEdit(AISettingsDialog)
        self.fontEdit.setObjectName(u"fontEdit")

        self.root.setWidget(7, QFormLayout.ItemRole.FieldRole, self.fontEdit)

        self.fontSizeLabel = QLabel(AISettingsDialog)
        self.fontSizeLabel.setObjectName(u"fontSizeLabel")

        self.root.setWidget(8, QFormLayout.ItemRole.LabelRole, self.fontSizeLabel)

        self.fontSizeSpin = QSpinBox(AISettingsDialog)
        self.fontSizeSpin.setObjectName(u"fontSizeSpin")
        self.fontSizeSpin.setMinimum(8)
        self.fontSizeSpin.setMaximum(48)

        self.root.setWidget(8, QFormLayout.ItemRole.FieldRole, self.fontSizeSpin)

        self.textColorLabel = QLabel(AISettingsDialog)
        self.textColorLabel.setObjectName(u"textColorLabel")

        self.root.setWidget(9, QFormLayout.ItemRole.LabelRole, self.textColorLabel)

        self.textColorEdit = QLineEdit(AISettingsDialog)
        self.textColorEdit.setObjectName(u"textColorEdit")

        self.root.setWidget(9, QFormLayout.ItemRole.FieldRole, self.textColorEdit)

        self.bgColorLabel = QLabel(AISettingsDialog)
        self.bgColorLabel.setObjectName(u"bgColorLabel")

        self.root.setWidget(10, QFormLayout.ItemRole.LabelRole, self.bgColorLabel)

        self.bgColorEdit = QLineEdit(AISettingsDialog)
        self.bgColorEdit.setObjectName(u"bgColorEdit")

        self.root.setWidget(10, QFormLayout.ItemRole.FieldRole, self.bgColorEdit)

        self.spacingLabel = QLabel(AISettingsDialog)
        self.spacingLabel.setObjectName(u"spacingLabel")

        self.root.setWidget(11, QFormLayout.ItemRole.LabelRole, self.spacingLabel)

        self.spacingSpin = QDoubleSpinBox(AISettingsDialog)
        self.spacingSpin.setObjectName(u"spacingSpin")
        self.spacingSpin.setMinimum(0.800000000000000)
        self.spacingSpin.setMaximum(3.000000000000000)
        self.spacingSpin.setSingleStep(0.100000000000000)

        self.root.setWidget(11, QFormLayout.ItemRole.FieldRole, self.spacingSpin)

        self.buttonBox = QDialogButtonBox(AISettingsDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.root.setWidget(12, QFormLayout.ItemRole.FieldRole, self.buttonBox)


        self.retranslateUi(AISettingsDialog)

        QMetaObject.connectSlotsByName(AISettingsDialog)
    # setupUi

    def retranslateUi(self, AISettingsDialog):
        self.urlLabel.setText(QCoreApplication.translate("QDialog", u"LM Studio \uc8fc\uc18c", None))
        self.modelLabel.setText(QCoreApplication.translate("QDialog", u"\ubaa8\ub378 ID (\ube44\uc6b0\uba74 \uccab \ubaa8\ub378)", None))
        self.refreshButton.setText(QCoreApplication.translate("QDialog", u"\ubaa8\ub378 \uc0c8\ub85c\uace0\uce68", None))
        self.testButton.setText(QCoreApplication.translate("QDialog", u"\uc5f0\uacb0 \ud14c\uc2a4\ud2b8", None))
        self.tempLabel.setText(QCoreApplication.translate("QDialog", u"Temperature", None))
        self.topLabel.setText(QCoreApplication.translate("QDialog", u"Top P", None))
        self.maxLabel.setText(QCoreApplication.translate("QDialog", u"\ucd5c\ub300 \ucd9c\ub825 \ud1a0\ud070", None))
        self.fontLabel.setText(QCoreApplication.translate("QDialog", u"\uc6d0\uace0 \uae00\uaf34", None))
        self.fontSizeLabel.setText(QCoreApplication.translate("QDialog", u"\uc6d0\uace0 \uae00\uc790 \ud06c\uae30", None))
        self.textColorLabel.setText(QCoreApplication.translate("QDialog", u"\uc6d0\uace0 \uae00\uc790 \uc0c9", None))
        self.bgColorLabel.setText(QCoreApplication.translate("QDialog", u"\uc6d0\uace0 \ubc30\uacbd \uc0c9", None))
        self.spacingLabel.setText(QCoreApplication.translate("QDialog", u"\uc904 \uac04\uaca9", None))
        pass
    # retranslateUi

