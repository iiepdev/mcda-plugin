import logging
from typing import Any, Dict

from qgis.core import QgsCoordinateReferenceSystem, QgsMapLayerProxyModel
from qgis.gui import QgsFileWidget, QgsProjectionSelectionWidget
from qgis.PyQt.QtWidgets import QDialog

from ..core.infrastructure_model import InfrastructureSuitability
from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.resources import plugin_name
from .base_panel import BasePanel

LOGGER = logging.getLogger(plugin_name())


# class MetricCrsOnlyProjectionSelectionWidget(QgsProjectionSelectionWidget):
#     def selectCrs(self):  # noqa
#         dialog = QgsProjectionSelectionDialog(self)
#         dialog.setOgcWmsCrsFilter(self._metric_crs_list)
#         if dialog.exec():
#             self.setValue(dialog.crs().authid())

#     @property
#     def _metric_crs_list(self):
#         return ["EPSG:3857", ]


class InfrastructurePanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.algorithm = InfrastructureSuitability()
        self.panel = Panels.Infrastructure
        self.name = "infra"

    def setup_panel(self) -> None:
        super().setup_panel()
        self.dlg.infra_map_layer_cmb_bx_boundaries.setFilters(
            QgsMapLayerProxyModel.PolygonLayer
        )
        self.dlg.infra_map_layer_cmb_bx_schools.setFilters(
            QgsMapLayerProxyModel.PointLayer
        )
        self.dlg.infra_map_layer_cmb_bx_pop_dens.setFilters(
            QgsMapLayerProxyModel.RasterLayer
        )
        self.dlg.infra_map_layer_cmb_bx_boundaries.setShowCrs(True)
        self.dlg.infra_map_layer_cmb_bx_schools.setShowCrs(True)
        self.dlg.infra_map_layer_cmb_bx_pop_dens.setShowCrs(True)
        self.dlg.infra_crs_widget.setShowAccuracyWarnings(True)
        self.dlg.infra_crs_widget.setOptionVisible(
            QgsProjectionSelectionWidget.CrsOption.LayerCrs, visible=True
        )
        # would require a whole custom dialog to filter the crs choices :(
        # self.dlg.infra_crs_widget.dialog.setOgcWmsCrsFilter(self._metric_crs_list)
        # Use default 3857 until the user selects a better one
        # (~1 meter around the equator)
        self.dlg.infra_crs_widget.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))

        self.dlg.infra_dbl_spn_bx_min_dist.setMinimum(0)
        self.dlg.infra_dbl_spn_bx_min_dist.setMaximum(100)
        self.dlg.infra_dbl_spn_bx_min_dist.setClearValue(0.05)
        self.dlg.infra_dbl_spn_bx_min_dist.clear()
        self.dlg.infra_dbl_spn_bx_max_dist.setMinimum(0)
        self.dlg.infra_dbl_spn_bx_max_dist.setMaximum(10)
        self.dlg.infra_dbl_spn_bx_max_dist.setClearValue(1.5)
        self.dlg.infra_dbl_spn_bx_max_dist.clear()
        self.dlg.infra_dbl_spn_bx_pop_weight.setMinimum(0)
        self.dlg.infra_dbl_spn_bx_pop_weight.setMaximum(100)
        self.dlg.infra_dbl_spn_bx_pop_weight.setClearValue(40)
        self.dlg.infra_dbl_spn_bx_pop_weight.clear()
        self.dlg.infra_spinbox_pop_threshold.setMinimum(0)
        self.dlg.infra_spinbox_pop_threshold.setMaximum(1000)
        self.dlg.infra_spinbox_pop_threshold.setClearValue(100)
        self.dlg.infra_spinbox_pop_threshold.clear()
        self.dlg.infra_dbl_spn_bx_school_weight.setMinimum(0)
        self.dlg.infra_dbl_spn_bx_school_weight.setMaximum(100)
        self.dlg.infra_dbl_spn_bx_school_weight.setClearValue(60)
        self.dlg.infra_dbl_spn_bx_school_weight.clear()
        self.dlg.infra_dbl_spn_bx_pop_weight.valueChanged.connect(
            lambda value: self.dlg.infra_dbl_spn_bx_school_weight.setValue(100 - value)
        )
        self.dlg.infra_dbl_spn_bx_school_weight.valueChanged.connect(
            lambda value: self.dlg.infra_dbl_spn_bx_pop_weight.setValue(100 - value)
        )

        self.dlg.infra_file_wdgt_save_output.setStorageMode(QgsFileWidget.SaveFile)

    def _get_params(self) -> dict:
        params: Dict[str, Any] = {}
        params["Studyarea"] = self.dlg.infra_map_layer_cmb_bx_boundaries.currentLayer()
        params["Schools"] = self.dlg.infra_map_layer_cmb_bx_schools.currentLayer()
        # params[
        #     "Identifyingschoolvariable"
        # ] = self.dlg.infra_fld_cmb_bx_school_var.currentField()
        params[
            "PopulationDensity"
        ] = self.dlg.infra_map_layer_cmb_bx_pop_dens.currentLayer()
        params["MaxDistancefromExistingSchools"] = (
            self.dlg.infra_dbl_spn_bx_max_dist.value() * 1000
        )
        params["Minimumsuitabledistancetoanotherschool"] = (
            self.dlg.infra_dbl_spn_bx_min_dist.value() * 1000
        )
        params["PopulationThreshold"] = self.dlg.infra_spinbox_pop_threshold.value()
        params["Newschoolsshouldideallybelocatedinsparselypopulatedareas"] = (
            self.dlg.infra_ideal_location_combo_box.currentIndex() != 0
        )
        params[
            "Newschoolsshouldbelocatedfurtherfromexistingschoolsratherthanclosetothem"
        ] = (self.dlg.infra_location_combo_box.currentIndex() == 0)
        params["ProjectedReferenceSystem"] = self.dlg.infra_crs_widget.crs()
        params["SchoolWeight"] = self.dlg.infra_dbl_spn_bx_school_weight.value() / 100
        params["PopWeight"] = self.dlg.infra_dbl_spn_bx_pop_weight.value() / 100
        params[
            "InfrastructureSuitability"
        ] = self.dlg.infra_file_wdgt_save_output.filePath()
        LOGGER.info(params)
        return params
