# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'new_project.ui'
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
    QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpinBox, QWidget)

class Ui_QDialog(object):
    def setupUi(self, NewProjectDialog):
        if not NewProjectDialog.objectName():
            NewProjectDialog.setObjectName(u"NewProjectDialog")
        NewProjectDialog.resize(650, 520)
        self.root = QFormLayout(NewProjectDialog)
        self.root.setObjectName(u"root")
        self.titleLabel = QLabel(NewProjectDialog)
        self.titleLabel.setObjectName(u"titleLabel")

        self.root.setWidget(0, QFormLayout.ItemRole.LabelRole, self.titleLabel)

        self.titleEdit = QLineEdit(NewProjectDialog)
        self.titleEdit.setObjectName(u"titleEdit")

        self.root.setWidget(0, QFormLayout.ItemRole.FieldRole, self.titleEdit)

        self.folderLabel = QLabel(NewProjectDialog)
        self.folderLabel.setObjectName(u"folderLabel")

        self.root.setWidget(1, QFormLayout.ItemRole.LabelRole, self.folderLabel)

        self.fl = QHBoxLayout()
        self.fl.setObjectName(u"fl")
        self.folderEdit = QLineEdit(NewProjectDialog)
        self.folderEdit.setObjectName(u"folderEdit")

        self.fl.addWidget(self.folderEdit)

        self.browseButton = QPushButton(NewProjectDialog)
        self.browseButton.setObjectName(u"browseButton")

        self.fl.addWidget(self.browseButton)


        self.root.setLayout(1, QFormLayout.ItemRole.FieldRole, self.fl)

        self.genreLabel = QLabel(NewProjectDialog)
        self.genreLabel.setObjectName(u"genreLabel")

        self.root.setWidget(2, QFormLayout.ItemRole.LabelRole, self.genreLabel)

        self.genreEdit = QLineEdit(NewProjectDialog)
        self.genreEdit.setObjectName(u"genreEdit")

        self.root.setWidget(2, QFormLayout.ItemRole.FieldRole, self.genreEdit)

        self.moodLabel = QLabel(NewProjectDialog)
        self.moodLabel.setObjectName(u"moodLabel")

        self.root.setWidget(3, QFormLayout.ItemRole.LabelRole, self.moodLabel)

        self.moodEdit = QLineEdit(NewProjectDialog)
        self.moodEdit.setObjectName(u"moodEdit")

        self.root.setWidget(3, QFormLayout.ItemRole.FieldRole, self.moodEdit)

        self.totalLabel = QLabel(NewProjectDialog)
        self.totalLabel.setObjectName(u"totalLabel")

        self.root.setWidget(4, QFormLayout.ItemRole.LabelRole, self.totalLabel)

        self.totalSpin = QSpinBox(NewProjectDialog)
        self.totalSpin.setObjectName(u"totalSpin")
        self.totalSpin.setMinimum(1)
        self.totalSpin.setMaximum(5000)
        self.totalSpin.setValue(500)

        self.root.setWidget(4, QFormLayout.ItemRole.FieldRole, self.totalSpin)

        self.charsLabel = QLabel(NewProjectDialog)
        self.charsLabel.setObjectName(u"charsLabel")

        self.root.setWidget(5, QFormLayout.ItemRole.LabelRole, self.charsLabel)

        self.charsSpin = QSpinBox(NewProjectDialog)
        self.charsSpin.setObjectName(u"charsSpin")
        self.charsSpin.setMinimum(500)
        self.charsSpin.setMaximum(30000)
        self.charsSpin.setValue(5000)

        self.root.setWidget(5, QFormLayout.ItemRole.FieldRole, self.charsSpin)

        self.tolLabel = QLabel(NewProjectDialog)
        self.tolLabel.setObjectName(u"tolLabel")

        self.root.setWidget(6, QFormLayout.ItemRole.LabelRole, self.tolLabel)

        self.tolSpin = QSpinBox(NewProjectDialog)
        self.tolSpin.setObjectName(u"tolSpin")
        self.tolSpin.setMinimum(0)
        self.tolSpin.setMaximum(5000)
        self.tolSpin.setValue(300)

        self.root.setWidget(6, QFormLayout.ItemRole.FieldRole, self.tolSpin)

        self.buttonBox = QDialogButtonBox(NewProjectDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.root.setWidget(7, QFormLayout.ItemRole.FieldRole, self.buttonBox)


        self.retranslateUi(NewProjectDialog)

        QMetaObject.connectSlotsByName(NewProjectDialog)
    # setupUi

    def retranslateUi(self, NewProjectDialog):
        self.titleLabel.setText(QCoreApplication.translate("QDialog", u"\uc791\ud488\uba85", None))
        self.folderLabel.setText(QCoreApplication.translate("QDialog", u"\uc800\uc7a5 \ud3f4\ub354", None))
        self.browseButton.setText(QCoreApplication.translate("QDialog", u"\ucc3e\uae30", None))
        self.genreLabel.setText(QCoreApplication.translate("QDialog", u"\uc7a5\ub974", None))
        self.genreEdit.setText(QCoreApplication.translate("QDialog", u"\uc120\ud611", None))
        self.moodLabel.setText(QCoreApplication.translate("QDialog", u"\ubd84\uc704\uae30", None))
        self.moodEdit.setText(QCoreApplication.translate("QDialog", u"\uc9c4\uc911\ud558\uace0 \uc5b4\ub450\uc6b4 \ubd84\uc704\uae30", None))
        self.totalLabel.setText(QCoreApplication.translate("QDialog", u"\ucd1d \ud654\uc218", None))
        self.charsLabel.setText(QCoreApplication.translate("QDialog", u"\ud654\ub2f9 \ubaa9\ud45c \uae00\uc790 \uc218", None))
        self.tolLabel.setText(QCoreApplication.translate("QDialog", u"\ud5c8\uc6a9 \uc624\ucc28", None))
        pass
    # retranslateUi

