import logging
from typing import Any, Dict

from qgis.core import (
    QgsMapLayerProxyModel,
    QgsProcessingContext,
    QgsRasterLayer,
    QgsVectorLayer,
)
from qgis.gui import QgsDoubleSpinBox, QgsFileWidget, QgsMapLayerComboBox
from qgis.PyQt.QtWidgets import QDialog, QLabel

from ..core.hri_model import NaturalHazardRisksForSchools
from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.logger_processing import LoggerProcessingFeedBack
from ..qgis_plugin_tools.tools.resources import plugin_name
from .base_panel import BasePanel

LOGGER = logging.getLogger(plugin_name())


class HazardRiskIndexPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.panel = Panels.HazardRiskIndex
        self.minimum = 2
        self.maximum = 6
        self.default_values = 6
        self.current_number_of_hazards = self.default_values
        self.hri_result = None
        self.hri_result_schools = None

    def setup_panel(self) -> None:

        # self.dlg.hri_progress_bar.setMinimum(0)
        self.dlg.hri_progress_bar.setValue(0)
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
        self.dlg.hri_btn_run.clicked.connect(self.__run_model)
        self.dlg.hri_btn_close.clicked.connect(self.__close_dialog)

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

    def __get_params(self) -> dict:
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
        # use default 4326 for now
        params["ProjectedReferenceSystem"] = 4326
        params["Studyarea"] = self.dlg.hri_map_layer_cmb_bx_boundaries.currentLayer()
        params["Schools"] = self.dlg.hri_map_layer_cmb_bx_schools.currentLayer()
        params["HazardIndex"] = self.hri_result
        params["HazardIndexSchools"] = self.hri_result_schools
        return params

    def __run_model(self) -> None:
        hri_path = self.dlg.hri_save_hri_file_widget.filePath()
        if hri_path:
            self.hri_result = QgsRasterLayer(hri_path, "Hazard index")
        hri_schools_path = self.dlg.hri_save_hri_schools_file_widget.filePath()
        if hri_schools_path:
            self.hri_result_schools = QgsVectorLayer(
                hri_schools_path, "Hazard index - schools", "ogr"
            )
        algorithm = NaturalHazardRisksForSchools()
        params = self.__get_params()
        context = QgsProcessingContext()
        feedback = LoggerProcessingFeedBack(use_logger=True)
        algorithm.initAlgorithm()
        LOGGER.info(params)
        results = algorithm.processAlgorithm(params, context, feedback)
        LOGGER.info(results)

    def __close_dialog(self) -> None:
        self.dlg.hide()
