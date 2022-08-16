import logging
from typing import Any, Dict

from qgis.core import QgsCoordinateReferenceSystem, QgsMapLayerProxyModel
from qgis.gui import QgsFileWidget, QgsProjectionSelectionWidget
from qgis.PyQt.QtWidgets import QDialog

from ..core.economic_model import EconomicSuitability
from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.resources import plugin_name
from .base_panel import BasePanel

LOGGER = logging.getLogger(plugin_name())


class EconomicSuitabilityPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.algorithm = EconomicSuitability()
        self.panel = Panels.EconomicSuitability
        self.name = "econ"

    def setup_panel(self) -> None:
        super().setup_panel()
        self.dlg.econ_map_layer_cmb_bx_boundary.setFilters(
            QgsMapLayerProxyModel.PolygonLayer
        )
        self.dlg.econ_map_layer_cmb_bx_roads.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.dlg.econ_map_layer_cmb_bx_waterways.setFilters(
            QgsMapLayerProxyModel.LineLayer
        )
        self.dlg.econ_map_layer_cmb_bx_boundary.setShowCrs(True)
        self.dlg.econ_map_layer_cmb_bx_roads.setShowCrs(True)
        self.dlg.econ_map_layer_cmb_bx_waterways.setShowCrs(True)
        self.dlg.econ_crs_widget.setShowAccuracyWarnings(True)
        self.dlg.econ_crs_widget.setOptionVisible(
            QgsProjectionSelectionWidget.CrsOption.LayerCrs, visible=True
        )
        # would require a whole custom dialog to filter the crs choices :(
        # self.dlg.infra_crs_widget.dialog.setOgcWmsCrsFilter(self._metric_crs_list)
        # Use default 3857 until the user selects a better one
        # (~1 meter around the equator)
        self.dlg.econ_crs_widget.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))

        self.dlg.econ_dbl_spn_bx_road_min_dist.setMinimum(0)
        self.dlg.econ_dbl_spn_bx_road_min_dist.setMaximum(1)
        self.dlg.econ_dbl_spn_bx_road_min_dist.setClearValue(0.02)
        self.dlg.econ_dbl_spn_bx_road_min_dist.clear()
        self.dlg.econ_dbl_spn_bx_road_max_dist.setMinimum(0)
        self.dlg.econ_dbl_spn_bx_road_max_dist.setMaximum(10)
        self.dlg.econ_dbl_spn_bx_road_max_dist.setClearValue(0.5)
        self.dlg.econ_dbl_spn_bx_road_max_dist.clear()
        self.dlg.econ_dbl_spn_bx_water_min_dist.setMinimum(0)
        self.dlg.econ_dbl_spn_bx_water_min_dist.setMaximum(1)
        self.dlg.econ_dbl_spn_bx_water_min_dist.setClearValue(0.15)
        self.dlg.econ_dbl_spn_bx_water_min_dist.clear()
        self.dlg.econ_dbl_spn_bx_water_max_dist.setMinimum(0)
        self.dlg.econ_dbl_spn_bx_water_max_dist.setMaximum(10)
        self.dlg.econ_dbl_spn_bx_water_max_dist.setClearValue(1.5)
        self.dlg.econ_dbl_spn_bx_water_max_dist.clear()
        self.dlg.econ_dbl_spn_bx_road_weight.setMinimum(0)
        self.dlg.econ_dbl_spn_bx_road_weight.setMaximum(100)
        self.dlg.econ_dbl_spn_bx_road_weight.setClearValue(30)
        self.dlg.econ_dbl_spn_bx_road_weight.clear()
        self.dlg.econ_dbl_spn_bx_water_weight.setMinimum(0)
        self.dlg.econ_dbl_spn_bx_water_weight.setMaximum(100)
        self.dlg.econ_dbl_spn_bx_water_weight.setClearValue(70)
        self.dlg.econ_dbl_spn_bx_water_weight.clear()
        self.dlg.econ_dbl_spn_bx_road_weight.valueChanged.connect(
            lambda value: self.dlg.econ_dbl_spn_bx_water_weight.setValue(100 - value)
        )
        self.dlg.econ_dbl_spn_bx_water_weight.valueChanged.connect(
            lambda value: self.dlg.econ_dbl_spn_bx_road_weight.setValue(100 - value)
        )

        self.dlg.econ_file_wdgt_save_output.setStorageMode(QgsFileWidget.SaveFile)
        self.dlg.econ_file_wdgt_save_output.fileChanged.connect(
            lambda: self._set_file_extension(
                self.dlg.econ_file_wdgt_save_output, ".tif"
            )
        )

    def _get_params(self) -> dict:
        params: Dict[str, Any] = {}
        params["Studyarea"] = self.dlg.econ_map_layer_cmb_bx_boundary.currentLayer()
        params["Roads"] = self.dlg.econ_map_layer_cmb_bx_roads.currentLayer()
        params["Waterways"] = self.dlg.econ_map_layer_cmb_bx_waterways.currentLayer()
        # roads
        params["MaxRoadDistance"] = (
            self.dlg.econ_dbl_spn_bx_road_max_dist.value() * 1000
        )
        params["Minimumsuitabledistancetotheroad"] = (
            self.dlg.econ_dbl_spn_bx_road_min_dist.value() * 1000
        )
        params["Arelocationsclosetoroadsmoresuitable"] = (
            self.dlg.econ_cmb_bx_near_roads.currentIndex() != 0
        )
        params["WeightforRoads"] = self.dlg.econ_dbl_spn_bx_road_weight.value() / 100
        # waterways
        params["MaxWaterDistance"] = (
            self.dlg.econ_dbl_spn_bx_water_max_dist.value() * 1000
        )
        params["Minimumsuitabledistancetoawaterway"] = (
            self.dlg.econ_dbl_spn_bx_water_min_dist.value() * 1000
        )
        params["WeightforWaterways"] = (
            self.dlg.econ_dbl_spn_bx_water_weight.value() / 100
        )
        params["Arelocationsclosetowaterwaysmoresuitable"] = (
            self.dlg.econ_cmb_bx_near_water.currentIndex() != 0
        )
        params["ProjectedReferenceSystem"] = self.dlg.econ_crs_widget.crs()
        params["EconomicSuitability"] = self.dlg.econ_file_wdgt_save_output.filePath()
        LOGGER.info(params)
        return params
