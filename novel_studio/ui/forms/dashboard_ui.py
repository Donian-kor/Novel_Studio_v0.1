# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dashboard.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_DashboardPage(object):
    def setupUi(self, DashboardPage):
        if not DashboardPage.objectName():
            DashboardPage.setObjectName(u"DashboardPage")
        self.l = QVBoxLayout(DashboardPage)
        self.l.setObjectName(u"l")
        self.title = QLabel(DashboardPage)
        self.title.setObjectName(u"title")

        self.l.addWidget(self.title)

        self.summaryLabel = QLabel(DashboardPage)
        self.summaryLabel.setObjectName(u"summaryLabel")
        self.summaryLabel.setWordWrap(True)

        self.l.addWidget(self.summaryLabel)

        self.spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.l.addItem(self.spacer)


        self.retranslateUi(DashboardPage)

        QMetaObject.connectSlotsByName(DashboardPage)
    # setupUi

    def retranslateUi(self, DashboardPage):
        self.title.setText(QCoreApplication.translate("DashboardPage", u"\ub300\uc2dc\ubcf4\ub4dc", None))
        self.summaryLabel.setText(QCoreApplication.translate("DashboardPage", u"\uc791\ud488 \uc815\ubcf4\ub97c \ubd88\ub7ec\uc624\ub294 \uc911...", None))
        pass
    # retranslateUi

