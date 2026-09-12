# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'section_page.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_QWidget(object):
    def setupUi(self, SectionPage):
        if not SectionPage.objectName():
            SectionPage.setObjectName(u"SectionPage")
        SectionPage.resize(1000, 700)
        self.root = QVBoxLayout(SectionPage)
        self.root.setObjectName(u"root")
        self.sectionTitle = QLabel(SectionPage)
        self.sectionTitle.setObjectName(u"sectionTitle")

        self.root.addWidget(self.sectionTitle)

        self.contentEdit = QPlainTextEdit(SectionPage)
        self.contentEdit.setObjectName(u"contentEdit")
        self.contentEdit.setReadOnly(False)

        self.root.addWidget(self.contentEdit)

        self.buttons = QHBoxLayout()
        self.buttons.setObjectName(u"buttons")
        self.generateButton = QPushButton(SectionPage)
        self.generateButton.setObjectName(u"generateButton")

        self.buttons.addWidget(self.generateButton)

        self.improveButton = QPushButton(SectionPage)
        self.improveButton.setObjectName(u"improveButton")

        self.buttons.addWidget(self.improveButton)

        self.loadButton = QPushButton(SectionPage)
        self.loadButton.setObjectName(u"loadButton")

        self.buttons.addWidget(self.loadButton)


        self.root.addLayout(self.buttons)


        self.retranslateUi(SectionPage)

        QMetaObject.connectSlotsByName(SectionPage)
    # setupUi

    def retranslateUi(self, SectionPage):
        self.sectionTitle.setText(QCoreApplication.translate("QWidget", u"\uc601\uc5ed", None))
        self.generateButton.setText(QCoreApplication.translate("QWidget", u"AI \uc0dd\uc131", None))
        self.improveButton.setText(QCoreApplication.translate("QWidget", u"AI \uac1c\uc120", None))
        self.loadButton.setText(QCoreApplication.translate("QWidget", u"DB \ubd88\ub7ec\uc624\uae30", None))
        pass
    # retranslateUi

