from qgis.core import QgsMapLayerProxyModel
from qgis.PyQt.QtWidgets import QDialog

from ..definitions.gui import Panels
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
