import logging
from typing import Any, Dict

from qgis.core import QgsMapLayerProxyModel
from qgis.gui import QgsFileWidget
from qgis.PyQt.QtWidgets import QDialog

from ..core.mcda_model import Mcda
from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.resources import plugin_name
from .base_panel import BasePanel

LOGGER = logging.getLogger(plugin_name())


class MultiCriteriaSuitabilityPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.name = "mcda"
        self.panel = Panels.MultiCriteriaSuitability
        self.algorithm = Mcda()

    def setup_panel(self) -> None:
        super().setup_panel()
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
        self.dlg.mcda_map_layer_cmb_bx_env.setShowCrs(True)
        self.dlg.mcda_map_layer_cmb_bx_econ.setShowCrs(True)
        self.dlg.mcda_map_layer_cmb_bx_infra.setShowCrs(True)
        self.dlg.mcda_dbl_spn_bx_env_weight.setMinimum(0)
        self.dlg.mcda_dbl_spn_bx_env_weight.setMaximum(100)
        self.dlg.mcda_dbl_spn_bx_env_weight.setClearValue(40)
        self.dlg.mcda_dbl_spn_bx_env_weight.clear()
        self.dlg.mcda_dbl_spn_bx_econ_weight.setMinimum(0)
        self.dlg.mcda_dbl_spn_bx_econ_weight.setMaximum(100)
        self.dlg.mcda_dbl_spn_bx_econ_weight.setClearValue(30)
        self.dlg.mcda_dbl_spn_bx_econ_weight.clear()
        self.dlg.mcda_dbl_spn_bx_infra_weight.setMinimum(0)
        self.dlg.mcda_dbl_spn_bx_infra_weight.setMaximum(100)
        self.dlg.mcda_dbl_spn_bx_infra_weight.setClearValue(30)
        self.dlg.mcda_dbl_spn_bx_infra_weight.clear()

        self.dlg.mcda_file_wdgt_save_output.setStorageMode(QgsFileWidget.SaveFile)
        self.dlg.mcda_file_wdgt_save_output.fileChanged.connect(
            lambda: self._set_file_extension(
                self.dlg.mcda_file_wdgt_save_output, ".tif"
            )
        )

    def _get_params(self) -> dict:
        params: Dict[str, Any] = {}
        params["Studyarea"] = self.dlg.hri_map_layer_cmb_bx_boundaries.currentLayer()
        params["Layers"] = []
        params["Weights"] = []
        layer_ids = ["env", "econ", "infra"]
        for id in layer_ids:
            params["Layers"].append(
                getattr(self.dlg, f"mcda_map_layer_cmb_bx_{id}").currentLayer()
            )
            params["Weights"].append(
                getattr(self.dlg, f"mcda_dbl_spn_bx_{id}_weight").value()
            )
        params["Weights"] = self._normalize_weights(params["Weights"])
        # Our layers already contain suitability indexes 1 (best) to 4 (worst).
        # We just want to sum the indexes without normalizing.
        params["NormalizeLayers"] = False
        # Use default 3857 for now (~1 meter around the equator)
        params["ProjectedReferenceSystem"] = "EPSG:3857"
        params["OutputRaster"] = self.dlg.mcda_file_wdgt_save_output.filePath()
        params["LayerNames"] = {"OutputRaster": "MCDA", "SampledOutput": None}
        return params
