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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_PlanningPage(object):
    def setupUi(self, PlanningPage):
        if not PlanningPage.objectName():
            PlanningPage.setObjectName(u"PlanningPage")
        self.l = QVBoxLayout(PlanningPage)
        self.l.setSpacing(10)
        self.l.setObjectName(u"l")
        self.l.setContentsMargins(10, 10, 10, 10)
        self.pageHeader = QHBoxLayout()
        self.pageHeader.setObjectName(u"pageHeader")
        self.pageTitle = QLabel(PlanningPage)
        self.pageTitle.setObjectName(u"pageTitle")

        self.pageHeader.addWidget(self.pageTitle)

        self.spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.pageHeader.addItem(self.spacer)

        self.pageHint = QLabel(PlanningPage)
        self.pageHint.setObjectName(u"pageHint")

        self.pageHeader.addWidget(self.pageHint)


        self.l.addLayout(self.pageHeader)

        self.cardGrid = QGridLayout()
        self.cardGrid.setObjectName(u"cardGrid")
        self.cardGrid.setHorizontalSpacing(10)
        self.cardGrid.setVerticalSpacing(10)
        self.ideaCard = QFrame(PlanningPage)
        self.ideaCard.setObjectName(u"ideaCard")
        self.ideaCard.setFrameShape(QFrame.Shape.StyledPanel)
        self.ideaLayout = QVBoxLayout(self.ideaCard)
        self.ideaLayout.setObjectName(u"ideaLayout")
        self.ideaHead = QHBoxLayout()
        self.ideaHead.setObjectName(u"ideaHead")
        self.ideaLbl = QLabel(self.ideaCard)
        self.ideaLbl.setObjectName(u"ideaLbl")

        self.ideaHead.addWidget(self.ideaLbl)

        self.s1 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.ideaHead.addItem(self.s1)

        self.generateBtn = QPushButton(self.ideaCard)
        self.generateBtn.setObjectName(u"generateBtn")

        self.ideaHead.addWidget(self.generateBtn)

        self.useBtn = QPushButton(self.ideaCard)
        self.useBtn.setObjectName(u"useBtn")

        self.ideaHead.addWidget(self.useBtn)


        self.ideaLayout.addLayout(self.ideaHead)

        self.hint = QLabel(self.ideaCard)
        self.hint.setObjectName(u"hint")
        self.hint.setWordWrap(True)

        self.ideaLayout.addWidget(self.hint)

        self.ideaEdit = QPlainTextEdit(self.ideaCard)
        self.ideaEdit.setObjectName(u"ideaEdit")

        self.ideaLayout.addWidget(self.ideaEdit)


        self.cardGrid.addWidget(self.ideaCard, 0, 0, 1, 1)

        self.masterCard = QFrame(PlanningPage)
        self.masterCard.setObjectName(u"masterCard")
        self.masterCard.setFrameShape(QFrame.Shape.StyledPanel)
        self.masterLayout = QVBoxLayout(self.masterCard)
        self.masterLayout.setObjectName(u"masterLayout")
        self.mHead = QHBoxLayout()
        self.mHead.setObjectName(u"mHead")
        self.mLbl = QLabel(self.masterCard)
        self.mLbl.setObjectName(u"mLbl")

        self.mHead.addWidget(self.mLbl)

        self.s2 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.mHead.addItem(self.s2)

        self.masterBtn = QPushButton(self.masterCard)
        self.masterBtn.setObjectName(u"masterBtn")

        self.mHead.addWidget(self.masterBtn)

        self.saveMasterBtn = QPushButton(self.masterCard)
        self.saveMasterBtn.setObjectName(u"saveMasterBtn")

        self.mHead.addWidget(self.saveMasterBtn)

        self.diffMasterBtn = QPushButton(self.masterCard)
        self.diffMasterBtn.setObjectName(u"diffMasterBtn")

        self.mHead.addWidget(self.diffMasterBtn)


        self.masterLayout.addLayout(self.mHead)

        self.masterEdit = QPlainTextEdit(self.masterCard)
        self.masterEdit.setObjectName(u"masterEdit")

        self.masterLayout.addWidget(self.masterEdit)


        self.cardGrid.addWidget(self.masterCard, 0, 1, 1, 1)

        self.contractCard = QFrame(PlanningPage)
        self.contractCard.setObjectName(u"contractCard")
        self.contractCard.setFrameShape(QFrame.Shape.StyledPanel)
        self.contractLayout = QVBoxLayout(self.contractCard)
        self.contractLayout.setObjectName(u"contractLayout")
        self.cHead = QHBoxLayout()
        self.cHead.setObjectName(u"cHead")
        self.cLbl = QLabel(self.contractCard)
        self.cLbl.setObjectName(u"cLbl")

        self.cHead.addWidget(self.cLbl)

        self.s3 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.cHead.addItem(self.s3)

        self.contractBtn = QPushButton(self.contractCard)
        self.contractBtn.setObjectName(u"contractBtn")

        self.cHead.addWidget(self.contractBtn)

        self.lockBtn = QPushButton(self.contractCard)
        self.lockBtn.setObjectName(u"lockBtn")

        self.cHead.addWidget(self.lockBtn)

        self.saveContractBtn = QPushButton(self.contractCard)
        self.saveContractBtn.setObjectName(u"saveContractBtn")

        self.cHead.addWidget(self.saveContractBtn)


        self.contractLayout.addLayout(self.cHead)

        self.contractEdit = QPlainTextEdit(self.contractCard)
        self.contractEdit.setObjectName(u"contractEdit")

        self.contractLayout.addWidget(self.contractEdit)


        self.cardGrid.addWidget(self.contractCard, 1, 0, 1, 1)

        self.plotCard = QFrame(PlanningPage)
        self.plotCard.setObjectName(u"plotCard")
        self.plotCard.setFrameShape(QFrame.Shape.StyledPanel)
        self.plotLayout = QVBoxLayout(self.plotCard)
        self.plotLayout.setObjectName(u"plotLayout")
        self.pHead = QHBoxLayout()
        self.pHead.setObjectName(u"pHead")
        self.pLbl = QLabel(self.plotCard)
        self.pLbl.setObjectName(u"pLbl")

        self.pHead.addWidget(self.pLbl)

        self.s4 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.pHead.addItem(self.s4)

        self.masterPlotBtn = QPushButton(self.plotCard)
        self.masterPlotBtn.setObjectName(u"masterPlotBtn")

        self.pHead.addWidget(self.masterPlotBtn)

        self.savePlotBtn = QPushButton(self.plotCard)
        self.savePlotBtn.setObjectName(u"savePlotBtn")

        self.pHead.addWidget(self.savePlotBtn)


        self.plotLayout.addLayout(self.pHead)

        self.masterPlotEdit = QPlainTextEdit(self.plotCard)
        self.masterPlotEdit.setObjectName(u"masterPlotEdit")

        self.plotLayout.addWidget(self.masterPlotEdit)


        self.cardGrid.addWidget(self.plotCard, 1, 1, 1, 1)


        self.l.addLayout(self.cardGrid)


        self.retranslateUi(PlanningPage)

        QMetaObject.connectSlotsByName(PlanningPage)
    # setupUi

    def retranslateUi(self, PlanningPage):
        self.pageTitle.setText(QCoreApplication.translate("PlanningPage", u"\uae30\ud68d \uc6cc\ud06c\uc2a4\ud398\uc774\uc2a4", None))
        self.pageHint.setText(QCoreApplication.translate("PlanningPage", u"\uc774\uc57c\uae30 \uc544\uc774\ub514\uc5b4 \u2192 \uc18c\uc124 \uc124\uacc4 \u2192 \uc791\ud488 \uaddc\uce59 \u2192 \uc804\uccb4 \uc904\uac70\ub9ac", None))
        self.ideaLbl.setText(QCoreApplication.translate("PlanningPage", u"\u2460 \uc774\uc57c\uae30 \uc544\uc774\ub514\uc5b4", None))
        self.generateBtn.setText(QCoreApplication.translate("PlanningPage", u"AI \uc544\uc774\ub514\uc5b4 \uc0dd\uc131", None))
        self.useBtn.setText(QCoreApplication.translate("PlanningPage", u"\uc774 \uc544\uc774\ub514\uc5b4 \uc0ac\uc6a9", None))
        self.hint.setText(QCoreApplication.translate("PlanningPage", u"\ucd08\uc548\uc744 \ub9cc\ub4e4\uace0 \ud655\uc815\ud55c \ub4a4 \ub2e4\uc74c \ub2e8\uacc4\ub85c \uc774\ub3d9\ud569\ub2c8\ub2e4.", None))
        self.mLbl.setText(QCoreApplication.translate("PlanningPage", u"\u2461 \uc18c\uc124 \uc124\uacc4", None))
        self.masterBtn.setText(QCoreApplication.translate("PlanningPage", u"AI \uc18c\uc124 \uc124\uacc4 \uc0dd\uc131", None))
        self.saveMasterBtn.setText(QCoreApplication.translate("PlanningPage", u"\uc800\uc7a5", None))
        self.diffMasterBtn.setText(QCoreApplication.translate("PlanningPage", u"\ubcc0\uacbd\uc810 \uac80\uc0ac", None))
        self.cLbl.setText(QCoreApplication.translate("PlanningPage", u"\u2462 \uc791\ud488 \uaddc\uce59", None))
        self.contractBtn.setText(QCoreApplication.translate("PlanningPage", u"AI \uc791\ud488 \uaddc\uce59 \ucd94\ucd9c", None))
        self.lockBtn.setText(QCoreApplication.translate("PlanningPage", u"\uc7a0\uae08", None))
        self.saveContractBtn.setText(QCoreApplication.translate("PlanningPage", u"\uc800\uc7a5", None))
        self.pLbl.setText(QCoreApplication.translate("PlanningPage", u"\u2463 \uc804\uccb4 \uc904\uac70\ub9ac", None))
        self.masterPlotBtn.setText(QCoreApplication.translate("PlanningPage", u"AI \uc804\uccb4 \uc904\uac70\ub9ac \uc0dd\uc131", None))
        self.savePlotBtn.setText(QCoreApplication.translate("PlanningPage", u"\uc800\uc7a5", None))
        pass
    # retranslateUi

