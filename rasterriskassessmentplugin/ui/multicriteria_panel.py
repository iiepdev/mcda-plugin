from qgis.core import QgsMapLayerProxyModel
from qgis.PyQt.QtWidgets import QDialog

from ..definitions.gui import Panels
from .base_panel import BasePanel


class MultiCriteriaSuitabilityPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.name = "multi"
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
