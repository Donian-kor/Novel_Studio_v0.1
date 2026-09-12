# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sections.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_SectionsPage(object):
    def setupUi(self, SectionsPage):
        if not SectionsPage.objectName():
            SectionsPage.setObjectName(u"SectionsPage")
        self.l = QVBoxLayout(SectionsPage)
        self.l.setObjectName(u"l")
        self.hint = QLabel(SectionsPage)
        self.hint.setObjectName(u"hint")

        self.l.addWidget(self.hint)

        self.catCombo = QComboBox(SectionsPage)
        self.catCombo.setObjectName(u"catCombo")

        self.l.addWidget(self.catCombo)

        self.buttons = QHBoxLayout()
        self.buttons.setObjectName(u"buttons")
        self.addBtn = QPushButton(SectionsPage)
        self.addBtn.setObjectName(u"addBtn")

        self.buttons.addWidget(self.addBtn)

        self.aiBtn = QPushButton(SectionsPage)
        self.aiBtn.setObjectName(u"aiBtn")

        self.buttons.addWidget(self.aiBtn)

        self.saveBtn = QPushButton(SectionsPage)
        self.saveBtn.setObjectName(u"saveBtn")

        self.buttons.addWidget(self.saveBtn)

        self.delBtn = QPushButton(SectionsPage)
        self.delBtn.setObjectName(u"delBtn")

        self.buttons.addWidget(self.delBtn)


        self.l.addLayout(self.buttons)

        self.work = QHBoxLayout()
        self.work.setObjectName(u"work")
        self.list = QListWidget(SectionsPage)
        self.list.setObjectName(u"list")

        self.work.addWidget(self.list)

        self.detail = QPlainTextEdit(SectionsPage)
        self.detail.setObjectName(u"detail")

        self.work.addWidget(self.detail)


        self.l.addLayout(self.work)


        self.retranslateUi(SectionsPage)

        QMetaObject.connectSlotsByName(SectionsPage)
    # setupUi

    def retranslateUi(self, SectionsPage):
        self.hint.setText(QCoreApplication.translate("SectionsPage", u"\uc778\ubb3c\u00b7\uc138\ub825\u00b7\uc7a5\uc18c\u00b7\ubcf5\uc120\u00b7\ud575\uc2ec \uc0ac\uac74\u00b7\uc2dc\uac04\ucd95\uc744 \uc5ec\ub7ec \ud56d\ubaa9\uc73c\ub85c \uad00\ub9ac\ud569\ub2c8\ub2e4. \ud544\uc694\ud55c \ub9cc\ud07c \ucd94\uac00\ud558\uc138\uc694.", None))
        self.addBtn.setText(QCoreApplication.translate("SectionsPage", u"+ \ucd94\uac00", None))
        self.aiBtn.setText(QCoreApplication.translate("SectionsPage", u"AI\ub85c \ucd94\uac00", None))
        self.saveBtn.setText(QCoreApplication.translate("SectionsPage", u"\uc800\uc7a5", None))
        self.delBtn.setText(QCoreApplication.translate("SectionsPage", u"\uc0ad\uc81c", None))
        pass
    # retranslateUi

