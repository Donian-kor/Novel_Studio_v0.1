# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'idea.ui'
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
    def setupUi(self, IdeaView):
        if not IdeaView.objectName():
            IdeaView.setObjectName(u"IdeaView")
        IdeaView.resize(1000, 700)
        self.root = QVBoxLayout(IdeaView)
        self.root.setObjectName(u"root")
        self.pageTitle = QLabel(IdeaView)
        self.pageTitle.setObjectName(u"pageTitle")

        self.root.addWidget(self.pageTitle)

        self.ideaEdit = QPlainTextEdit(IdeaView)
        self.ideaEdit.setObjectName(u"ideaEdit")
        self.ideaEdit.setReadOnly(False)

        self.root.addWidget(self.ideaEdit)

        self.buttons = QHBoxLayout()
        self.buttons.setObjectName(u"buttons")
        self.generateButton = QPushButton(IdeaView)
        self.generateButton.setObjectName(u"generateButton")

        self.buttons.addWidget(self.generateButton)

        self.useButton = QPushButton(IdeaView)
        self.useButton.setObjectName(u"useButton")

        self.buttons.addWidget(self.useButton)


        self.root.addLayout(self.buttons)

        self.hintLabel = QLabel(IdeaView)
        self.hintLabel.setObjectName(u"hintLabel")

        self.root.addWidget(self.hintLabel)


        self.retranslateUi(IdeaView)

        QMetaObject.connectSlotsByName(IdeaView)
    # setupUi

    def retranslateUi(self, IdeaView):
        self.pageTitle.setText(QCoreApplication.translate("QWidget", u"\uc544\uc774\ub514\uc5b4", None))
        self.generateButton.setText(QCoreApplication.translate("QWidget", u"AI \uc544\uc774\ub514\uc5b4 \uc0dd\uc131", None))
        self.useButton.setText(QCoreApplication.translate("QWidget", u"\uc774 \uc544\uc774\ub514\uc5b4 \uc0ac\uc6a9", None))
        self.hintLabel.setText(QCoreApplication.translate("QWidget", u"AI \uc544\uc774\ub514\uc5b4 \uc0dd\uc131\uc740 \ud55c \ubc88\uc5d0 1\uac1c \uc2dc\uc548\uc744 \ubcf4\uc5ec\uc8fc\uba70, \ub2e4\uc2dc \ub204\ub974\uba74 \uc0c8 \uc2dc\uc548\uc73c\ub85c \uad50\uccb4\ud569\ub2c8\ub2e4.", None))
        pass
    # retranslateUi

