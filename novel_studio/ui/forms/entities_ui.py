# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'entities.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpinBox, QSplitter,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget)

class Ui_EntitiesPage(object):
    def setupUi(self, EntitiesPage):
        if not EntitiesPage.objectName():
            EntitiesPage.setObjectName(u"EntitiesPage")
        self.l = QHBoxLayout(EntitiesPage)
        self.l.setObjectName(u"l")
        self.entitiesSplitter = QSplitter(EntitiesPage)
        self.entitiesSplitter.setObjectName(u"entitiesSplitter")
        self.entitiesSplitter.setOrientation(Qt.Horizontal)
        self.entitiesSplitter.setChildrenCollapsible(False)
        self.entitiesSplitter.setHandleWidth(9)
        self.entitiesLeft = QWidget(self.entitiesSplitter)
        self.entitiesLeft.setObjectName(u"entitiesLeft")
        self.left = QVBoxLayout(self.entitiesLeft)
        self.left.setObjectName(u"left")
        self.left.setContentsMargins(0, 0, 0, 0)
        self.catLbl = QLabel(self.entitiesLeft)
        self.catLbl.setObjectName(u"catLbl")

        self.left.addWidget(self.catLbl)

        self.catCombo = QComboBox(self.entitiesLeft)
        self.catCombo.setObjectName(u"catCombo")

        self.left.addWidget(self.catCombo)

        self.entryList = QListWidget(self.entitiesLeft)
        self.entryList.setObjectName(u"entryList")

        self.left.addWidget(self.entryList)

        self.addRow = QHBoxLayout()
        self.addRow.setObjectName(u"addRow")
        self.addBtn = QPushButton(self.entitiesLeft)
        self.addBtn.setObjectName(u"addBtn")

        self.addRow.addWidget(self.addBtn)

        self.delBtn = QPushButton(self.entitiesLeft)
        self.delBtn.setObjectName(u"delBtn")

        self.addRow.addWidget(self.delBtn)


        self.left.addLayout(self.addRow)

        self.entitiesSplitter.addWidget(self.entitiesLeft)
        self.entitiesRight = QWidget(self.entitiesSplitter)
        self.entitiesRight.setObjectName(u"entitiesRight")
        self.right = QVBoxLayout(self.entitiesRight)
        self.right.setObjectName(u"right")
        self.right.setContentsMargins(0, 0, 0, 0)
        self.head = QHBoxLayout()
        self.head.setObjectName(u"head")
        self.nameLbl = QLabel(self.entitiesRight)
        self.nameLbl.setObjectName(u"nameLbl")

        self.head.addWidget(self.nameLbl)

        self.nameEdit = QLineEdit(self.entitiesRight)
        self.nameEdit.setObjectName(u"nameEdit")

        self.head.addWidget(self.nameEdit)

        self.generateBtn = QPushButton(self.entitiesRight)
        self.generateBtn.setObjectName(u"generateBtn")

        self.head.addWidget(self.generateBtn)

        self.saveBtn = QPushButton(self.entitiesRight)
        self.saveBtn.setObjectName(u"saveBtn")

        self.head.addWidget(self.saveBtn)


        self.right.addLayout(self.head)

        self.formStack = QStackedWidget(self.entitiesRight)
        self.formStack.setObjectName(u"formStack")
        self.characterPage = QWidget()
        self.characterPage.setObjectName(u"characterPage")
        self.characterForm = QFormLayout(self.characterPage)
        self.characterForm.setObjectName(u"characterForm")
        self.characterNameLabel = QLabel(self.characterPage)
        self.characterNameLabel.setObjectName(u"characterNameLabel")

        self.characterForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.characterNameLabel)

        self.characterNameEdit = QLineEdit(self.characterPage)
        self.characterNameEdit.setObjectName(u"characterNameEdit")

        self.characterForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.characterNameEdit)

        self.characterRoleLabel = QLabel(self.characterPage)
        self.characterRoleLabel.setObjectName(u"characterRoleLabel")

        self.characterForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.characterRoleLabel)

        self.characterRoleEdit = QLineEdit(self.characterPage)
        self.characterRoleEdit.setObjectName(u"characterRoleEdit")

        self.characterForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.characterRoleEdit)

        self.characterProfileLabel = QLabel(self.characterPage)
        self.characterProfileLabel.setObjectName(u"characterProfileLabel")

        self.characterForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.characterProfileLabel)

        self.characterProfileEdit = QTextEdit(self.characterPage)
        self.characterProfileEdit.setObjectName(u"characterProfileEdit")
        self.characterProfileEdit.setMaximumHeight(120)

        self.characterForm.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.characterProfileEdit)

        self.characterPersonalityLabel = QLabel(self.characterPage)
        self.characterPersonalityLabel.setObjectName(u"characterPersonalityLabel")

        self.characterForm.setWidget(3, QFormLayout.ItemRole.LabelRole, self.characterPersonalityLabel)

        self.characterPersonalityEdit = QTextEdit(self.characterPage)
        self.characterPersonalityEdit.setObjectName(u"characterPersonalityEdit")
        self.characterPersonalityEdit.setMaximumHeight(120)

        self.characterForm.setWidget(3, QFormLayout.ItemRole.SpanningRole, self.characterPersonalityEdit)

        self.characterSpeechStyleLabel = QLabel(self.characterPage)
        self.characterSpeechStyleLabel.setObjectName(u"characterSpeechStyleLabel")

        self.characterForm.setWidget(4, QFormLayout.ItemRole.LabelRole, self.characterSpeechStyleLabel)

        self.characterSpeechStyleEdit = QTextEdit(self.characterPage)
        self.characterSpeechStyleEdit.setObjectName(u"characterSpeechStyleEdit")
        self.characterSpeechStyleEdit.setMaximumHeight(120)

        self.characterForm.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.characterSpeechStyleEdit)

        self.characterGoalLabel = QLabel(self.characterPage)
        self.characterGoalLabel.setObjectName(u"characterGoalLabel")

        self.characterForm.setWidget(5, QFormLayout.ItemRole.LabelRole, self.characterGoalLabel)

        self.characterGoalEdit = QTextEdit(self.characterPage)
        self.characterGoalEdit.setObjectName(u"characterGoalEdit")
        self.characterGoalEdit.setMaximumHeight(120)

        self.characterForm.setWidget(5, QFormLayout.ItemRole.SpanningRole, self.characterGoalEdit)

        self.characterSecretLabel = QLabel(self.characterPage)
        self.characterSecretLabel.setObjectName(u"characterSecretLabel")

        self.characterForm.setWidget(6, QFormLayout.ItemRole.LabelRole, self.characterSecretLabel)

        self.characterSecretEdit = QTextEdit(self.characterPage)
        self.characterSecretEdit.setObjectName(u"characterSecretEdit")
        self.characterSecretEdit.setMaximumHeight(120)

        self.characterForm.setWidget(6, QFormLayout.ItemRole.SpanningRole, self.characterSecretEdit)

        self.characterArcLabel = QLabel(self.characterPage)
        self.characterArcLabel.setObjectName(u"characterArcLabel")

        self.characterForm.setWidget(7, QFormLayout.ItemRole.LabelRole, self.characterArcLabel)

        self.characterArcEdit = QTextEdit(self.characterPage)
        self.characterArcEdit.setObjectName(u"characterArcEdit")
        self.characterArcEdit.setMaximumHeight(120)

        self.characterForm.setWidget(7, QFormLayout.ItemRole.SpanningRole, self.characterArcEdit)

        self.formStack.addWidget(self.characterPage)
        self.factionPage = QWidget()
        self.factionPage.setObjectName(u"factionPage")
        self.factionForm = QFormLayout(self.factionPage)
        self.factionForm.setObjectName(u"factionForm")
        self.factionNameLabel = QLabel(self.factionPage)
        self.factionNameLabel.setObjectName(u"factionNameLabel")

        self.factionForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.factionNameLabel)

        self.factionNameEdit = QLineEdit(self.factionPage)
        self.factionNameEdit.setObjectName(u"factionNameEdit")

        self.factionForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.factionNameEdit)

        self.factionCategoryLabel = QLabel(self.factionPage)
        self.factionCategoryLabel.setObjectName(u"factionCategoryLabel")

        self.factionForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.factionCategoryLabel)

        self.factionCategoryEdit = QLineEdit(self.factionPage)
        self.factionCategoryEdit.setObjectName(u"factionCategoryEdit")
        self.factionCategoryEdit.setReadOnly(True)

        self.factionForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.factionCategoryEdit)

        self.factionDescriptionLabel = QLabel(self.factionPage)
        self.factionDescriptionLabel.setObjectName(u"factionDescriptionLabel")

        self.factionForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.factionDescriptionLabel)

        self.factionDescriptionEdit = QTextEdit(self.factionPage)
        self.factionDescriptionEdit.setObjectName(u"factionDescriptionEdit")
        self.factionDescriptionEdit.setMaximumHeight(120)

        self.factionForm.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.factionDescriptionEdit)

        self.factionRulesLabel = QLabel(self.factionPage)
        self.factionRulesLabel.setObjectName(u"factionRulesLabel")

        self.factionForm.setWidget(3, QFormLayout.ItemRole.LabelRole, self.factionRulesLabel)

        self.factionRulesEdit = QTextEdit(self.factionPage)
        self.factionRulesEdit.setObjectName(u"factionRulesEdit")
        self.factionRulesEdit.setMaximumHeight(120)

        self.factionForm.setWidget(3, QFormLayout.ItemRole.SpanningRole, self.factionRulesEdit)

        self.formStack.addWidget(self.factionPage)
        self.locationPage = QWidget()
        self.locationPage.setObjectName(u"locationPage")
        self.locationForm = QFormLayout(self.locationPage)
        self.locationForm.setObjectName(u"locationForm")
        self.locationNameLabel = QLabel(self.locationPage)
        self.locationNameLabel.setObjectName(u"locationNameLabel")

        self.locationForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.locationNameLabel)

        self.locationNameEdit = QLineEdit(self.locationPage)
        self.locationNameEdit.setObjectName(u"locationNameEdit")

        self.locationForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.locationNameEdit)

        self.locationCategoryLabel = QLabel(self.locationPage)
        self.locationCategoryLabel.setObjectName(u"locationCategoryLabel")

        self.locationForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.locationCategoryLabel)

        self.locationCategoryEdit = QLineEdit(self.locationPage)
        self.locationCategoryEdit.setObjectName(u"locationCategoryEdit")
        self.locationCategoryEdit.setReadOnly(True)

        self.locationForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.locationCategoryEdit)

        self.locationDescriptionLabel = QLabel(self.locationPage)
        self.locationDescriptionLabel.setObjectName(u"locationDescriptionLabel")

        self.locationForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.locationDescriptionLabel)

        self.locationDescriptionEdit = QTextEdit(self.locationPage)
        self.locationDescriptionEdit.setObjectName(u"locationDescriptionEdit")
        self.locationDescriptionEdit.setMaximumHeight(120)

        self.locationForm.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.locationDescriptionEdit)

        self.locationRulesLabel = QLabel(self.locationPage)
        self.locationRulesLabel.setObjectName(u"locationRulesLabel")

        self.locationForm.setWidget(3, QFormLayout.ItemRole.LabelRole, self.locationRulesLabel)

        self.locationRulesEdit = QTextEdit(self.locationPage)
        self.locationRulesEdit.setObjectName(u"locationRulesEdit")
        self.locationRulesEdit.setMaximumHeight(120)

        self.locationForm.setWidget(3, QFormLayout.ItemRole.SpanningRole, self.locationRulesEdit)

        self.formStack.addWidget(self.locationPage)
        self.foreshadowPage = QWidget()
        self.foreshadowPage.setObjectName(u"foreshadowPage")
        self.foreshadowForm = QFormLayout(self.foreshadowPage)
        self.foreshadowForm.setObjectName(u"foreshadowForm")
        self.foreshadowCodeLabel = QLabel(self.foreshadowPage)
        self.foreshadowCodeLabel.setObjectName(u"foreshadowCodeLabel")

        self.foreshadowForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.foreshadowCodeLabel)

        self.foreshadowCodeEdit = QLineEdit(self.foreshadowPage)
        self.foreshadowCodeEdit.setObjectName(u"foreshadowCodeEdit")

        self.foreshadowForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.foreshadowCodeEdit)

        self.foreshadowTitleLabel = QLabel(self.foreshadowPage)
        self.foreshadowTitleLabel.setObjectName(u"foreshadowTitleLabel")

        self.foreshadowForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.foreshadowTitleLabel)

        self.foreshadowTitleEdit = QLineEdit(self.foreshadowPage)
        self.foreshadowTitleEdit.setObjectName(u"foreshadowTitleEdit")

        self.foreshadowForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.foreshadowTitleEdit)

        self.foreshadowFirstChapterLabel = QLabel(self.foreshadowPage)
        self.foreshadowFirstChapterLabel.setObjectName(u"foreshadowFirstChapterLabel")

        self.foreshadowForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.foreshadowFirstChapterLabel)

        self.foreshadowFirstChapterSpin = QSpinBox(self.foreshadowPage)
        self.foreshadowFirstChapterSpin.setObjectName(u"foreshadowFirstChapterSpin")
        self.foreshadowFirstChapterSpin.setMinimum(0)
        self.foreshadowFirstChapterSpin.setMaximum(9999)

        self.foreshadowForm.setWidget(2, QFormLayout.ItemRole.FieldRole, self.foreshadowFirstChapterSpin)

        self.foreshadowRevealChapterLabel = QLabel(self.foreshadowPage)
        self.foreshadowRevealChapterLabel.setObjectName(u"foreshadowRevealChapterLabel")

        self.foreshadowForm.setWidget(3, QFormLayout.ItemRole.LabelRole, self.foreshadowRevealChapterLabel)

        self.foreshadowRevealChapterSpin = QSpinBox(self.foreshadowPage)
        self.foreshadowRevealChapterSpin.setObjectName(u"foreshadowRevealChapterSpin")
        self.foreshadowRevealChapterSpin.setMinimum(0)
        self.foreshadowRevealChapterSpin.setMaximum(9999)

        self.foreshadowForm.setWidget(3, QFormLayout.ItemRole.FieldRole, self.foreshadowRevealChapterSpin)

        self.foreshadowStatusLabel = QLabel(self.foreshadowPage)
        self.foreshadowStatusLabel.setObjectName(u"foreshadowStatusLabel")

        self.foreshadowForm.setWidget(4, QFormLayout.ItemRole.LabelRole, self.foreshadowStatusLabel)

        self.foreshadowStatusEdit = QLineEdit(self.foreshadowPage)
        self.foreshadowStatusEdit.setObjectName(u"foreshadowStatusEdit")

        self.foreshadowForm.setWidget(4, QFormLayout.ItemRole.FieldRole, self.foreshadowStatusEdit)

        self.foreshadowPublicInfoLabel = QLabel(self.foreshadowPage)
        self.foreshadowPublicInfoLabel.setObjectName(u"foreshadowPublicInfoLabel")

        self.foreshadowForm.setWidget(5, QFormLayout.ItemRole.LabelRole, self.foreshadowPublicInfoLabel)

        self.foreshadowPublicInfoEdit = QTextEdit(self.foreshadowPage)
        self.foreshadowPublicInfoEdit.setObjectName(u"foreshadowPublicInfoEdit")
        self.foreshadowPublicInfoEdit.setMaximumHeight(120)

        self.foreshadowForm.setWidget(5, QFormLayout.ItemRole.SpanningRole, self.foreshadowPublicInfoEdit)

        self.foreshadowAuthorTruthLabel = QLabel(self.foreshadowPage)
        self.foreshadowAuthorTruthLabel.setObjectName(u"foreshadowAuthorTruthLabel")

        self.foreshadowForm.setWidget(6, QFormLayout.ItemRole.LabelRole, self.foreshadowAuthorTruthLabel)

        self.foreshadowAuthorTruthEdit = QTextEdit(self.foreshadowPage)
        self.foreshadowAuthorTruthEdit.setObjectName(u"foreshadowAuthorTruthEdit")
        self.foreshadowAuthorTruthEdit.setMaximumHeight(120)

        self.foreshadowForm.setWidget(6, QFormLayout.ItemRole.SpanningRole, self.foreshadowAuthorTruthEdit)

        self.foreshadowRelatedCharactersLabel = QLabel(self.foreshadowPage)
        self.foreshadowRelatedCharactersLabel.setObjectName(u"foreshadowRelatedCharactersLabel")

        self.foreshadowForm.setWidget(7, QFormLayout.ItemRole.LabelRole, self.foreshadowRelatedCharactersLabel)

        self.foreshadowRelatedCharactersEdit = QLineEdit(self.foreshadowPage)
        self.foreshadowRelatedCharactersEdit.setObjectName(u"foreshadowRelatedCharactersEdit")

        self.foreshadowForm.setWidget(7, QFormLayout.ItemRole.FieldRole, self.foreshadowRelatedCharactersEdit)

        self.foreshadowNotesLabel = QLabel(self.foreshadowPage)
        self.foreshadowNotesLabel.setObjectName(u"foreshadowNotesLabel")

        self.foreshadowForm.setWidget(8, QFormLayout.ItemRole.LabelRole, self.foreshadowNotesLabel)

        self.foreshadowNotesEdit = QTextEdit(self.foreshadowPage)
        self.foreshadowNotesEdit.setObjectName(u"foreshadowNotesEdit")
        self.foreshadowNotesEdit.setMaximumHeight(120)

        self.foreshadowForm.setWidget(8, QFormLayout.ItemRole.SpanningRole, self.foreshadowNotesEdit)

        self.formStack.addWidget(self.foreshadowPage)
        self.majorEventPage = QWidget()
        self.majorEventPage.setObjectName(u"majorEventPage")
        self.majorEventForm = QFormLayout(self.majorEventPage)
        self.majorEventForm.setObjectName(u"majorEventForm")
        self.majorTitleLabel = QLabel(self.majorEventPage)
        self.majorTitleLabel.setObjectName(u"majorTitleLabel")

        self.majorEventForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.majorTitleLabel)

        self.majorTitleEdit = QLineEdit(self.majorEventPage)
        self.majorTitleEdit.setObjectName(u"majorTitleEdit")

        self.majorEventForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.majorTitleEdit)

        self.majorStartChapterLabel = QLabel(self.majorEventPage)
        self.majorStartChapterLabel.setObjectName(u"majorStartChapterLabel")

        self.majorEventForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.majorStartChapterLabel)

        self.majorStartChapterSpin = QSpinBox(self.majorEventPage)
        self.majorStartChapterSpin.setObjectName(u"majorStartChapterSpin")
        self.majorStartChapterSpin.setMinimum(0)
        self.majorStartChapterSpin.setMaximum(9999)

        self.majorEventForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.majorStartChapterSpin)

        self.majorEndChapterLabel = QLabel(self.majorEventPage)
        self.majorEndChapterLabel.setObjectName(u"majorEndChapterLabel")

        self.majorEventForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.majorEndChapterLabel)

        self.majorEndChapterSpin = QSpinBox(self.majorEventPage)
        self.majorEndChapterSpin.setObjectName(u"majorEndChapterSpin")
        self.majorEndChapterSpin.setMinimum(0)
        self.majorEndChapterSpin.setMaximum(9999)

        self.majorEventForm.setWidget(2, QFormLayout.ItemRole.FieldRole, self.majorEndChapterSpin)

        self.majorDescriptionLabel = QLabel(self.majorEventPage)
        self.majorDescriptionLabel.setObjectName(u"majorDescriptionLabel")

        self.majorEventForm.setWidget(3, QFormLayout.ItemRole.LabelRole, self.majorDescriptionLabel)

        self.majorDescriptionEdit = QTextEdit(self.majorEventPage)
        self.majorDescriptionEdit.setObjectName(u"majorDescriptionEdit")
        self.majorDescriptionEdit.setMaximumHeight(120)

        self.majorEventForm.setWidget(3, QFormLayout.ItemRole.SpanningRole, self.majorDescriptionEdit)

        self.majorConsequenceLabel = QLabel(self.majorEventPage)
        self.majorConsequenceLabel.setObjectName(u"majorConsequenceLabel")

        self.majorEventForm.setWidget(4, QFormLayout.ItemRole.LabelRole, self.majorConsequenceLabel)

        self.majorConsequenceEdit = QTextEdit(self.majorEventPage)
        self.majorConsequenceEdit.setObjectName(u"majorConsequenceEdit")
        self.majorConsequenceEdit.setMaximumHeight(120)

        self.majorEventForm.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.majorConsequenceEdit)

        self.majorStatusLabel = QLabel(self.majorEventPage)
        self.majorStatusLabel.setObjectName(u"majorStatusLabel")

        self.majorEventForm.setWidget(5, QFormLayout.ItemRole.LabelRole, self.majorStatusLabel)

        self.majorStatusEdit = QLineEdit(self.majorEventPage)
        self.majorStatusEdit.setObjectName(u"majorStatusEdit")

        self.majorEventForm.setWidget(5, QFormLayout.ItemRole.FieldRole, self.majorStatusEdit)

        self.formStack.addWidget(self.majorEventPage)
        self.timelinePage = QWidget()
        self.timelinePage.setObjectName(u"timelinePage")
        self.timelineForm = QFormLayout(self.timelinePage)
        self.timelineForm.setObjectName(u"timelineForm")
        self.timelineChapterLabel = QLabel(self.timelinePage)
        self.timelineChapterLabel.setObjectName(u"timelineChapterLabel")

        self.timelineForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.timelineChapterLabel)

        self.timelineChapterSpin = QSpinBox(self.timelinePage)
        self.timelineChapterSpin.setObjectName(u"timelineChapterSpin")
        self.timelineChapterSpin.setMinimum(0)
        self.timelineChapterSpin.setMaximum(9999)

        self.timelineForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.timelineChapterSpin)

        self.timelineStoryDateLabel = QLabel(self.timelinePage)
        self.timelineStoryDateLabel.setObjectName(u"timelineStoryDateLabel")

        self.timelineForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.timelineStoryDateLabel)

        self.timelineStoryDateEdit = QLineEdit(self.timelinePage)
        self.timelineStoryDateEdit.setObjectName(u"timelineStoryDateEdit")

        self.timelineForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.timelineStoryDateEdit)

        self.timelineTitleLabel = QLabel(self.timelinePage)
        self.timelineTitleLabel.setObjectName(u"timelineTitleLabel")

        self.timelineForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.timelineTitleLabel)

        self.timelineTitleEdit = QLineEdit(self.timelinePage)
        self.timelineTitleEdit.setObjectName(u"timelineTitleEdit")

        self.timelineForm.setWidget(2, QFormLayout.ItemRole.FieldRole, self.timelineTitleEdit)

        self.timelineDescriptionLabel = QLabel(self.timelinePage)
        self.timelineDescriptionLabel.setObjectName(u"timelineDescriptionLabel")

        self.timelineForm.setWidget(3, QFormLayout.ItemRole.LabelRole, self.timelineDescriptionLabel)

        self.timelineDescriptionEdit = QTextEdit(self.timelinePage)
        self.timelineDescriptionEdit.setObjectName(u"timelineDescriptionEdit")
        self.timelineDescriptionEdit.setMaximumHeight(120)

        self.timelineForm.setWidget(3, QFormLayout.ItemRole.SpanningRole, self.timelineDescriptionEdit)

        self.timelineLocationLabel = QLabel(self.timelinePage)
        self.timelineLocationLabel.setObjectName(u"timelineLocationLabel")

        self.timelineForm.setWidget(4, QFormLayout.ItemRole.LabelRole, self.timelineLocationLabel)

        self.timelineLocationEdit = QLineEdit(self.timelinePage)
        self.timelineLocationEdit.setObjectName(u"timelineLocationEdit")

        self.timelineForm.setWidget(4, QFormLayout.ItemRole.FieldRole, self.timelineLocationEdit)

        self.timelineParticipantsLabel = QLabel(self.timelinePage)
        self.timelineParticipantsLabel.setObjectName(u"timelineParticipantsLabel")

        self.timelineForm.setWidget(5, QFormLayout.ItemRole.LabelRole, self.timelineParticipantsLabel)

        self.timelineParticipantsEdit = QLineEdit(self.timelinePage)
        self.timelineParticipantsEdit.setObjectName(u"timelineParticipantsEdit")

        self.timelineForm.setWidget(5, QFormLayout.ItemRole.FieldRole, self.timelineParticipantsEdit)

        self.formStack.addWidget(self.timelinePage)

        self.right.addWidget(self.formStack)

        self.entitiesSplitter.addWidget(self.entitiesRight)

        self.l.addWidget(self.entitiesSplitter)


        self.retranslateUi(EntitiesPage)

        self.formStack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(EntitiesPage)
    # setupUi

    def retranslateUi(self, EntitiesPage):
        EntitiesPage.setStyleSheet(QCoreApplication.translate("EntitiesPage", u"QLabel { color: #d0d0d0; font-size: 12px; } QLineEdit, QTextEdit, QSpinBox { background: #1e1e1e; color: #e0e0e0; border: 1px solid #3a3a3a; border-radius: 3px; padding: 4px; } QSplitter::handle { background: #6a6a6a; } QSplitter::handle:hover { background: #9a9a9a; }", None))
        self.catLbl.setText(QCoreApplication.translate("EntitiesPage", u"\ubd84\ub958", None))
        self.addBtn.setText(QCoreApplication.translate("EntitiesPage", u"+ \ucd94\uac00", None))
        self.delBtn.setText(QCoreApplication.translate("EntitiesPage", u"\uc0ad\uc81c", None))
        self.nameLbl.setText(QCoreApplication.translate("EntitiesPage", u"\uc774\ub984/\ucf54\ub4dc", None))
        self.generateBtn.setText(QCoreApplication.translate("EntitiesPage", u"AI\ub85c \uc0dd\uc131/\ubcf4\uc644", None))
        self.saveBtn.setText(QCoreApplication.translate("EntitiesPage", u"\uc800\uc7a5", None))
        self.characterNameLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc774\ub984", None))
        self.characterRoleLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc5ed\ud560", None))
        self.characterProfileLabel.setText(QCoreApplication.translate("EntitiesPage", u"\ud504\ub85c\ud544", None))
        self.characterPersonalityLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc131\uaca9", None))
        self.characterSpeechStyleLabel.setText(QCoreApplication.translate("EntitiesPage", u"\ub9d0\ud22c", None))
        self.characterGoalLabel.setText(QCoreApplication.translate("EntitiesPage", u"\ubaa9\ud45c", None))
        self.characterSecretLabel.setText(QCoreApplication.translate("EntitiesPage", u"\ube44\ubc00", None))
        self.characterArcLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc544\ud06c", None))
        self.factionNameLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc774\ub984", None))
        self.factionCategoryLabel.setText(QCoreApplication.translate("EntitiesPage", u"\ubd84\ub958", None))
        self.factionCategoryEdit.setStyleSheet(QCoreApplication.translate("EntitiesPage", u"background: #2a2a2a; color: #888;", None))
        self.factionDescriptionLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc124\uba85", None))
        self.factionRulesLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uaddc\uce59", None))
        self.locationNameLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc774\ub984", None))
        self.locationCategoryLabel.setText(QCoreApplication.translate("EntitiesPage", u"\ubd84\ub958", None))
        self.locationCategoryEdit.setStyleSheet(QCoreApplication.translate("EntitiesPage", u"background: #2a2a2a; color: #888;", None))
        self.locationDescriptionLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc124\uba85", None))
        self.locationRulesLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uaddc\uce59/\ud2b9\uc9d5", None))
        self.foreshadowCodeLabel.setText(QCoreApplication.translate("EntitiesPage", u"\ucf54\ub4dc", None))
        self.foreshadowTitleLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc81c\ubaa9", None))
        self.foreshadowFirstChapterLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uccab \ub4f1\uc7a5 \ud654\uc218", None))
        self.foreshadowRevealChapterLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uacf5\uac1c \ud654\uc218", None))
        self.foreshadowStatusLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc0c1\ud0dc", None))
        self.foreshadowPublicInfoLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uacf5\uac1c\ub41c \uc815\ubcf4", None))
        self.foreshadowAuthorTruthLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc9c4\uc0c1(\uc791\uac00 \uc9c4\uc2e4)", None))
        self.foreshadowRelatedCharactersLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uad00\ub828 \uc778\ubb3c", None))
        self.foreshadowNotesLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uba54\ubaa8", None))
        self.majorTitleLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc81c\ubaa9", None))
        self.majorStartChapterLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc2dc\uc791 \ud654\uc218", None))
        self.majorEndChapterLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc885\ub8cc \ud654\uc218", None))
        self.majorDescriptionLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc124\uba85", None))
        self.majorConsequenceLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uacb0\uacfc/\ud30c\uc7a5", None))
        self.majorStatusLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc0c1\ud0dc", None))
        self.timelineChapterLabel.setText(QCoreApplication.translate("EntitiesPage", u"\ud654\uc218", None))
        self.timelineStoryDateLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc774\uc57c\uae30 \uc18d \ub0a0\uc9dc", None))
        self.timelineTitleLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc81c\ubaa9", None))
        self.timelineDescriptionLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc124\uba85", None))
        self.timelineLocationLabel.setText(QCoreApplication.translate("EntitiesPage", u"\uc7a5\uc18c", None))
        self.timelineParticipantsLabel.setText(QCoreApplication.translate("EntitiesPage", u"\ucc38\uc5ec\uc790", None))
    # retranslateUi

