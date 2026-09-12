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

class Ui_QWidget(object):
    def setupUi(self, PlanningView):
        if not PlanningView.objectName():
            PlanningView.setObjectName(u"PlanningView")
        PlanningView.resize(1000, 700)
        self.root = QVBoxLayout(PlanningView)
        self.root.setObjectName(u"root")
        self.pageTitle = QLabel(PlanningView)
        self.pageTitle.setObjectName(u"pageTitle")

        self.root.addWidget(self.pageTitle)

        self.ideaLabel = QLabel(PlanningView)
        self.ideaLabel.setObjectName(u"ideaLabel")

        self.root.addWidget(self.ideaLabel)

        self.ideaEdit = QPlainTextEdit(PlanningView)
        self.ideaEdit.setObjectName(u"ideaEdit")
        self.ideaEdit.setReadOnly(False)

        self.root.addWidget(self.ideaEdit)

        self.b1 = QHBoxLayout()
        self.b1.setObjectName(u"b1")
        self.ideaButton = QPushButton(PlanningView)
        self.ideaButton.setObjectName(u"ideaButton")

        self.b1.addWidget(self.ideaButton)

        self.useIdeaButton = QPushButton(PlanningView)
        self.useIdeaButton.setObjectName(u"useIdeaButton")

        self.b1.addWidget(self.useIdeaButton)

        self.masterButton = QPushButton(PlanningView)
        self.masterButton.setObjectName(u"masterButton")

        self.b1.addWidget(self.masterButton)

        self.allSectionsButton = QPushButton(PlanningView)
        self.allSectionsButton.setObjectName(u"allSectionsButton")

        self.b1.addWidget(self.allSectionsButton)


        self.root.addLayout(self.b1)

        self.masterLabel = QLabel(PlanningView)
        self.masterLabel.setObjectName(u"masterLabel")

        self.root.addWidget(self.masterLabel)

        self.masterEdit = QPlainTextEdit(PlanningView)
        self.masterEdit.setObjectName(u"masterEdit")
        self.masterEdit.setReadOnly(False)

        self.root.addWidget(self.masterEdit)

        self.b2 = QHBoxLayout()
        self.b2.setObjectName(u"b2")
        self.saveMasterButton = QPushButton(PlanningView)
        self.saveMasterButton.setObjectName(u"saveMasterButton")

        self.b2.addWidget(self.saveMasterButton)

        self.contractButton = QPushButton(PlanningView)
        self.contractButton.setObjectName(u"contractButton")

        self.b2.addWidget(self.contractButton)

        self.lockContractButton = QPushButton(PlanningView)
        self.lockContractButton.setObjectName(u"lockContractButton")

        self.b2.addWidget(self.lockContractButton)

        self.masterPlotButton = QPushButton(PlanningView)
        self.masterPlotButton.setObjectName(u"masterPlotButton")

        self.b2.addWidget(self.masterPlotButton)

        self.savePlotButton = QPushButton(PlanningView)
        self.savePlotButton.setObjectName(u"savePlotButton")

        self.b2.addWidget(self.savePlotButton)


        self.root.addLayout(self.b2)

        self.contractLabel = QLabel(PlanningView)
        self.contractLabel.setObjectName(u"contractLabel")

        self.root.addWidget(self.contractLabel)

        self.contractEdit = QPlainTextEdit(PlanningView)
        self.contractEdit.setObjectName(u"contractEdit")
        self.contractEdit.setReadOnly(False)

        self.root.addWidget(self.contractEdit)

        self.plotLabel = QLabel(PlanningView)
        self.plotLabel.setObjectName(u"plotLabel")

        self.root.addWidget(self.plotLabel)

        self.masterPlotEdit = QPlainTextEdit(PlanningView)
        self.masterPlotEdit.setObjectName(u"masterPlotEdit")
        self.masterPlotEdit.setReadOnly(False)

        self.root.addWidget(self.masterPlotEdit)


        self.retranslateUi(PlanningView)

        QMetaObject.connectSlotsByName(PlanningView)
    # setupUi

    def retranslateUi(self, PlanningView):
        self.pageTitle.setText(QCoreApplication.translate("QWidget", u"AI \ub9c8\uc2a4\ud130 \uae30\ud68d", None))
        self.ideaLabel.setText(QCoreApplication.translate("QWidget", u"\ud604\uc7ac \uc544\uc774\ub514\uc5b4", None))
        self.ideaButton.setText(QCoreApplication.translate("QWidget", u"AI \uc544\uc774\ub514\uc5b4 \uc0dd\uc131", None))
        self.useIdeaButton.setText(QCoreApplication.translate("QWidget", u"\uc544\uc774\ub514\uc5b4 \uc801\uc6a9", None))
        self.masterButton.setText(QCoreApplication.translate("QWidget", u"AI \ub9c8\uc2a4\ud130 \uae30\ud68d", None))
        self.allSectionsButton.setText(QCoreApplication.translate("QWidget", u"AI \uc804\uccb4 \uc124\uc815 \uc790\ub3d9 \uc0dd\uc131", None))
        self.masterLabel.setText(QCoreApplication.translate("QWidget", u"\ub9c8\uc2a4\ud130 \uae30\ud68d", None))
        self.saveMasterButton.setText(QCoreApplication.translate("QWidget", u"\ub9c8\uc2a4\ud130 \uae30\ud68d \uc800\uc7a5", None))
        self.contractButton.setText(QCoreApplication.translate("QWidget", u"AI Contract \ucd94\ucd9c", None))
        self.lockContractButton.setText(QCoreApplication.translate("QWidget", u"Contract \uc2b9\uc778/\uc7a0\uae08", None))
        self.masterPlotButton.setText(QCoreApplication.translate("QWidget", u"AI \uc804\uccb4 \ud50c\ub86f \uc0dd\uc131", None))
        self.savePlotButton.setText(QCoreApplication.translate("QWidget", u"\uc804\uccb4 \ud50c\ub86f \uc800\uc7a5", None))
        self.contractLabel.setText(QCoreApplication.translate("QWidget", u"Plan Contract", None))
        self.plotLabel.setText(QCoreApplication.translate("QWidget", u"\uc804\uccb4 \ub9c8\uc2a4\ud130 \ud50c\ub86f", None))
        pass
    # retranslateUi

