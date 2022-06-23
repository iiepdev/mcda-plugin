from qgis.PyQt.QtWidgets import QDialog

from ..core.economic_model import EconomicSuitability
from ..core.environmental_model import EnvironmentalSuitability
from ..core.hri_model import NaturalHazardRisksForSchools
from ..core.infrastructure_model import InfrastructureSuitability
from ..core.mcda_model import Mcda
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
        self.dlg.infrastructure_help_string = (
            InfrastructureSuitability.shortHelpString()
        )
        self.dlg.economic_help_string = EconomicSuitability.shortHelpString()
        self.dlg.environmental_help_string = EnvironmentalSuitability.shortHelpString()
        self.dlg.mcda_help_string = Mcda.shortHelpString()
        self.dlg.textBrowser.setPlainText("help")
        self.dlg.textBrowser.setHtml(self.dlg.hri_help_string)

        self.help_string_dict = {
            0: self.dlg.hri_help_string,
            1: self.dlg.infrastructure_help_string,
            2: self.dlg.economic_help_string,
            3: self.dlg.environmental_help_string,
            4: self.dlg.mcda_help_string,
        }
        print(self.help_string_dict)

        def _update_content(index):
            self.dlg.textBrowser.setHtml(self.help_string_dict.get(index))

        self.dlg.comboBox.currentIndexChanged.connect(_update_content)
