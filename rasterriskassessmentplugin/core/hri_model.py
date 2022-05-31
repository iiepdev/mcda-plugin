"""
Model exported as python.
Name : Natural Hazard Risks for Schools
Group : Final models
With QGIS : 31600
"""

import os
import sys
from typing import List

import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingFeedback,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterCrs,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterVectorLayer,
    QgsRasterLayer,
    QgsVectorLayer,
)

# Mac OS PROJ path fix until https://github.com/qgis/QGIS-Mac-Packager/issues/151 is
# resolved
if "darwin" in sys.platform:
    os.environ["PROJ_LIB"] = os.environ["GDAL_DATA"].replace("/gdal", "/proj")


class NaturalHazardRisksForSchools(QgsProcessingAlgorithm):
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
        self, parameters, context, model_feedback
    ) -> dict:
        # Use a multi-step feedback, so that individual child algorithm progress
        # reports are adjusted for the overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(
            2 * len(parameters["HazardLayers"]) + 6, model_feedback
        )
        self.feedback: QgsProcessingFeedback = feedback
        self.parameters = parameters
        self.context = context
        standardized_layers: List[QgsRasterLayer] = []

        for index, hazard_layer in enumerate(parameters["HazardLayers"]):
            reprojected = self.__reproject_layer(hazard_layer)
            feedback.setCurrentStep(1 + 2 * index)
            if feedback.isCanceled():
                return {}

            standardized_layers.append(self.__normalize_layer(reprojected))
            feedback.setCurrentStep(2 + 2 * index)
            if feedback.isCanceled():
                return {}

        clipped_schools = self.__clip_vector_layer(
            parameters["Schools"], parameters["Studyarea"]
        )
        feedback.setCurrentStep(2 * index + 3)
        if feedback.isCanceled():
            return {}

        sum = self.__merge_layers(standardized_layers, parameters["Weights"])
        feedback.setCurrentStep(2 * index + 4)
        if feedback.isCanceled():
            return {}

        hri_result = self.__clip_raster_layer(sum, parameters["Studyarea"])

        feedback.setCurrentStep(2 * index + 5)
        if feedback.isCanceled():
            return {}

        school_raster_values = self.__sample_layer(hri_result, clipped_schools)

        return {"HazardIndex": hri_result, "HazardIndexSchools": school_raster_values}

    def __reproject_layer(self, hazard_layer: QgsRasterLayer) -> QgsRasterLayer:
        """
        Reproject layer to the HRI CRS. Also set layer nodata value to zero.
        """
        alg_params = {
            "DATA_TYPE": 0,
            "EXTRA": "",
            "INPUT": hazard_layer,
            "MULTITHREADING": False,
            "NODATA": 0,
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

    def __normalize_layer(self, hazard_layer: QgsRasterLayer) -> QgsRasterLayer:
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

    def __clip_vector_layer(
        self, input: QgsVectorLayer, overlay: QgsVectorLayer
    ) -> QgsVectorLayer:
        """
        Clip input layer with overlay.
        """
        alg_params = {
            "INPUT": input,
            "OVERLAY": overlay,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "native:clip",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def __clip_raster_layer(
        self, input: QgsRasterLayer, mask: QgsVectorLayer
    ) -> QgsRasterLayer:
        """
        Clip input layer with mask.
        """
        alg_params = {
            "ALPHA_BAND": False,
            "CROP_TO_CUTLINE": True,
            "DATA_TYPE": 0,
            "EXTRA": "",
            "INPUT": input,
            "KEEP_RESOLUTION": False,
            "MASK": mask,
            "MULTITHREADING": False,
            "NODATA": None,
            "OPTIONS": "",
            "SET_RESOLUTION": False,
            "SOURCE_CRS": None,
            "TARGET_CRS": None,
            "X_RESOLUTION": None,
            "Y_RESOLUTION": None,
            "OUTPUT": self.parameters["HazardIndex"]
            if self.parameters["HazardIndex"]
            else QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "gdal:cliprasterbymasklayer",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def __sample_layer(
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

    def __merge_layers(
        self, layers: List[QgsRasterLayer], weights: List[float]
    ) -> QgsRasterLayer:
        """
        Merge raster layers together and calculate their weighted sum.
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
