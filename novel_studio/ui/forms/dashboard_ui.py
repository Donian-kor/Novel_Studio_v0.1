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
from PySide6.QtWidgets import (QApplication, QLabel, QPlainTextEdit, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_QWidget(object):
    def setupUi(self, DashboardView):
        if not DashboardView.objectName():
            DashboardView.setObjectName(u"DashboardView")
        DashboardView.resize(1000, 700)
        self.root = QVBoxLayout(DashboardView)
        self.root.setObjectName(u"root")
        self.pageTitle = QLabel(DashboardView)
        self.pageTitle.setObjectName(u"pageTitle")

        self.root.addWidget(self.pageTitle)

        self.dashboardText = QPlainTextEdit(DashboardView)
        self.dashboardText.setObjectName(u"dashboardText")
        self.dashboardText.setReadOnly(True)

        self.root.addWidget(self.dashboardText)


        self.retranslateUi(DashboardView)

        QMetaObject.connectSlotsByName(DashboardView)
    # setupUi

    def retranslateUi(self, DashboardView):
        self.pageTitle.setText(QCoreApplication.translate("QWidget", u"\ub300\uc2dc\ubcf4\ub4dc", None))
        pass
    # retranslateUi

