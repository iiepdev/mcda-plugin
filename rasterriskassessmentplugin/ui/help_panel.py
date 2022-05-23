import logging

from qgis.PyQt.QtWidgets import QDialog, QTextBrowser
from qgis.core import QgsFieldProxyModel, QgsMapLayerProxyModel

from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import plugin_name
from ..qgis_plugin_tools.tools.version import version
from .base_panel import BasePanel
from ..core.hri_model import NaturalHazardRisksForSchools
from ..core.economic_model import EconomicSuitability


class HelpPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.panel = Panels.Help

    def setup_panel(self) -> None:

        self.dlg.textBrowser: QTextBrowser()
        # self.dlg.hri_help: str()
        self.dlg.hri_help_string = NaturalHazardRisksForSchools.shortHelpString(self)
        self.dlg.economic_help_string = EconomicSuitability.shortHelpString(self)

        self.dlg.textBrowser.setPlainText("help")
        self.dlg.textBrowser.setHtml(self.dlg.hri_help_string)

        # self.dlg.textBrowser.currentTextChanged.connect(__update_content)

        # def __update_content(self):
        #    self.dlg.textBrowser.setPlainText
