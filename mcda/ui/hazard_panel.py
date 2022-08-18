import logging
from typing import Any, Dict, Optional

from qgis.core import QgsMapLayerProxyModel, QgsRasterLayer, QgsVectorLayer
from qgis.gui import QgsDoubleSpinBox, QgsFileWidget, QgsMapLayerComboBox
from qgis.PyQt.QtWidgets import QDialog

from ..core.hri_model import NaturalHazardRisksForSchools
from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.resources import plugin_name
from .base_panel import BasePanel

LOGGER = logging.getLogger(plugin_name())


class HazardRiskIndexPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.algorithm = NaturalHazardRisksForSchools()
        self.panel = Panels.HazardRiskIndex
        self.name = "hri"
        self.minimum = 2
        self.maximum = 6
        self.default_values = 6
        self.current_number_of_hazards = self.default_values
        self.hri_result: Optional[QgsRasterLayer] = None
        self.hri_result_schools: Optional[QgsVectorLayer] = None

    def setup_panel(self) -> None:
        super().setup_panel()
        self.dlg.hri_map_layer_cmb_bx_boundaries.setFilters(
            QgsMapLayerProxyModel.PolygonLayer
        )
        self.dlg.hri_map_layer_cmb_bx_schools.setFilters(
            QgsMapLayerProxyModel.PointLayer
        )
        self.dlg.hri_map_layer_cmb_bx_boundaries.setShowCrs(True)
        self.dlg.hri_map_layer_cmb_bx_schools.setShowCrs(True)
        self.dlg.hri_spn_bx_number_of_hazards.setClearValue(self.default_values)
        self.dlg.hri_spn_bx_number_of_hazards.clear()
        self.dlg.hri_spn_bx_number_of_hazards.setMinimum(self.minimum)
        self.dlg.hri_spn_bx_number_of_hazards.setMaximum(self.maximum)
        self.dlg.hri_spn_bx_number_of_hazards.valueChanged.connect(
            self.__set_hri_risk_layer_grid
        )

        for layer_number in range(1, self.default_values + 1):
            combobox = getattr(self.dlg, f"hri_raster_layer_cb_{layer_number}")
            self.__set_combobox(combobox, layer_number)
            spinbox = getattr(self.dlg, f"hri_raster_layer_dspnb_{layer_number}")
            self.__set_spinbox(spinbox)

        self.dlg.groupbox_rasters.setLayout(self.dlg.hri_risk_layer_gridlayout)

        self.dlg.hri_save_hri_file_widget.setStorageMode(QgsFileWidget.SaveFile)
        self.dlg.hri_save_hri_file_widget.fileChanged.connect(
            lambda: self._set_file_extension(self.dlg.hri_save_hri_file_widget, ".tif")
        )
        self.dlg.hri_save_hri_schools_file_widget.setStorageMode(QgsFileWidget.SaveFile)
        self.dlg.hri_save_hri_schools_file_widget.fileChanged.connect(
            lambda: self._set_file_extension(
                self.dlg.hri_save_hri_schools_file_widget, ".gpkg"
            )
        )

    def __set_combobox(self, combobox: QgsMapLayerComboBox, layer_number: int) -> None:
        combobox.setFilters(QgsMapLayerProxyModel.RasterLayer)
        combobox.setShowCrs(True)
        combobox.setLayer(combobox.layer(layer_number - 1))

    def __set_spinbox(self, spinbox: QgsDoubleSpinBox) -> None:
        spinbox.setSuffix(" %")
        spinbox.setDecimals(1)
        spinbox.setClearValue(16.7)
        spinbox.clear()

    def __set_hri_risk_layer_grid(self, nr_of_risks: int) -> None:
        """
        Sets the form to have the desired number of risk layers.

        Note that this function requires that existing layout items in
        main_dialog.ui are defined in order of increasing row number.
        """
        layout = self.dlg.hri_risk_layer_gridlayout
        if nr_of_risks < self.current_number_of_hazards:
            # remove layers from layout
            while layout.count() > 2 + 3 * nr_of_risks:
                widget = layout.itemAt(layout.count() - 1).widget()
                widget.hide()
                layout.removeWidget(widget)
                # do not delete the widgets, they will be reused!
        if nr_of_risks > self.current_number_of_hazards:
            # add layers to layout
            layer_number = int((layout.count() - 2) / 3) + 1
            while layer_number <= nr_of_risks:
                # add existing widgets back to layout
                # label
                label = getattr(self.dlg, f"hri_raster_layer_label_{layer_number}")
                label.show()
                self.dlg.hri_risk_layer_gridlayout.addWidget(label, layer_number, 0)

                # combobox
                combobox = getattr(self.dlg, f"hri_raster_layer_cb_{layer_number}")
                combobox.show()
                self.dlg.hri_risk_layer_gridlayout.addWidget(combobox, layer_number, 1)

                # spinbox
                spinbox = getattr(self.dlg, f"hri_raster_layer_dspnb_{layer_number}")
                spinbox.show()
                self.dlg.hri_risk_layer_gridlayout.addWidget(spinbox, layer_number, 2)
                layer_number = int((layout.count() - 2) / 3) + 1
        self.current_number_of_hazards = nr_of_risks

    def _get_params(self) -> dict:
        params: Dict[str, Any] = {}
        params["Studyarea"] = self.dlg.hri_map_layer_cmb_bx_boundaries.currentLayer()
        params["Layers"] = []
        params["Weights"] = []
        for layer_number in range(1, self.current_number_of_hazards + 1):
            params["Layers"].append(
                getattr(self.dlg, f"hri_raster_layer_cb_{layer_number}").currentLayer()
            )
            params["Weights"].append(
                getattr(self.dlg, f"hri_raster_layer_dspnb_{layer_number}").value()
            )
        params["Weights"] = self._normalize_weights(params["Weights"])
        # The input layers may contain wildly different values, so they should
        # be normalized on a scale 0...1
        params["NormalizeLayers"] = True
        # Use default 3857 for now (~1 meter around the equator)
        params["ProjectedReferenceSystem"] = "EPSG:3857"
        params["Schools"] = self.dlg.hri_map_layer_cmb_bx_schools.currentLayer()
        params["OutputRaster"] = self.dlg.hri_save_hri_file_widget.filePath()
        params["SampledOutput"] = self.dlg.hri_save_hri_schools_file_widget.filePath()
        params["LayerNames"] = {
            "OutputRaster": "Hazard Index",
            "SampledOutput": "Hazard Index at Schools",
        }
        return params
