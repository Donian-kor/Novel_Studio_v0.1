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

class Ui_IdeaPage(object):
    def setupUi(self, IdeaPage):
        if not IdeaPage.objectName():
            IdeaPage.setObjectName(u"IdeaPage")
        self.l = QVBoxLayout(IdeaPage)
        self.l.setObjectName(u"l")
        self.title = QLabel(IdeaPage)
        self.title.setObjectName(u"title")

        self.l.addWidget(self.title)

        self.hint = QLabel(IdeaPage)
        self.hint.setObjectName(u"hint")

        self.l.addWidget(self.hint)

        self.ideaEdit = QPlainTextEdit(IdeaPage)
        self.ideaEdit.setObjectName(u"ideaEdit")

        self.l.addWidget(self.ideaEdit)

        self.a = QHBoxLayout()
        self.a.setObjectName(u"a")
        self.generateBtn = QPushButton(IdeaPage)
        self.generateBtn.setObjectName(u"generateBtn")

        self.a.addWidget(self.generateBtn)

        self.useBtn = QPushButton(IdeaPage)
        self.useBtn.setObjectName(u"useBtn")

        self.a.addWidget(self.useBtn)


        self.l.addLayout(self.a)


        self.retranslateUi(IdeaPage)

        QMetaObject.connectSlotsByName(IdeaPage)
    # setupUi

    def retranslateUi(self, IdeaPage):
        self.title.setText(QCoreApplication.translate("IdeaPage", u"\uc544\uc774\ub514\uc5b4", None))
        self.hint.setText(QCoreApplication.translate("IdeaPage", u"\uc544\uc774\ub514\uc5b4\uac00 \uc5c6\uc5b4\ub3c4 \ub429\ub2c8\ub2e4. AI \uc544\uc774\ub514\uc5b4 \uc0dd\uc131\uc740 \ud55c \ubc88\uc5d0 \ud558\ub098\uc758 \uc2dc\uc548\ub9cc \ubcf4\uc5ec\uc8fc\uba70 \ub2e4\uc2dc \ub204\ub974\uba74 \uc0c8 \uc2dc\uc548\uc73c\ub85c \uad50\uccb4\ud569\ub2c8\ub2e4.", None))
        self.generateBtn.setText(QCoreApplication.translate("IdeaPage", u"AI \uc544\uc774\ub514\uc5b4 \uc0dd\uc131", None))
        self.useBtn.setText(QCoreApplication.translate("IdeaPage", u"\uc774 \uc544\uc774\ub514\uc5b4 \uc0ac\uc6a9", None))
        pass
    # retranslateUi

