import logging

from qgis.PyQt.QtWidgets import QDialog

from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import plugin_name
from ..qgis_plugin_tools.tools.exceptions import QgsPluginException
from .base_panel import BasePanel

LOGGER = logging.getLogger(plugin_name())


class HazardRiskIndexPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.panel = Panels.HazardRiskIndex

    def setup_panel(self) -> None:
        # self.hri_btn_close
        pass
