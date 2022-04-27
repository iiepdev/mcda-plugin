import logging

from qgis.PyQt.QtWidgets import QDialog
from qgis.core import QgsFieldProxyModel, QgsMapLayerProxyModel

from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import plugin_name
from ..qgis_plugin_tools.tools.version import version
from .base_panel import BasePanel


class MultiCriteriaSuitabilityPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.panel = Panels.MultiCriteriaSuitability

    def setup_panel(self) -> None:
        self.dlg.mcda_map_layer_cmb_bx_boundary.setFilters(
            QgsMapLayerProxyModel.PolygonLayer
        )
        self.dlg.mcda_map_layer_cmb_bx_env.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.mcda_map_layer_cmb_bx_econ.setFilters(
            QgsMapLayerProxyModel.RasterLayer
        )
        self.dlg.mcda_map_layer_cmb_bx_infra.setFilters(
            QgsMapLayerProxyModel.RasterLayer
        )

        # mcda_file_wdgt_save_output
