"""
Model exported as python.
Name : Natural Hazard Risks for Schools
Group : Final models
With QGIS : 31600
"""

from typing import Any, Dict, List

import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterCrs,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterVectorLayer,
    QgsRasterLayer,
    QgsVectorLayer,
)

from .base_model import BaseModel


class NaturalHazardRisksForSchools(BaseModel):
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
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                "HazardIndex", "Hazard index", createByDefault=True, defaultValue=None
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "HazardIndexSchools",
                "Hazard Index - Schools",
                type=QgsProcessing.TypeVectorPoint,
                createByDefault=True,
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
            parameters, context, feedback, steps=2 * len(parameters["HazardLayers"]) + 4
        )

        standardized_layers: List[QgsRasterLayer] = []
        # Why do we only reproject rasters but not vectors here?
        for index, hazard_layer in enumerate(parameters["HazardLayers"]):
            # reproject layers to the same CRS so they can be merged
            reprojected = self._reproject_raster_to_crs(
                hazard_layer, self.parameters["ProjectedReferenceSystem"], nodata=0
            )
            if self.feedback.isCanceled():
                return {}

            self.feedback.setCurrentStep(1 + 2 * index)
            standardized_layers.append(self._normalize_layer(reprojected))
            if self.feedback.isCanceled():
                return {}

        self.feedback.setCurrentStep(2 + 2 * index)
        # calculate raster
        sum = self._merge_layers(standardized_layers, parameters["Weights"])
        if self.feedback.isCanceled():
            return {}

        # clip to area if provided
        self.feedback.setCurrentStep(2 * index + 3)
        if self.studyarea:
            hri_result = self._clip_raster_to_studyarea(
                sum, write_to_layer=parameters["HazardIndex"]
            )
        else:
            hri_result = sum
        if self.feedback.isCanceled():
            return {}

        # sample schools if provided
        self.feedback.setCurrentStep(2 * index + 4)
        if parameters["Schools"]:
            if self.studyarea:
                clipped_schools = self._clip_vector_to_studyarea(parameters["Schools"])
            else:
                clipped_schools = parameters["Schools"]
            school_raster_values = self._sample_layer(hri_result, clipped_schools)
        else:
            school_raster_values = None

        return {"HazardIndex": hri_result, "HazardIndexSchools": school_raster_values}

    def _normalize_layer(self, hazard_layer: QgsRasterLayer) -> QgsRasterLayer:
        """
        Scale layer to 0...1.
        """
        alg_params = {
            "BAND": 1,
            "INPUT": hazard_layer,
        }
        statistics = processing.run(
            "native:rasterlayerstatistics",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )

        min = statistics["MIN"]
        max = statistics["MAX"]
        expression = f"(A - {min})/({max} - {min})"
        alg_params = {
            "BAND_A": 1,
            "EXTRA": "",
            "FORMULA": expression,
            "INPUT_A": hazard_layer,
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
            "OUTPUT": self.parameters["HazardIndexSchools"]
            if self.parameters["HazardIndexSchools"]
            else QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "native:rastersampling",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def name(self):
        return "Natural Hazard Risks for Schools"

    def displayName(self):  # noqa: N802
        return "Natural Hazard Risks for Schools"

    def group(self):
        return "Final models"

    def groupId(self):  # noqa: N802
        return "Final models"

    @classmethod
    def shortHelpString(cls):  # noqa: N802
        return """<html><body><h2>Algorithm description</h2>
<p>This algorithm creates a composite hazard risk index by using anywhere from 2 to 6 different raster hazard risk layers. The user can define custom weights (default is 1) for each raster. The result include a raster </p>
<h2>Input parameters</h2>
<h3>Number of risks to compute</h3>
<p>Any whole number between 2 and 6</p>
<h3>Hazard layer 1</h3>
<p></p>
<h3>Weight for Hazard layer 1</h3>
<p></p>
<h3>Hazard layer 2</h3>
<p></p>
<h3>Weight for Hazard layer 2</h3>
<p></p>
<h3>Hazard layer 3</h3>
<p></p>
<h3>Weight for Hazard layer 3</h3>
<p></p>
<h3>Hazard layer 4</h3>
<p></p>
<h3>Weight for Hazard layer 4</h3>
<p></p>
<h3>Hazard layer 5</h3>
<p></p>
<h3>Weight for Hazard layer 5</h3>
<p></p>
<h3>Hazard layer 6</h3>
<p></p>
<h3>Weight for Hazard layer 6</h3>
<p></p>
<h3>Projected Reference System</h3>
<p></p>
<h3>Schools</h3>
<p>A point vector layer with one observation for each school in the area of analysis</p>
<h3>Study area</h3>
<p>A polygon vector layer delimiting the area of analysis.</p>
<h3>Hazard index</h3>
<p></p>
<h3>Layer 1</h3>
<p></p>
<h3>Layer 2</h3>
<p></p>
<h3>Layer 3</h3>
<p></p>
<h3>Hazard Index - Schools</h3>
<p>The original point layer file with the information on the composite hazard index that corresponds to the location of the school</p>
<h2>Outputs</h2>
<h3>Hazard index</h3>
<p></p>
<h3>Layer 1</h3>
<p></p>
<h3>Layer 2</h3>
<p></p>
<h3>Layer 3</h3>
<p></p>
<h3>Hazard Index - Schools</h3>
<p>The original point layer file with the information on the composite hazard index that corresponds to the location of the school</p>
<br><p align="right">Algorithm author: Development unit at IIEP-UNESCO (development@iiep.unesco.org)</p><p align="right">Help author: Development unit at IIEP-UNESCO (development@iiep.unesco.org)</p><p align="right">Algorithm version: 1.0</p></body></html>"""  # noqa

    def helpUrl(self):  # noqa: N802
        return (
            "https://github.com/iiepdev/mcda-site-classification-educational-facilities"
        )

    def createInstance(self):  # noqa: N802
        return NaturalHazardRisksForSchools()
