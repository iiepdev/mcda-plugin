import os
import sys
from typing import Any, Dict, List, Optional

import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingMultiStepFeedback,
    QgsRasterLayer,
    QgsVectorLayer,
)

# Mac OS PROJ path fix until https://github.com/qgis/QGIS-Mac-Packager/issues/151 is
# resolved
if "darwin" in sys.platform:
    os.environ["PROJ_LIB"] = os.environ["GDAL_DATA"].replace("/gdal", "/proj")


class BaseModel(QgsProcessingAlgorithm):
    """
    This class contains methods that are common in all processing algorithms.
    """

    def __init__(self) -> None:
        super().__init__()
        self.parameters: Dict[str, Any] = {}
        self.studyarea: Optional[QgsVectorLayer] = None
        self.projected_reference_system: str = "EPSG:3857"

    def initAlgorithm(self, configuration: Dict[str, Any] = ...) -> None:  # noqa: N802
        """
        Each algorithm must define some processing params.
        """
        raise NotImplementedError()

    def processAlgorithm(  # noqa: N802
        self,
        parameters: Dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> Dict[str, Any]:
        """
        Each algorithm must define a process.
        """
        raise NotImplementedError()

    def startAlgorithm(  # noqa: N802
        self,
        parameters: Dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
        steps: int,
    ) -> None:
        """
        Here we do things that should be run at the start of any process.
        """
        # Use a multi-step feedback, so that individual child algorithm progress
        # reports are adjusted for the overall progress through the model
        self.feedback = QgsProcessingMultiStepFeedback(steps, feedback)
        self.parameters = parameters
        self.context = context
        if parameters["ProjectedReferenceSystem"]:
            self.projected_reference_system = parameters["ProjectedReferenceSystem"]
        if parameters["Studyarea"]:
            # In case there are problems (self-intersections) in the area vector, we
            # want to fix them before proceeding.
            self.studyarea = self._fix_vector_layer(parameters["Studyarea"])
            # Also indexing the study area may help in speeding up??
            # self.studyarea = self._create_spatial_index(self.studyarea)

    def _create_spatial_index(self, input: QgsVectorLayer) -> QgsVectorLayer:
        """
        Add spatial index to input layer
        """
        alg_params = {"INPUT": input}
        return processing.run(
            "native:createspatialindex",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def _fix_vector_layer(self, input: QgsVectorLayer) -> QgsVectorLayer:
        """
        Fix self-intersections
        """
        alg_params = {
            "INPUT": input,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "native:fixgeometries",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def _clip_vector_to_studyarea(self, input: QgsVectorLayer) -> QgsVectorLayer:
        """
        Clip vector layer to algorithm study area.
        """
        alg_params = {
            "INPUT": input,
            "OVERLAY": self.studyarea,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "native:clip",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def _clip_raster_to_studyarea(
        self, input: QgsRasterLayer, write_to_layer: Optional[str] = None
    ) -> QgsRasterLayer:
        """
        Clip raster layer to algorithm study area.
        """
        alg_params = {
            "ALPHA_BAND": False,
            "CROP_TO_CUTLINE": True,
            "DATA_TYPE": 0,
            "EXTRA": "",
            "INPUT": input,
            "KEEP_RESOLUTION": False,
            "MASK": self.studyarea,
            "MULTITHREADING": False,
            "NODATA": None,
            "OPTIONS": "",
            "SET_RESOLUTION": False,
            "SOURCE_CRS": None,
            "TARGET_CRS": None,
            "X_RESOLUTION": None,
            "Y_RESOLUTION": None,
            "OUTPUT": write_to_layer
            if write_to_layer
            else QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "gdal:cliprasterbymasklayer",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def _reproject_vector_to_crs(
        self, input: QgsVectorLayer, crs: str
    ) -> QgsVectorLayer:
        """
        Reproject vector layer to given crs.
        """
        alg_params = {
            "INPUT": input,
            "OPERATION": "",
            "TARGET_CRS": crs,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        # memory vector layer has to be dug up from the processing context again
        return self.context.takeResultLayer(
            processing.run(
                "native:reprojectlayer",
                alg_params,
                context=self.context,
                feedback=self.feedback,
                is_child_algorithm=True,
            )["OUTPUT"]
        )

    def _reproject_raster_to_crs(
        self, input: QgsRasterLayer, crs: str, nodata: int = None
    ) -> QgsRasterLayer:

        """
        Reproject raster layer to given CRS. Optionally, set nodata to desired value.
        """
        alg_params = {
            "DATA_TYPE": 0,
            "EXTRA": "",
            "INPUT": input,
            "MULTITHREADING": False,
            "NODATA": nodata,
            "OPTIONS": "",
            "RESAMPLING": 0,
            "SOURCE_CRS": None,
            "TARGET_CRS": crs,
            "TARGET_EXTENT": None,
            "TARGET_EXTENT_CRS": None,
            "TARGET_RESOLUTION": None,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "gdal:warpreproject",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def _get_layer_statistics(self, layer: QgsRasterLayer) -> Dict[str, float]:
        """
        Get raster layer statistics.
        """
        alg_params = {
            "BAND": 1,
            "INPUT": layer,
        }
        statistics = processing.run(
            "native:rasterlayerstatistics",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )
        return statistics

    def _normalize_layer(self, layer: QgsRasterLayer) -> QgsRasterLayer:
        """
        Scale layer to 0...1.
        """
        statistics = self._get_layer_statistics(layer)
        min = statistics["MIN"]
        max = statistics["MAX"]
        expression = f"(A - {min})/({max} - {min})"
        alg_params = {
            "BAND_A": 1,
            "EXTRA": "",
            "FORMULA": expression,
            "INPUT_A": layer,
            "NO_DATA": None,
            "OPTIONS": "",
            "RTYPE": 5,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def _merge_layers(
        self,
        layers: List[QgsRasterLayer],
        weights: List[float],
        write_to_layer: Optional[str] = None,
    ) -> QgsRasterLayer:
        """
        Merge raster layers together and calculate their weighted sum. Note
        that the layers have to be normalized or otherwise use common units.

        Note that all the raster layers must have the same CRS. They are not
        reprojected here.
        """

        # Merge to separate channels
        alg_params = {
            "DATA_TYPE": 5,
            "EXTRA": "",
            "INPUT": layers,
            "NODATA_INPUT": None,
            "NODATA_OUTPUT": None,
            "OPTIONS": "",
            "PCT": False,
            "SEPARATE": True,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        merged = processing.run(
            "gdal:merge",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        # Raster calculator
        band_params = {}
        input_params = {}
        expression_parts = []
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for index in range(0, len(layers)):
            band_params[f"BAND_{alphabet[index]}"] = index + 1
            input_params[f"INPUT_{alphabet[index]}"] = merged
            expression_parts.append(f"{alphabet[index]}*{weights[index]}")
        sum_expression = "+".join(expression_parts)
        alg_params = {
            **band_params,
            "EXTRA": "",
            "FORMULA": sum_expression,
            **input_params,
            "NO_DATA": None,
            "OPTIONS": "",
            "RTYPE": 5,
            "OUTPUT": write_to_layer
            if write_to_layer
            else QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def _rasterize_vector(self, input: QgsVectorLayer) -> QgsRasterLayer:
        """
        Rasterize input layer within the model study area.

        The vector rasterization assumes projected_reference_system will have units
        of approximately one meter. The more the coordinate system unit differs
        from meter, the larger the error in all distances.

        Since the study size can be small or large, the default is EPSG:3857. That way
        we will get 100x100m resolution on the equator and larger away from the
        equator. Similarly, the extent has to be calculated in the same crs.
        """
        area_projected = self._reproject_vector_to_crs(
            self.studyarea, self.projected_reference_system
        )
        input_projected = self._reproject_vector_to_crs(
            input, self.projected_reference_system
        )
        extent = area_projected.extent()
        self.feedback.pushInfo(str(extent.area()))
        self.feedback.pushInfo(
            f"{extent.xMinimum()},{extent.xMaximum()},{extent.yMinimum()},{extent.yMaximum()}"  # noqa
        )
        alg_params = {
            "BURN": 1,  # Just burn any non-zero value
            "DATA_TYPE": 5,
            "EXTENT": f"{extent.xMinimum()},{extent.xMaximum()},{extent.yMinimum()},{extent.yMaximum()}",  # noqa
            "EXTRA": "",
            "HEIGHT": 100,  # 100x100 meter resolution with ideal PRS
            "INIT": None,
            "INPUT": input_projected,
            "INVERT": False,
            "NODATA": 0,  # Zero (no schools in pixel) must be nodata in our result!
            "OPTIONS": "",
            "UNITS": 1,  # 100x100 meter resolution with ideal PRS
            "USE_Z": False,
            "WIDTH": 100,  # 100x100 meter resolution with ideal PRS
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "gdal:rasterize",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def _proximity_map(
        self, input: QgsRasterLayer, max_distance: float
    ) -> QgsRasterLayer:
        """
        Create proximity map to non-zero pixels in the input layer.
        """
        alg_params = {
            "BAND": 1,
            "DATA_TYPE": 5,
            "EXTRA": "",
            "INPUT": input,
            "MAX_DISTANCE": max_distance,
            "NODATA": max_distance,
            "OPTIONS": "",
            "REPLACE": 0,
            "UNITS": 0,
            "VALUES": "",
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "gdal:proximity",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def _classify_by_distance(
        self,
        input: QgsRasterLayer,
        min_distance: float,
        max_distance: float,
        further_is_better: bool = False,
    ) -> QgsRasterLayer:
        """
        Returns area classification raster around location raster input. Input
        layer is assumed to be in a projected CRS with units in meters. Points within
        min_distance or outside max_distance will be given classification 4.

        input: Raster layer in a projected CRS to classify.
        min_distance: Minimum acceptable distance in meters for classification 1-3.
        max_distance: Maximum acceptable distance in meters for classification 1-3.
        further_is_better: Whether class will decrease or increase by distance.
        """
        proximity_layer = self._proximity_map(input, max_distance)
        # concentric buffers around input non-zero pixels will have different
        # suitability values
        too_close = f"(A <= {min_distance})"
        self.feedback.pushInfo(too_close)
        close = f"(A > {min_distance})*(A <= {max_distance/3})"
        self.feedback.pushInfo(close)
        medium = f"(A > {max_distance/3})*(A < 2*{max_distance}/3)"
        self.feedback.pushInfo(medium)
        far = f"(A >= 2*{max_distance/3})*(A < {max_distance})"
        self.feedback.pushInfo(far)
        too_far = f"(A >= {max_distance})"
        self.feedback.pushInfo(too_far)
        if further_is_better:
            expression = (
                f"4*{too_close} + 3*{close} + 2*{medium} + 1*{far} + 4*{too_far}"
            )
        else:
            expression = (
                f"4*{too_close} + 1*{close} + 2*{medium} + 3*{far} + 4*{too_far}"
            )
        self.feedback.pushInfo(expression)
        alg_params = {
            "BAND_A": 1,
            "EXTRA": "",
            "FORMULA": expression,
            "INPUT_A": proximity_layer,
            "NO_DATA": None,  # The result will not have nodata pixels
            "OPTIONS": "",
            "RTYPE": 4,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def _fill_nodata(self, input: QgsRasterLayer, value: int) -> QgsRasterLayer:
        """
        Fill nodata values with desired value.
        """
        alg_params = {
            "BAND": 1,
            "FILL_VALUE": value,
            "INPUT": input,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "native:fillnodata",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def _classify_by_threshold(
        self, input: QgsRasterLayer, threshold: int, invert: bool = False
    ) -> QgsRasterLayer:
        """
        Classify raster to suitable (1) or unsuitable (4) by threshold value.
        """
        # returns 0 (below 100) or 1 (above 100). However, nodata values will be
        # set to default 8bit nodata, i.e. 255!
        # vs. original algorithm had rtype=4 (Int32), which has nodata value -2147483647
        expression = f"A < {threshold}" if invert else f"A > {threshold}"
        # invert: False returns 0 (below 100) or 1 (above 100) or 4 (zero density)
        # invert: True returns 0 (above 100) or 1 (below 100) or 4 (zero density)
        # 0 will always be the best, i.e. the result is opposite to that intended!!
        # Nodata will always be the worst.
        alg_params = {
            "BAND_A": 1,
            "EXTRA": "",
            "FORMULA": expression,
            "INPUT_A": input,
            "NO_DATA": 0,
            # None-setting will result in three index values (0, 1 and 4)
            # after setting nodata to 4 in next step.
            # Is this intentional??
            "OPTIONS": "",
            "RTYPE": 0,  # We don't want a huge 32bit geotiff
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        thresholded = processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]
        filled_and_thresholded = self._fill_nodata(thresholded, 4)
        return filled_and_thresholded

    def _classify_by_value(self, layer: QgsRasterLayer) -> QgsRasterLayer:
        """
        Classify raster from suitable (1) to unsuitable (4) and in between,
        dividing positive value range to four parts.
        """
        # First we need layer statistics
        statistics = self._get_layer_statistics(layer)
        min = statistics["MIN"]
        max = statistics["MAX"]
        scale = 4
        # Use the ceiling function to get the scale 1 to 4.
        # However, index values of exactly zero must be handled separately to
        # map to 1.
        expression = f"ceil({scale}*(A - {min})/({max} - {min}))*(A > 0) + (A == 0)"
        alg_params = {
            "BAND_A": 1,
            "EXTRA": "",
            "FORMULA": expression,
            "INPUT_A": layer,
            "NO_DATA": None,
            "OPTIONS": "",
            "RTYPE": 5,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]
