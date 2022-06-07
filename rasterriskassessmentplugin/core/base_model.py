import os
import sys
from typing import Any, Dict, List, Optional

import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
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
        Each algorithm must define process.
        """
        raise NotImplementedError()

    def _clip_vector_to_studyarea(self, input: QgsVectorLayer) -> QgsVectorLayer:
        """
        Clip vector layer to algorithm study area.
        """
        alg_params = {
            "INPUT": input,
            "OVERLAY": self.parameters["Studyarea"],
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
        self, input: QgsRasterLayer, write_to_layer: Optional[QgsRasterLayer] = None
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
            "MASK": self.parameters["Studyarea"],
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
            "TARGET_CRS": self.parameters["ProjectedReferenceSystem"],
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

    def _merge_layers(
        self, layers: List[QgsRasterLayer], weights: List[float]
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
            "OPTIONS": "hideNoData",
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

    def _rasterize_vector(self, input: QgsVectorLayer) -> QgsRasterLayer:
        """
        Rasterize input layer within the model study area.

        The vector rasterization assumes the coordinate system will have units
        of approximately one meter. The more the coordinate system unit differs
        from meter, the larger the error in all distances.

        Since the study size can be small or large, the default is EPSG:3857. That way
        we will get 100x100m resolution on the equator and larger away from the
        equator. Similarly, the extent has to be calculated in the same crs.
        """
        area_projected = self._reproject_vector_to_crs(
            self.parameters["Studyarea"], self.parameters["ProjectedReferenceSystem"]
        )
        input_projected = self._reproject_vector_to_crs(
            input, self.parameters["ProjectedReferenceSystem"]
        )
        extent = area_projected.extent()
        self.feedback.pushInfo(str(extent.area()))
        self.feedback.pushInfo(
            f"{extent.xMinimum()},{extent.xMaximum()},{extent.yMinimum()},{extent.yMaximum()}"  # noqa
        )
        alg_params = {
            "BURN": 0,
            "DATA_TYPE": 5,
            "EXTENT": f"{extent.xMinimum()},{extent.xMaximum()},{extent.yMinimum()},{extent.yMaximum()}",  # noqa
            "EXTRA": "",
            "FIELD": self.parameters[
                "Identifyingschoolvariable"
            ],  # why do we want to save the school id??
            "HEIGHT": 100,  # 100x100 meter resolution with ideal PRS
            "INIT": None,
            "INPUT": input_projected,
            "INVERT": False,
            "NODATA": 0,
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
            "NO_DATA": None,
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
