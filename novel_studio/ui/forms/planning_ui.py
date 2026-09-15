# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'planning.ui'
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

class Ui_PlanningPage(object):
    def setupUi(self, PlanningPage):
        if not PlanningPage.objectName():
            PlanningPage.setObjectName(u"PlanningPage")
        self.l = QVBoxLayout(PlanningPage)
        self.l.setObjectName(u"l")
        self.ideaHead = QHBoxLayout()
        self.ideaHead.setObjectName(u"ideaHead")
        self.ideaLbl = QLabel(PlanningPage)
        self.ideaLbl.setObjectName(u"ideaLbl")

        self.ideaHead.addWidget(self.ideaLbl)

        self.generateBtn = QPushButton(PlanningPage)
        self.generateBtn.setObjectName(u"generateBtn")

        self.ideaHead.addWidget(self.generateBtn)

        self.useBtn = QPushButton(PlanningPage)
        self.useBtn.setObjectName(u"useBtn")

        self.ideaHead.addWidget(self.useBtn)


        self.l.addLayout(self.ideaHead)

        self.hint = QLabel(PlanningPage)
        self.hint.setObjectName(u"hint")
        self.hint.setWordWrap(True)

        self.l.addWidget(self.hint)

        self.ideaEdit = QPlainTextEdit(PlanningPage)
        self.ideaEdit.setObjectName(u"ideaEdit")

        self.l.addWidget(self.ideaEdit)

        self.mHead = QHBoxLayout()
        self.mHead.setObjectName(u"mHead")
        self.mLbl = QLabel(PlanningPage)
        self.mLbl.setObjectName(u"mLbl")

        self.mHead.addWidget(self.mLbl)

        self.masterBtn = QPushButton(PlanningPage)
        self.masterBtn.setObjectName(u"masterBtn")

        self.mHead.addWidget(self.masterBtn)

        self.saveMasterBtn = QPushButton(PlanningPage)
        self.saveMasterBtn.setObjectName(u"saveMasterBtn")

        self.mHead.addWidget(self.saveMasterBtn)

        self.diffMasterBtn = QPushButton(PlanningPage)
        self.diffMasterBtn.setObjectName(u"diffMasterBtn")

        self.mHead.addWidget(self.diffMasterBtn)


        self.l.addLayout(self.mHead)

        self.masterEdit = QPlainTextEdit(PlanningPage)
        self.masterEdit.setObjectName(u"masterEdit")

        self.l.addWidget(self.masterEdit)

        self.cHead = QHBoxLayout()
        self.cHead.setObjectName(u"cHead")
        self.cLbl = QLabel(PlanningPage)
        self.cLbl.setObjectName(u"cLbl")

        self.cHead.addWidget(self.cLbl)

        self.contractBtn = QPushButton(PlanningPage)
        self.contractBtn.setObjectName(u"contractBtn")

        self.cHead.addWidget(self.contractBtn)

        self.lockBtn = QPushButton(PlanningPage)
        self.lockBtn.setObjectName(u"lockBtn")

        self.cHead.addWidget(self.lockBtn)

        self.saveContractBtn = QPushButton(PlanningPage)
        self.saveContractBtn.setObjectName(u"saveContractBtn")

        self.cHead.addWidget(self.saveContractBtn)


        self.l.addLayout(self.cHead)

        self.contractEdit = QPlainTextEdit(PlanningPage)
        self.contractEdit.setObjectName(u"contractEdit")

        self.l.addWidget(self.contractEdit)

        self.pHead = QHBoxLayout()
        self.pHead.setObjectName(u"pHead")
        self.pLbl = QLabel(PlanningPage)
        self.pLbl.setObjectName(u"pLbl")

        self.pHead.addWidget(self.pLbl)

        self.masterPlotBtn = QPushButton(PlanningPage)
        self.masterPlotBtn.setObjectName(u"masterPlotBtn")

        self.pHead.addWidget(self.masterPlotBtn)

        self.savePlotBtn = QPushButton(PlanningPage)
        self.savePlotBtn.setObjectName(u"savePlotBtn")

        self.pHead.addWidget(self.savePlotBtn)


        self.l.addLayout(self.pHead)

        self.masterPlotEdit = QPlainTextEdit(PlanningPage)
        self.masterPlotEdit.setObjectName(u"masterPlotEdit")

        self.l.addWidget(self.masterPlotEdit)


        self.retranslateUi(PlanningPage)

        QMetaObject.connectSlotsByName(PlanningPage)
    # setupUi

    def retranslateUi(self, PlanningPage):
        self.ideaLbl.setText(QCoreApplication.translate("PlanningPage", u"\uc544\uc774\ub514\uc5b4", None))
        self.generateBtn.setText(QCoreApplication.translate("PlanningPage", u"AI \uc544\uc774\ub514\uc5b4 \uc0dd\uc131", None))
        self.useBtn.setText(QCoreApplication.translate("PlanningPage", u"\uc774 \uc544\uc774\ub514\uc5b4 \uc0ac\uc6a9", None))
        self.hint.setText(QCoreApplication.translate("PlanningPage", u"\uc544\uc774\ub514\uc5b4\uac00 \uc5c6\uc5b4\ub3c4 \ub429\ub2c8\ub2e4. AI \uc544\uc774\ub514\uc5b4 \uc0dd\uc131\uc740 \ud55c \ubc88\uc5d0 \ud558\ub098\uc758 \uc2dc\uc548\ub9cc \ubcf4\uc5ec\uc8fc\uba70 \ub2e4\uc2dc \ub204\ub974\uba74 \uc0c8 \uc2dc\uc548\uc73c\ub85c \uad50\uccb4\ud569\ub2c8\ub2e4. \uc544\ub798\uc5d0 \uc544\uc774\ub514\uc5b4\ub97c \uc801\uace0 [\uc774 \uc544\uc774\ub514\uc5b4 \uc0ac\uc6a9]\uc744 \ub204\ub978 \ub4a4 [AI \ub9c8\uc2a4\ud130 \uae30\ud68d \uc0dd\uc131]\uc73c\ub85c \uc774\uc5b4\uac00\uc138\uc694.", None))
        self.mLbl.setText(QCoreApplication.translate("PlanningPage", u"\ub9c8\uc2a4\ud130 \uae30\ud68d", None))
        self.masterBtn.setText(QCoreApplication.translate("PlanningPage", u"AI \ub9c8\uc2a4\ud130 \uae30\ud68d \uc0dd\uc131", None))
        self.saveMasterBtn.setText(QCoreApplication.translate("PlanningPage", u"\ub9c8\uc2a4\ud130 \uae30\ud68d \uc800\uc7a5", None))
        self.diffMasterBtn.setText(QCoreApplication.translate("PlanningPage", u"\ubcc0\uacbd\uc810 \uac80\uc0ac", None))
        self.cLbl.setText(QCoreApplication.translate("PlanningPage", u"\uc7a5\ud3b8 \ud575\uc2ec \uae30\uc900 (Plan Contract)", None))
        self.contractBtn.setText(QCoreApplication.translate("PlanningPage", u"AI \ud575\uc2ec \uae30\uc900 \ucd94\ucd9c", None))
        self.lockBtn.setText(QCoreApplication.translate("PlanningPage", u"\ud575\uc2ec \uae30\uc900 \uc7a0\uae08", None))
        self.saveContractBtn.setText(QCoreApplication.translate("PlanningPage", u"\ud575\uc2ec \uae30\uc900 \uc800\uc7a5", None))
        self.pLbl.setText(QCoreApplication.translate("PlanningPage", u"\uc804\uccb4 \ud50c\ub86f (\ub9c8\uc2a4\ud130 \ud50c\ub86f)", None))
        self.masterPlotBtn.setText(QCoreApplication.translate("PlanningPage", u"AI \uc804\uccb4 \ud50c\ub86f \uc0dd\uc131", None))
        self.savePlotBtn.setText(QCoreApplication.translate("PlanningPage", u"\uc804\uccb4 \ud50c\ub86f \uc800\uc7a5", None))
        pass
    # retranslateUi

