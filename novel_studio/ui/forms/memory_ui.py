# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'memory.ui'
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

class Ui_MemoryPage(object):
    def setupUi(self, MemoryPage):
        if not MemoryPage.objectName():
            MemoryPage.setObjectName(u"MemoryPage")
        self.l = QVBoxLayout(MemoryPage)
        self.l.setObjectName(u"l")
        self.hint = QLabel(MemoryPage)
        self.hint.setObjectName(u"hint")

        self.l.addWidget(self.hint)

        self.toolbar = QHBoxLayout()
        self.toolbar.setObjectName(u"toolbar")
        self.refreshMemoryBtn = QPushButton(MemoryPage)
        self.refreshMemoryBtn.setObjectName(u"refreshMemoryBtn")

        self.toolbar.addWidget(self.refreshMemoryBtn)

        self.auditBtn = QPushButton(MemoryPage)
        self.auditBtn.setObjectName(u"auditBtn")

        self.toolbar.addWidget(self.auditBtn)


        self.l.addLayout(self.toolbar)

        self.edit = QPlainTextEdit(MemoryPage)
        self.edit.setObjectName(u"edit")

        self.l.addWidget(self.edit)


        self.retranslateUi(MemoryPage)

        QMetaObject.connectSlotsByName(MemoryPage)
    # setupUi

    def retranslateUi(self, MemoryPage):
        self.hint.setText(QCoreApplication.translate("MemoryPage", u"\ud654\ubcc4 \uae30\uc5b5\uacfc \uc5f0\uc18d\uc131 \uac80\uc0ac \uacb0\uacfc", None))
        self.refreshMemoryBtn.setText(QCoreApplication.translate("MemoryPage", u"\uc7a5\uae30 \uae30\uc5b5 \uc0c8\ub85c\uace0\uce68", None))
        self.auditBtn.setText(QCoreApplication.translate("MemoryPage", u"\uc7a5\ud3b8 \uc815\ubc00 \uc5f0\uc18d\uc131 \uac80\uc0ac", None))
        pass
    # retranslateUi

