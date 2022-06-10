"""
Model exported as python.
Name : Economic suitability
Group : Multi-criteria decision analysis
With QGIS : 31600
"""

from typing import Any, Dict

from qgis.core import (
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterVectorLayer,
)

from .base_model import BaseModel


class EconomicSuitability(BaseModel):
    def initAlgorithm(self, config=None):  # noqa: N802
        # TODO: add rest of the proper parameters if we want to use the algorithm in
        # QGIS processing tool?
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "Roads",
                "Roads",
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "MaxRoadDistance",
                "Maximum suitable distance to a road",
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                maxValue=1.79769e308,
                defaultValue=500,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "Minimumsuitabledistancetotheroad",
                "Minimum suitable distance to the road",
                type=QgsProcessingParameterNumber.Integer,
                minValue=0,
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "WeightforRoads",
                "Weight for the road sub-component",
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                maxValue=1,
                defaultValue=0.5,
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "Waterways",
                "Waterways",
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "MaxWaterDistance",
                "Maximum suitable distance to a waterway",
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                maxValue=1.79769e308,
                defaultValue=500,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "Minimumsuitabledistancetoawaterway",
                "Minimum suitable distance to a waterway",
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                "Arelocationsclosetowaterwaysmoresuitable",
                "Are locations close to waterways more suitable than locations further away from waterways?",  # noqa
                defaultValue=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "WeightforWaterways",
                "Weight for the waterways sub-component",
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                maxValue=1,
                defaultValue=0.5,
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "SiteAreavector",
                "Area of analysis",
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                "CRS", "Projected reference system", defaultValue="EPSG:4326"
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                "EconomicSuitability",
                "Economic suitability",
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
        self.startAlgorithm(parameters, context, feedback, steps=5)

        # Fix roads geometries
        roads = self._fix_vector_layer(parameters["Roads"])
        # Fix waterways geometries
        waterways = self._fix_vector_layer(parameters["Waterways"])
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(1)
        # Clip if studyarea given
        if self.studyarea:
            roads = self._clip_vector_to_studyarea(roads)
            waterways = self._clip_vector_to_studyarea(waterways)
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(2)
        # Rasterize
        rasterized_roads = self._rasterize_vector(roads)
        rasterized_waterways = self._rasterize_vector(waterways)
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(3)
        # Classify
        road_classification = self._classify_by_distance(
            rasterized_roads,
            parameters["Minimumsuitabledistancetotheroad"],
            parameters["MaxRoadDistance"],
            not parameters["Arelocationsclosetoroadsmoresuitable"],
        )
        waterway_classification = self._classify_by_distance(
            rasterized_waterways,
            parameters["Minimumsuitabledistancetoawaterway"],
            parameters["MaxWaterDistance"],
            not parameters["Arelocationsclosetowaterwaysmoresuitable"],
        )
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(4)
        sum = self._merge_layers(
            [road_classification, waterway_classification],
            [self.parameters["WeightforRoads"], self.parameters["WeightforWaterways"]],
            write_to_layer=self.parameters["EconomicSuitability"],
        )
        return {"EconomicSuitability": sum}

    def name(self):
        return "Economic suitability"

    def displayName(self):  # noqa: N802
        return "Economic suitability"

    def group(self):
        return "Multi-criteria decision analysis"

    def groupId(self):  # noqa: N802
        return "Multi-criteria decision analysis"

    @classmethod
    def shortHelpString(cls):  # noqa: N802
        return """<html><body><h2>Algorithm description</h2>
<p></p>
<h2>Input parameters</h2>
<h3>Roads</h3>
<p></p>
<h3>Maximum suitable distance to a road</h3>
<p></p>
<h3>Minimum suitable distance to the road</h3>
<p></p>
<h3>Weight for the road sub-component</h3>
<p>Make sure that the sum of "Weight for Roads" and "Weight for Waterways" is equal to 1.</p>
<h3>Waterways</h3>
<p></p>
<h3>Maximum suitable distance to a waterway</h3>
<p></p>
<h3>Minimum suitable distance to a waterway</h3>
<p></p>
<h3>Are locations close to waterways more suitable than locations further away from waterways?</h3>
<p></p>
<h3>Weight for the waterways sub-component</h3>
<p>Make sure that the sum of "Weight for Roads" and "Weight for Waterways" is equal to 1.</p>
<h3>Area of analysis</h3>
<p></p>
<h3>Projected reference system</h3>
<p></p>
<h3>Economic suitability</h3>
<p></p>
<h2>Outputs</h2>
<h3>Economic suitability</h3>
<p></p>
<br><p align="right">Algorithm author: Development team (development@iiep.unesco.org)</p><p align="right">Help author: Development team (development@iiep.unesco.org)</p><p align="right">Algorithm version: 1.0</p></body></html>"""  # noqa

    def helpUrl(self):  # noqa: N802
        return (
            "https://github.com/iiepdev/mcda-site-classification-educational-facilities"
        )

    def createInstance(self):  # noqa: N802
        return EconomicSuitability()
