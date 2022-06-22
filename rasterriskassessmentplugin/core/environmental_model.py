"""
Model exported as python.
Name : Environmental suitability
Group : Multi-criteria decision analysis
With QGIS : 31600
"""
from typing import Any, Dict

import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterCrs,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
    QgsRasterLayer,
)

from .base_model import BaseModel


class EnvironmentalSuitability(BaseModel):
    def initAlgorithm(self, config=None):  # noqa: N802
        self.addParameter(
            QgsProcessingParameterCrs(
                "ProjectedReferenceSystem", "CRS", defaultValue="EPSG:3857"
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                "MultiHazardRisk", "Multi-Hazard Risk", defaultValue=None
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "WeightforMultiHazardRisk",
                "Weight for Multi-Hazard Risk",
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                maxValue=1,
                defaultValue=0.33,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                "DigitalElevationModel", "Digital Elevation Model", defaultValue=None
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "WeightforElevation",
                "Weight for Elevation",
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                maxValue=1,
                defaultValue=0.33,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                "ForestVegetationClassifed", "Forest/ Vegetation", defaultValue=None
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "WeightforVegetation",
                "Weight for Vegetation",
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                maxValue=1,
                defaultValue=0.33,
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "SiteAreavector",
                "Site Area (vector)",
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                "EnvironmentalSuitability",
                "Environmental suitability",
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
        self.startAlgorithm(parameters, context, feedback, steps=6)

        # Reproject
        dem = self._reproject_raster_to_crs(
            parameters["DigitalElevationModel"], self.projected_reference_system
        )
        forest = self._reproject_raster_to_crs(
            parameters["ForestVegetationClassified"], self.projected_reference_system
        )
        hri = self._reproject_raster_to_crs(
            parameters["MultiHazardRisk"], self.projected_reference_system
        )
        if feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(1)
        # Forest classification (4 if forest is too dense, otherwise 1)
        classified_forest = self._classify_by_threshold(
            forest, 1, invert=True, nodata_suitability=1
        )
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(2)
        # We want to divide hri equally to classes 1, 2, 3 and 4
        # Standardize from min...max to 0...4, rounding up
        # Allow no pixels exactly zero (round up to 1).
        classified_hri = self._classify_by_value(hri)
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(3)
        # Slope classification
        slope_index = self._classify_by_slope(dem)
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(4)
        # calculate raster
        sum = self._merge_layers(
            [slope_index, classified_forest, classified_hri],
            [
                parameters["WeightforElevation"],
                parameters["WeightforVegetation"],
                parameters["WeightforMultiHazardRisk"],
            ],
        )
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(5)
        # clip to area if provided
        if self.studyarea:
            result = self._clip_raster_to_studyarea(
                sum, write_to_layer=parameters["EnvironmentalSuitability"]
            )
        else:
            result = sum
        return {"EnvironmentalSuitability": result}

    def _calculate_slope(self, dem: QgsRasterLayer) -> QgsRasterLayer:
        """
        Calculate slope from dem raster layer. The layer has to be in
        a metric projected coordinate system.
        """
        alg_params = {
            "AS_PERCENT": False,
            "BAND": 1,
            "COMPUTE_EDGES": False,
            "EXTRA": "",
            "INPUT": dem,
            "OPTIONS": "",
            "SCALE": 1,
            "ZEVENBERGEN": False,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        return processing.run(
            "gdal:slope",
            alg_params,
            context=self.context,
            feedback=self.feedback,
            is_child_algorithm=True,
        )["OUTPUT"]

    def _classify_by_slope(self, dem: QgsRasterLayer) -> QgsRasterLayer:
        """
        Classify DEM layer from suitable (1) to unsuitable (4) and in between,
        based on the slope in the model. The layer has to be in
        a metric projected coordinate system.
        """
        slope = self._calculate_slope(dem)
        expression = "1*(A<1) + 2*(A>=1)*(A<10) + 3*(A>=10)*(A<20) + 4*(A>=20)"
        alg_params = {
            "BAND_A": 1,
            "EXTRA": "",
            "FORMULA": expression,
            "INPUT_A": slope,
            "NO_DATA": None,
            "OPTIONS": "",
            "RTYPE": 1,
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
        return "Environmental suitability"

    def displayName(self):  # noqa: N802
        return "Environmental suitability"

    def group(self):
        return "Multi-criteria decision analysis"

    def groupId(self):  # noqa: N802
        return "Multi-criteria decision analysis"

    def createInstance(self):  # noqa: N802
        return EnvironmentalSuitability()

    @classmethod
    def shortHelpString(cls):  # noqa: N802
        return """<html><body><h2>Algorithm description</h2>
<p> Help menu to be added... </p>
<h2>Input parameters</h2>
<h2>Outputs</h2>
<br><p align="right">Algorithm author: Development unit at IIEP-UNESCO (development@iiep.unesco.org)</p><p align="right">Help author: Development unit at IIEP-UNESCO (development@iiep.unesco.org)</p><p align="right">Algorithm version: 1.0</p></body></html>"""  # noqa
