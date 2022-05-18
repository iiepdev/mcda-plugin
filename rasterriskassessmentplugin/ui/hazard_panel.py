import logging

from qgis.PyQt.QtWidgets import QDialog, QProgressBar, QGridLayout, QLabel, QGroupBox
from qgis.gui import (
    QgsMapLayerComboBox,
    QgsSpinBox,
    QgsDoubleSpinBox,
    QgsCollapsibleGroupBox,
)
from qgis.core import QgsFieldProxyModel, QgsMapLayerProxyModel

from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.i18n import tr
from ..qgis_plugin_tools.tools.resources import plugin_name
from ..qgis_plugin_tools.tools.exceptions import QgsPluginException
from .base_panel import BasePanel


LOGGER = logging.getLogger(plugin_name())


class HazardRiskIndexPanel(BasePanel):
    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self.panel = Panels.HazardRiskIndex

    def setup_panel(self) -> None:

        self.dlg.hri_map_layer_cmb_bx_boundaries: QgsMapLayerComboBox
        self.dlg.hri_map_layer_cmb_bx_schools: QgsMapLayerComboBox
        self.dlg.hri_progress_bar: QProgressBar
        self.dlg.hri_risk_layer_gridlayout: QGridLayout
        self.dlg.groupbox_rasters: QgsCollapsibleGroupBox
        # self.dlg.hri_progress_bar.setMinimum(0)
        self.dlg.hri_progress_bar.setValue(0)
        self.dlg.hri_map_layer_cmb_bx_boundaries.setFilters(
            QgsMapLayerProxyModel.PolygonLayer
        )
        self.dlg.hri_map_layer_cmb_bx_schools.setFilters(
            QgsMapLayerProxyModel.PointLayer
        )
        self.dlg.hri_spn_bx_number_of_hazards: QgsSpinBox
        self.dlg.hri_spn_bx_number_of_hazards.setClearValue(1)
        self.dlg.hri_spn_bx_number_of_hazards.clear()
        self.dlg.hri_spn_bx_number_of_hazards.setMinimum(1)
        self.dlg.hri_spn_bx_number_of_hazards.setMaximum(6)

        # self.dlg.hri_spn_bx_number_of_hazards.valueChanged.connect(
        #    self.__set_hri_risk_layer_grid
        # )

        self.dlg.hri_raster_layer_cb_1: QgsMapLayerComboBox()
        self.dlg.hri_raster_layer_cb_2: QgsMapLayerComboBox()
        self.dlg.hri_raster_layer_cb_3: QgsMapLayerComboBox()
        self.dlg.hri_raster_layer_cb_4: QgsMapLayerComboBox()
        self.dlg.hri_raster_layer_cb_5: QgsMapLayerComboBox()
        self.dlg.hri_raster_layer_cb_6: QgsMapLayerComboBox()
        self.dlg.hri_raster_layer_cb_1.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.hri_raster_layer_cb_2.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.hri_raster_layer_cb_3.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.hri_raster_layer_cb_4.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.hri_raster_layer_cb_5.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.hri_raster_layer_cb_6.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.hri_raster_layer_cb_1.setShowCrs(True)
        self.dlg.hri_raster_layer_cb_2.setShowCrs(True)
        self.dlg.hri_raster_layer_cb_3.setShowCrs(True)
        self.dlg.hri_raster_layer_cb_4.setShowCrs(True)
        self.dlg.hri_raster_layer_cb_5.setShowCrs(True)
        self.dlg.hri_raster_layer_cb_6.setShowCrs(True)
        self.dlg.hri_raster_layer_dspnb_1: QgsDoubleSpinBox()
        self.dlg.hri_raster_layer_dspnb_2: QgsDoubleSpinBox()
        self.dlg.hri_raster_layer_dspnb_3: QgsDoubleSpinBox()
        self.dlg.hri_raster_layer_dspnb_4: QgsDoubleSpinBox()
        self.dlg.hri_raster_layer_dspnb_5: QgsDoubleSpinBox()
        self.dlg.hri_raster_layer_dspnb_6: QgsDoubleSpinBox()

        self.dlg.hri_risk_layer_gridlayout.addWidget(
            QLabel("Number of hazard risks to include", self.dlg), 0, 0, 1, 2
        )
        for i in range(5):
            self.dlg.hri_risk_layer_gridlayout.addWidget(
                QLabel("Layer {}".format(i + 1), self.dlg), i + 1, 0
            )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_spn_bx_number_of_hazards, 0, 2
        )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_raster_layer_cb_1, 1, 1
        )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_raster_layer_cb_2, 2, 1
        )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_raster_layer_cb_3, 3, 1
        )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_raster_layer_cb_4, 4, 1
        )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_raster_layer_cb_5, 5, 1
        )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_raster_layer_cb_6, 6, 1
        )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_raster_layer_dspnb_1, 1, 2
        )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_raster_layer_dspnb_2, 2, 2
        )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_raster_layer_dspnb_3, 3, 2
        )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_raster_layer_dspnb_4, 4, 2
        )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_raster_layer_dspnb_5, 5, 2
        )
        self.dlg.hri_risk_layer_gridlayout.addWidget(
            self.dlg.hri_raster_layer_dspnb_6, 6, 2
        )

        self.dlg.groupbox_rasters.setLayout(self.dlg.hri_risk_layer_gridlayout)

        self.hri_layer_1 = self.dlg.hri_raster_layer_cb_1.currentLayer()
        self.hri_layer_2 = self.dlg.hri_raster_layer_cb_2.currentLayer()
        self.hri_layer_3 = self.dlg.hri_raster_layer_cb_3.currentLayer()
        self.hri_layer_4 = self.dlg.hri_raster_layer_cb_4.currentLayer()
        self.hri_layer_5 = self.dlg.hri_raster_layer_cb_5.currentLayer()
        self.hri_layer_6 = self.dlg.hri_raster_layer_cb_6.currentLayer()

        self.dlg.hri_map_layer_cmb_bx_boundaries.setShowCrs(True)
        self.dlg.hri_map_layer_cmb_bx_schools.setShowCrs(True)
        self.dlg.hri_raster_layer_cb_1.layerChanged.connect(
            self.__update_selected_layer
        )
        # self.hri_btn_run
        self.dlg.hri_btn_close.clicked.connect(self.__close_dialog)
        self.dlg.hri_raster_layer_cb_1.layerChanged.connect(
            self.__update_selected_layer
        )

    """def __set_hri_risk_layer_grid(self, nr_of_risks):

        print(nr_of_risks)
        self.__clear_gridlayout(self.dlg.hri_risk_layer_gridlayout)

        for i in range(1, nr_of_risks):
            self.dlg.hri_risk_layer_gridlayout.addWidget(
                QLabel("Layer {}".format(i + 1), self.dlg), i, 0
            )
            self.dlg.hri_risk_layer_gridlayout.addWidget(
                QgsMapLayerComboBox(),
                i,
                1,
            )
            self.dlg.hri_risk_layer_gridlayout.addWidget(
                self.dlg.hri_widget_list[i], i, 1
            )
            self.dlg.hri_risk_layer_gridlayout.addWidget(QgsDoubleSpinBox(), i, 2)

            self.dlg.hri_risk_layer_gridlayout.setRowMinimumHeight(i, 20)"""

    def __update_selected_layer(self, layer):
        self.hri_layer_1 = layer
        print(self.hri_layer_1)

    def __clear_gridlayout(self, layout):
        pass
        # does not work
        # while layout.count() > 0:
        #    layout.itemAt(0).setParent(None)

        """for i in range(layout.rowCount()):
        for j in range(layout.columnCount()):
            layout.removeWidget(layout.itemAt(i, j))
        for i in range(layout.rowCount() * layout.columnCount()):
            layout.removeWidget(parent, layout.itemAt(i))"""

    def __close_dialog(self):
        self.dlg.hide()
