import logging
from typing import Any, Dict, Optional

from qgis.core import (  # QgsLayerTreeLayer,; QgsProject,; QgsRasterLayer,
    QgsMapLayerProxyModel,
    QgsVectorLayer,
)
from qgis.PyQt.QtWidgets import QDialog

from ..core.infrastructure_model import InfrastructureSuitability
from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.resources import plugin_name
from .base_panel import BasePanel

LOGGER = logging.getLogger(plugin_name())


class InfrastructurePanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.algorithm = InfrastructureSuitability()
        self.panel = Panels.Infrastructure
        self.name = "infra"
        self.infra_result: Optional[QgsVectorLayer] = None

    def setup_panel(self) -> None:
        super().setup_panel()
        self.dlg.infra_map_layer_cmb_bx_boundaries.setFilters(
            QgsMapLayerProxyModel.PolygonLayer
        )
        self.dlg.infra_map_layer_cmb_bx_schools.setFilters(
            QgsMapLayerProxyModel.PointLayer
        )
        self.dlg.infra_map_layer_cmb_bx_boundaries.setShowCrs(True)
        self.dlg.infra_map_layer_cmb_bx_schools.setShowCrs(True)
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

    def _get_params(self) -> dict:
        pass
        # params: Dict[str, Any] = {}
        # params["HazardLayers"] = []
        # params["Weights"] = []
        # for layer_number in range(1, self.current_number_of_hazards + 1):
        #     params["HazardLayers"].append(
        #         getattr(self.dlg, f"hri_raster_layer_cb_{layer_number}").currentLayer()  # noqa
        #     )
        #     params["Weights"].append(
        #         getattr(self.dlg, f"hri_raster_layer_dspnb_{layer_number}").value()
        #     )
        # params["Weights"] = self.__normalize_weights(params["Weights"])
        # # use default 4326 for now
        # params["ProjectedReferenceSystem"] = 4326
        # params["Studyarea"] = self.dlg.hri_map_layer_cmb_bx_boundaries.currentLayer()
        # params["Schools"] = self.dlg.hri_map_layer_cmb_bx_schools.currentLayer()
        # params["HazardIndex"] = self.dlg.hri_save_hri_file_widget.filePath()
        # params[
        #     "HazardIndexSchools"
        # ] = self.dlg.hri_save_hri_schools_file_widget.filePath()
        # return params

    def _display_results(self, successful: bool, results: Dict[str, Any]) -> None:
        """
        Display result layers in current QGIS project.
        """
        pass
        # LOGGER.info("got results")
        # LOGGER.info(results)
        # if successful:
        #     # the raster layer will always be a tiff file (temporary or permanent)
        #     self.hri_result = QgsRasterLayer(results["HazardIndex"], "Hazard index")
        #     if results["HazardIndexSchools"]:
        #         # if result path was not set, the vector layer may only be in memory
        #         if self.params["HazardIndexSchools"]:
        #             self.hri_result_schools = QgsVectorLayer(
        #                 results["HazardIndexSchools"], "Hazard index - schools", "ogr"
        #             )
        #         else:
        #             # Aha! Child algorithm results won't actually be passed on:
        #             # https://gis.stackexchange.com/questions/361353/store-result-of-a-processing-algorithm-as-a-layer-in-qgis-python-script  # noqa
        #             # If a vector layer is only in memory, we will have to actually dig  # noqa
        #             # it up from the processing context to pass it on.
        #             self.hri_result_schools = self.context.takeResultLayer(
        #                 results["HazardIndexSchools"]
        #             )
        #     else:
        #         self.hri_result_schools = None
        #     QgsProject.instance().addMapLayer(self.hri_result, False)
        #     root = QgsProject.instance().layerTreeRoot()
        #     root.insertChildNode(0, QgsLayerTreeLayer(self.hri_result))
        #     if self.hri_result_schools:
        #         QgsProject.instance().addMapLayer(self.hri_result_schools, False)
        #         root.insertChildNode(0, QgsLayerTreeLayer(self.hri_result_schools))
