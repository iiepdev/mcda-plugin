import logging

from qgis.PyQt.QtWidgets import QDialog
from qgis.core import QgsFieldProxyModel, QgsMapLayerProxyModel

from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import plugin_name
from ..qgis_plugin_tools.tools.version import version
from .base_panel import BasePanel


class InfrastructurePanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.panel = Panels.Infrastructure

    def setup_panel(self) -> None:
        # self.dlg.infra_btn_close.connect()
        self.dlg.infra_map_layer_cmb_bx_boundaries.setFilters(
            QgsMapLayerProxyModel.PolygonLayer
        )
        self.dlg.infra_map_layer_cmb_bx_schools.setFilters(
            QgsMapLayerProxyModel.PointLayer
        )
        # self.dlg.infra_fld_cmb_bx_school_var(QgsFieldProxyModel.)
        """self.infra_dbl_spn_bx_max_dist: QgsDoubleSpinBox
        self.infra_dbl_spn_bx_max_dist.valueChanged.connect(
            self.on_max_dist_valueChanged
        )

        self.dlg.infra_map_layer_cmb_bx_schools.layerChanged.connect(
            self.infra_schools_layerChanged
        )

        def on_max_dist_valueChanged(self):
            pass

        def infra_schools_layerChanged(self, lyr):
            self.dlg.infra_fld_cmb_bx_school_var.setLayer(lyr)"""
