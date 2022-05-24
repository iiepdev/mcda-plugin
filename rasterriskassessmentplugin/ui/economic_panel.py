from qgis.core import QgsMapLayerProxyModel
from qgis.PyQt.QtWidgets import QDialog

from ..definitions.gui import Panels
from .base_panel import BasePanel


class EconomicSuitabilityPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.panel = Panels.EconomicSuitability

    def setup_panel(self) -> None:
        self.dlg.econ_map_layer_cmb_bx_boundary.setFilters(
            QgsMapLayerProxyModel.PolygonLayer
        )
        self.dlg.econ_map_layer_cmb_bx_roads.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.dlg.econ_map_layer_cmb_bx_waterways.setFilters(
            QgsMapLayerProxyModel.LineLayer
        )
