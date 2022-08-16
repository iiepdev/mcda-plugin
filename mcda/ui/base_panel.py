"""Panel core base class."""
import logging
from typing import Any, Dict, Optional

from qgis.core import (
    QgsApplication,
    QgsLayerTreeLayer,
    QgsProcessingAlgorithm,
    QgsProcessingAlgRunnerTask,
    QgsProcessingContext,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
)
from qgis.gui import QgsFileWidget
from qgis.PyQt.QtWidgets import QDialog, QProgressBar, QPushButton

from ..definitions.gui import Panels
from ..qgis_plugin_tools.tools.exceptions import QgsPluginNotImplementedException
from ..qgis_plugin_tools.tools.logger_processing import LoggerProcessingFeedBack
from ..qgis_plugin_tools.tools.resources import plugin_name

LOGGER = logging.getLogger(plugin_name())


class BasePanel:
    """
    Base panel for dialog. Adapted from https://github.com/3liz/QuickOSM
    licenced under GPL version 2
    """

    def __init__(self, dialog: QDialog) -> None:
        self._panel: Optional[Panels] = None
        self._dialog = dialog
        self._name: Optional[str] = None
        self._algorithm: Optional[QgsProcessingAlgorithm] = None
        self.elem_map: Dict[int, bool] = {}
        self.params: Dict[str, Any] = {}
        self.task: Optional[QgsProcessingAlgRunnerTask] = None
        self.context = QgsProcessingContext()
        self.feedback = LoggerProcessingFeedBack(use_logger=True)

    @property
    def panel(self) -> Panels:
        if self._panel:
            return self._panel
        else:
            raise NotImplementedError

    @panel.setter
    def panel(self, panel: Panels) -> None:
        self._panel = panel

    @property
    def dlg(self) -> QDialog:
        """Return the dialog."""
        return self._dialog

    @property
    def name(self) -> str:
        if self._name:
            return self._name
        else:
            raise NotImplementedError

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def algorithm(self) -> QgsProcessingAlgorithm:
        if self._algorithm:
            return self._algorithm
        else:
            raise NotImplementedError

    @algorithm.setter
    def algorithm(self, algorithm: QgsProcessingAlgorithm) -> None:
        self._algorithm = algorithm

    @property
    def __progress_bar(self) -> QProgressBar:
        if self._name:
            return getattr(self.dlg, f"{self._name}_progress_bar")
        else:
            raise NotImplementedError

    @property
    def __btn_run(self) -> QPushButton:
        if self._name:
            return getattr(self.dlg, f"{self._name}_btn_run")
        else:
            raise NotImplementedError

    @property
    def __btn_close(self) -> QPushButton:
        if self._name:
            return getattr(self.dlg, f"{self._name}_btn_close")
        else:
            raise NotImplementedError

    def setup_panel(self) -> None:
        """Setup the UI for the panel."""
        self.__set_run_button()
        self.__btn_close.clicked.connect(self.__close_dialog)

    def teardown_panel(self) -> None:
        """Teardown for the panels"""

    def on_update_map_layers(self) -> None:
        """Occurs when map layers are updated"""

    def is_active(self) -> bool:
        """Is the panel currently active (selected)"""
        curr_panel = list(self.dlg.panels.keys())[self.dlg.menu_widget.currentRow()]
        return curr_panel == self.panel

    def __set_run_button(self) -> None:
        self.__btn_run.setText("Run")
        self.__btn_run.setEnabled(True)
        self.__btn_run.clicked.connect(self.__run_model)
        self.__progress_bar.setValue(0)

    def __update_progress(self, percentage: float) -> None:
        self.__progress_bar.setValue(int(percentage))

    def __delete_task(self, task: QgsProcessingAlgRunnerTask) -> None:
        # This notifies PyQt that the C++ task has been destroyed. Otherwise
        # the Python wrapper will keep pointing to a deleted object.
        # http://enki-editor.org/2014/08/23/Pyqt_mem_mgmt.html
        self.task = None

    def _normalize_weights(self, weights: list) -> list:
        """
        Always sum weights to 1.
        """
        total = sum(weights)
        return [value / total for value in weights]

    def _set_file_extension(self, widget: QgsFileWidget, extension: str) -> None:
        if not widget.filePath().endswith(extension):
            widget.setFilePath(widget.filePath() + extension)

    def _get_params(self) -> dict:
        """Get algorithm parameters from the UI."""
        raise QgsPluginNotImplementedException()

    def _display_results(self, successful: bool, results: Dict[str, Any]) -> None:
        """
        Display result layers in current QGIS project.
        """
        LOGGER.info("got results")
        LOGGER.info(results)
        if successful:
            for layer_name, layer in results.items():
                if layer:
                    # the raster layer will always be a tiff file (temporary or
                    # permanent)
                    result = QgsRasterLayer(layer, layer_name)
                    if not result.isValid():
                        # the result might be a vector layer!
                        result = QgsVectorLayer(layer, layer_name, "ogr")
                        if not result.isValid():
                            # if result path was not set, the vector layer may only be
                            # in memory
                            # Child algorithm results won't actually be passed on:
                            # https://gis.stackexchange.com/questions/361353/store-result-of-a-processing-algorithm-as-a-layer-in-qgis-python-script
                            # If a vector layer is only in memory, we will have to
                            # actually dig it up from the processing context to pass
                            # it on.
                            result = self.context.takeResultLayer(layer)
                    QgsProject.instance().addMapLayer(result, False)
                    root = QgsProject.instance().layerTreeRoot()
                    root.insertChildNode(0, QgsLayerTreeLayer(result))

    def __run_model(self) -> None:
        # prevent clicking run if task is running
        if not self.task:
            # change button to cancel while running
            self.__set_cancel_button()
            # Get the algorithm parameters from subclass
            self.params = self._get_params()
            self.algorithm.initAlgorithm()
            # each task needs its own feedback object! Reusing old feedback
            # will prevent task from being canceled
            self.feedback = LoggerProcessingFeedBack(use_logger=True)
            self.task = QgsProcessingAlgRunnerTask(
                self.algorithm, self.params, self.context, self.feedback
            )
            self.task.progressChanged.connect(self.__update_progress)
            self.task.executed.connect(
                # no more canceling when setting run button again
                lambda successful: self.__btn_run.clicked.disconnect(self.__cancel_run)
            )
            self.task.executed.connect(self.__set_run_button)
            # Display the results
            self.task.executed.connect(self._display_results)
            self.task.destroyed.connect(self.__delete_task)
            QgsApplication.taskManager().addTask(self.task)

    def __set_cancel_button(self) -> None:
        self.__btn_run.setText("Cancel")
        # no more running when pressing cancel
        self.__btn_run.clicked.disconnect(self.__run_model)
        self.__btn_run.clicked.connect(self.__cancel_run)

    def __cancel_run(self) -> None:
        if self.task:
            self.__btn_run.setText("Canceling...")
            self.__btn_run.setEnabled(False)
            self.task.cancel()

    def __close_dialog(self) -> None:
        self.dlg.hide()
