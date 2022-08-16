from typing import Any, Dict

from qgis.core import QgsCoordinateReferenceSystem, QgsMapLayerProxyModel
from qgis.gui import QgsFileWidget, QgsProjectionSelectionWidget
from qgis.PyQt.QtWidgets import QDialog

from ..core.environmental_model import EnvironmentalSuitability
from ..definitions.gui import Panels
from .base_panel import BasePanel


class EnvironmentalSuitabilityPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.name = "env"
        self.panel = Panels.EnvironmentalSuitability
        self.algorithm = EnvironmentalSuitability()

    def setup_panel(self) -> None:
        super().setup_panel()
        self.dlg.env_map_layer_cmb_bx_boundary.setFilters(
            QgsMapLayerProxyModel.PolygonLayer
        )
        self.dlg.env_map_layer_cmb_bx_hri.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.env_map_layer_cmb_bx_dem.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.env_map_layer_cmb_bx_forest.setFilters(
            QgsMapLayerProxyModel.RasterLayer
        )
        self.dlg.env_map_layer_cmb_bx_boundary.setShowCrs(True)
        self.dlg.env_map_layer_cmb_bx_hri.setShowCrs(True)
        self.dlg.env_map_layer_cmb_bx_dem.setShowCrs(True)
        self.dlg.env_map_layer_cmb_bx_forest.setShowCrs(True)
        self.dlg.env_crs_widget.setShowAccuracyWarnings(True)
        self.dlg.env_crs_widget.setOptionVisible(
            QgsProjectionSelectionWidget.CrsOption.LayerCrs, visible=True
        )
        # would require a whole custom dialog to filter the crs choices :(
        # self.dlg.infra_crs_widget.dialog.setOgcWmsCrsFilter(self._metric_crs_list)
        # Use default 3857 until the user selects a better one
        # (~1 meter around the equator)
        self.dlg.env_crs_widget.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
        self.dlg.env_dbl_spn_bx_hri_weight.setMinimum(0)
        self.dlg.env_dbl_spn_bx_hri_weight.setMaximum(100)
        self.dlg.env_dbl_spn_bx_hri_weight.setClearValue(30)
        self.dlg.env_dbl_spn_bx_hri_weight.clear()
        self.dlg.env_dbl_spn_bx_dem_weight.setMinimum(0)
        self.dlg.env_dbl_spn_bx_dem_weight.setMaximum(100)
        self.dlg.env_dbl_spn_bx_dem_weight.setClearValue(20)
        self.dlg.env_dbl_spn_bx_dem_weight.clear()
        self.dlg.env_dbl_spn_bx_forest_weight.setMinimum(0)
        self.dlg.env_dbl_spn_bx_forest_weight.setMaximum(100)
        self.dlg.env_dbl_spn_bx_forest_weight.setClearValue(50)
        self.dlg.env_dbl_spn_bx_forest_weight.clear()

        self.dlg.env_file_wdgt_save_output.setStorageMode(QgsFileWidget.SaveFile)
        self.dlg.env_file_wdgt_save_output.fileChanged.connect(
            lambda: self._set_file_extension(self.dlg.env_file_wdgt_save_output, ".tif")
        )

    def _get_params(self) -> dict:
        params: Dict[str, Any] = {}
        params["Studyarea"] = self.dlg.env_map_layer_cmb_bx_boundary.currentLayer()
        params["MultiHazardRisk"] = self.dlg.env_map_layer_cmb_bx_hri.currentLayer()
        params[
            "DigitalElevationModel"
        ] = self.dlg.env_map_layer_cmb_bx_dem.currentLayer()
        params[
            "ForestVegetationClassified"
        ] = self.dlg.env_map_layer_cmb_bx_forest.currentLayer()
        params["WeightforMultiHazardRisk"] = (
            self.dlg.env_dbl_spn_bx_hri_weight.value() / 100
        )
        params["WeightforElevation"] = self.dlg.env_dbl_spn_bx_dem_weight.value() / 100
        params["WeightforVegetation"] = (
            self.dlg.env_dbl_spn_bx_forest_weight.value() / 100
        )
        # layer_ids = ["hri", "dem", "forest"]
        # for id in layer_ids:
        #     params["Layers"].append(
        #         getattr(self.dlg, f"env_map_layer_cmb_bx_{id}").currentLayer()
        #     )
        #     params["Weights"].append(
        #         getattr(self.dlg, f"env_dbl_spn_bx_{id}_weight").value()
        #     )
        # params["Weights"] = self._normalize_weights(params["Weights"])

        # Use default 3857 for now (~1 meter around the equator)
        params["ProjectedReferenceSystem"] = "EPSG:3857"
        params[
            "EnvironmentalSuitability"
        ] = self.dlg.env_file_wdgt_save_output.filePath()
        return params
