from qgis.PyQt.QtWidgets import QDialog

from ..core.economic_model import EconomicSuitability
from ..core.hri_model import NaturalHazardRisksForSchools
from ..definitions.gui import Panels
from .base_panel import BasePanel


class HelpPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.name = "help"
        self.panel = Panels.Help

    def setup_panel(self) -> None:

        # self.dlg.hri_help: str()
        self.dlg.hri_help_string = NaturalHazardRisksForSchools.shortHelpString()
        self.dlg.economic_help_string = EconomicSuitability.shortHelpString()

        self.dlg.textBrowser.setPlainText("help")
        self.dlg.textBrowser.setHtml(self.dlg.hri_help_string)

        # self.dlg.textBrowser.currentTextChanged.connect(__update_content)

        # def __update_content(self):
        #    self.dlg.textBrowser.setPlainText
