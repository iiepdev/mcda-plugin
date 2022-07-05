from typing import Any, Dict, List

import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterCrs,
    QgsProcessingParameterVectorLayer,
    QgsRasterLayer,
    QgsVectorLayer,
)

from .base_model import BaseModel


class CombineRasters(BaseModel):
    """
    This class implements algorithm for summing multiple raster
    layers with different weights and adjustable parameters.
    """

    def initAlgorithm(self, config=None):  # noqa: N802
        # TODO: add rest of the proper parameters if we want to use the algorithm in
        # QGIS processing tool?
        self.addParameter(
            QgsProcessingParameterCrs(
                "ProjectedReferenceSystem",
                "Projected Reference System",
                defaultValue="EPSG:4326",
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "Schools",
                "Schools",
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "Studyarea",
                "Study area",
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None,
            )
        )

    def processAlgorithm(  # noqa: N802
        self,
        parameters: Dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> Dict[str, Any]:
        self.startAlgorithm(
            parameters, context, feedback, steps=2 * len(parameters["Layers"]) + 4
        )

        layers: List[QgsRasterLayer] = []
        # Why do we only reproject rasters but not vectors here?
        for index, layer in enumerate(parameters["Layers"]):
            # reproject layers to the same CRS so they can be merged
            reprojected = self._reproject_raster_to_crs(
                layer, self.projected_reference_system, nodata=0
            )
            if self.feedback.isCanceled():
                return {}

            self.feedback.setCurrentStep(1 + 2 * index)
            if parameters["NormalizeLayers"]:
                layers.append(self._normalize_layer(reprojected))
            else:
                layers.append(reprojected)
            if self.feedback.isCanceled():
                return {}

        self.feedback.setCurrentStep(2 + 2 * index)
        # calculate raster
        sum = self._merge_layers(layers, parameters["Weights"])
        if self.feedback.isCanceled():
            return {}

        # clip to area if provided
        self.feedback.setCurrentStep(2 * index + 3)
        if self.studyarea:
            result = self._clip_raster_to_studyarea(
                sum, write_to_layer=parameters["OutputRaster"]
            )
        else:
            result = sum
        if self.feedback.isCanceled():
            return {}

        # sample schools if provided
        self.feedback.setCurrentStep(2 * index + 4)
        if "Schools" in parameters and parameters["Schools"]:
            if self.studyarea:
                clipped_schools = self._clip_vector_to_studyarea(parameters["Schools"])
            else:
                clipped_schools = parameters["Schools"]
            school_raster_values = self._sample_layer(result, clipped_schools)
        else:
            school_raster_values = None

        return {
            parameters["LayerNames"]["OutputRaster"]: result,
            parameters["LayerNames"]["SampledOutput"]: school_raster_values,
        }

    def _sample_layer(
        self, layer: QgsRasterLayer, points: QgsVectorLayer
    ) -> QgsVectorLayer:
        """
        Sample raster layer at vector layer points.
        """
        # Sample raster values
        alg_params = {
            "COLUMN_PREFIX": "HazardIndex",
            "INPUT": points,
            "RASTERCOPY": layer,
            "OUTPUT": self.parameters["SampledOutput"]
            if self.parameters["SampledOutput"]
            else QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "native:rastersampling",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]
