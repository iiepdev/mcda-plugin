import logging
from typing import Any, Dict, Optional

from qgis.core import QgsMapLayerProxyModel, QgsRasterLayer, QgsVectorLayer
from qgis.gui import QgsDoubleSpinBox, QgsFileWidget, QgsMapLayerComboBox
from qgis.PyQt.QtWidgets import QDialog, QLabel

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
        self.dlg.hri_save_hri_schools_file_widget.setStorageMode(QgsFileWidget.SaveFile)

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
            # remove layers
            while layout.count() > 2 + 3 * nr_of_risks:
                widget = layout.itemAt(layout.count() - 1).widget()
                layout.removeWidget(widget)
                widget.deleteLater()
        if nr_of_risks > self.current_number_of_hazards:
            # add layers
            layer_number = int((layout.count() - 2) / 3) + 1
            while layer_number <= nr_of_risks:
                # label
                label = QLabel(f"Layer {layer_number}", self.dlg)
                label.setObjectName(f"hri_raster_layer_label_{layer_number}")
                self.dlg.hri_risk_layer_gridlayout.addWidget(label, layer_number, 0)

                # combobox
                combobox = QgsMapLayerComboBox()
                combobox.setObjectName(f"hri_raster_layer_cb_{layer_number}")
                self.__set_combobox(combobox, layer_number)
                self.dlg.hri_risk_layer_gridlayout.addWidget(combobox, layer_number, 1)

                # spinbox
                spinbox = QgsDoubleSpinBox()
                spinbox.setObjectName(f"hri_raster_layer_dspnb_{layer_number}")
                self.__set_spinbox(spinbox)
                self.dlg.hri_risk_layer_gridlayout.addWidget(spinbox, layer_number, 2)
                layer_number = int((layout.count() - 2) / 3) + 1
        self.current_number_of_hazards = nr_of_risks

    def __normalize_weights(self, weights: list) -> list:
        """
        Always sum weights to 1.
        """
        total = sum(weights)
        return [value / total for value in weights]

    def _get_params(self) -> dict:
        params: Dict[str, Any] = {}
        params["HazardLayers"] = []
        params["Weights"] = []
        for layer_number in range(1, self.current_number_of_hazards + 1):
            params["HazardLayers"].append(
                getattr(self.dlg, f"hri_raster_layer_cb_{layer_number}").currentLayer()
            )
            params["Weights"].append(
                getattr(self.dlg, f"hri_raster_layer_dspnb_{layer_number}").value()
            )
        params["Weights"] = self.__normalize_weights(params["Weights"])
        # Use default 3857 for now (~1 meter around the equator)
        params["ProjectedReferenceSystem"] = "EPSG:3857"
        params["Studyarea"] = self.dlg.hri_map_layer_cmb_bx_boundaries.currentLayer()
        params["Schools"] = self.dlg.hri_map_layer_cmb_bx_schools.currentLayer()
        params["HazardIndex"] = self.dlg.hri_save_hri_file_widget.filePath()
        params[
            "HazardIndexSchools"
        ] = self.dlg.hri_save_hri_schools_file_widget.filePath()
        return params
