"""
Model exported as python.
Name : Natural Hazard Risks for Schools
Group : Final models
With QGIS : 31600
"""

import os
import sys

import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterCrs,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterVectorLayer,
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

    def processAlgorithm(self, parameters, context, model_feedback):  # noqa: N802
        # Use a multi-step feedback, so that individual child algorithm progress
        # reports are adjusted for the overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(
            3 * len(parameters["HazardLayers"]) + 7, model_feedback
        )
        standardized_layers = []

        for index, hazard_layer in enumerate(parameters["HazardLayers"]):
            # Reproject hazard layer
            # Note that nodata must be 0 on all layers!!
            alg_params = {
                "DATA_TYPE": 0,
                "EXTRA": "",
                "INPUT": hazard_layer,
                "MULTITHREADING": False,
                "NODATA": 0,
                "OPTIONS": "",
                "RESAMPLING": 0,
                "SOURCE_CRS": None,
                "TARGET_CRS": parameters["ProjectedReferenceSystem"],
                "TARGET_EXTENT": None,
                "TARGET_EXTENT_CRS": None,
                "TARGET_RESOLUTION": None,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            }
            reprojected = processing.run(
                "gdal:warpreproject",
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )["OUTPUT"]

            feedback.setCurrentStep(1 + 3 * index)
            if feedback.isCanceled():
                return {}

            # Raster layer statistics
            alg_params = {
                "BAND": 1,
                "INPUT": reprojected,
            }
            statistics = processing.run(
                "native:rasterlayerstatistics",
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )

            feedback.setCurrentStep(2 + 3 * index)
            if feedback.isCanceled():
                return {}

            # Standardizing layer
            min = statistics["MIN"]
            max = statistics["MAX"]
            expression = f"(A - {min})/({max} - {min})"
            alg_params = {
                "BAND_A": 1,
                "EXTRA": "",
                "FORMULA": expression,
                "INPUT_A": reprojected,
                "NO_DATA": None,
                "OPTIONS": "",
                "RTYPE": 5,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            }
            standardized_layers.append(
                processing.run(
                    "gdal:rastercalculator",
                    alg_params,
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True,
                )["OUTPUT"]
            )

            feedback.setCurrentStep(3 + 3 * index)
            if feedback.isCanceled():
                return {}

        # Clip
        alg_params = {
            "INPUT": parameters["Schools"],
            "OVERLAY": parameters["Studyarea"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        clipped_schools = processing.run(
            "native:clip",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        feedback.setCurrentStep(3 * index + 4)
        if feedback.isCanceled():
            return {}

        # Merge but in separate channels
        alg_params = {
            "DATA_TYPE": 5,
            "EXTRA": "",
            "INPUT": standardized_layers,
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
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        feedback.setCurrentStep(3 * index + 5)
        if feedback.isCanceled():
            return {}

        # Raster calculator
        band_params = {}
        input_params = {}
        expression_parts = []
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for index in range(0, len(parameters["HazardLayers"])):
            band_params[f"BAND_{alphabet[index]}"] = index + 1
            input_params[f"INPUT_{alphabet[index]}"] = merged
            expression_parts.append(f"{alphabet[index]}*{parameters['Weights'][index]}")
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
        sum = processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        feedback.setCurrentStep(3 * index + 6)
        if feedback.isCanceled():
            return {}

        feedback.pushWarning(str(parameters))
        # Clip raster by mask layer
        alg_params = {
            "ALPHA_BAND": False,
            "CROP_TO_CUTLINE": True,
            "DATA_TYPE": 0,
            "EXTRA": "",
            "INPUT": sum,
            "KEEP_RESOLUTION": False,
            "MASK": parameters["Studyarea"],
            "MULTITHREADING": False,
            "NODATA": None,
            "OPTIONS": "",
            "SET_RESOLUTION": False,
            "SOURCE_CRS": None,
            "TARGET_CRS": None,
            "X_RESOLUTION": None,
            "Y_RESOLUTION": None,
            "OUTPUT": parameters["HazardIndex"].dataProvider().dataSourceUri()
            if parameters["HazardIndex"]
            else QgsProcessing.TEMPORARY_OUTPUT,
        }
        hri_result = processing.run(
            "gdal:cliprasterbymasklayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

        feedback.setCurrentStep(3 * index + 7)
        if feedback.isCanceled():
            return {}

        # Sample raster values
        alg_params = {
            "COLUMN_PREFIX": "HazardIndex",
            "INPUT": clipped_schools,
            "RASTERCOPY": sum,
            "OUTPUT": parameters["HazardIndexSchools"].dataProvider().dataSourceUri()
            if parameters["HazardIndexSchools"]
            else QgsProcessing.TEMPORARY_OUTPUT,
        }
        school_raster_values = processing.run(
            "native:rastersampling",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )["OUTPUT"]
        return hri_result, school_raster_values

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
