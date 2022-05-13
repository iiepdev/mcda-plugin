import logging

from qgis.PyQt.QtWidgets import QDialog
from qgis.core import QgsFieldProxyModel, QgsMapLayerProxyModel

from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import plugin_name
from ..qgis_plugin_tools.tools.version import version
from .base_panel import BasePanel


class EnvironmentalSuitabilityPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.panel = Panels.EnvironmentalSuitability

    def setup_panel(self) -> None:
        self.dlg.env_map_layer_cmb_bx_boundary.setFilters(
            QgsMapLayerProxyModel.PolygonLayer
        )
        self.dlg.env_map_layer_cmb_bx_hri.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.env_map_layer_cmb_bx_dem.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.env_map_layer_cmb_bx_forest.setFilters(
            QgsMapLayerProxyModel.RasterLayer
        )

        # env_file_wdgt_save_output
