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
from PySide6.QtWidgets import (QApplication, QLabel, QSizePolicy, QTabWidget,
    QVBoxLayout, QWidget)

class Ui_QWidget(object):
    def setupUi(self, SectionsView):
        if not SectionsView.objectName():
            SectionsView.setObjectName(u"SectionsView")
        SectionsView.resize(1000, 700)
        self.root = QVBoxLayout(SectionsView)
        self.root.setObjectName(u"root")
        self.pageTitle = QLabel(SectionsView)
        self.pageTitle.setObjectName(u"pageTitle")

        self.root.addWidget(self.pageTitle)

        self.hintLabel = QLabel(SectionsView)
        self.hintLabel.setObjectName(u"hintLabel")

        self.root.addWidget(self.hintLabel)

        self.sectionTabs = QTabWidget(SectionsView)
        self.sectionTabs.setObjectName(u"sectionTabs")

        self.root.addWidget(self.sectionTabs)


        self.retranslateUi(SectionsView)

        QMetaObject.connectSlotsByName(SectionsView)
    # setupUi

    def retranslateUi(self, SectionsView):
        self.pageTitle.setText(QCoreApplication.translate("QWidget", u"\uc124\uc815 \uc790\ub3d9 \uc0dd\uc131", None))
        self.hintLabel.setText(QCoreApplication.translate("QWidget", u"\ub9c8\uc2a4\ud130 \uae30\ud68d\uc5d0\uc11c \ucd08\uc548\uc744 \uac00\uc838\uc628 \ub4a4 \uac01 \uc601\uc5ed\uc744 AI\ub85c \uc0dd\uc131\u00b7\ud655\uc7a5\u00b7\uac1c\uc120\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.", None))
        pass
    # retranslateUi

