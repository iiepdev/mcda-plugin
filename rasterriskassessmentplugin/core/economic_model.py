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
<p>This algorithm creates a composite economic suitability 
index for the education system of a particular region. It 
considers the suitability of a location depending on its 
proximity to the road network and to waterways. The user can 
define custom weights for each input. The result produces a 
raster ranging from 1 to 4, where 1 is Less suitable and 4 is 
More suitable.</p>
<h2>Input parameters</h2>
<h3>Roads</h3>
<p>A vector layer containing the road network for a particular 
region. The program assumes that all roads are equally useful 
for learners to go to school, so the user should only include 
those that suit this use before using this algorithm. The use 
of OpenStreetMap is encouraged when possible.</p>
<h3>Maximum suitable distance to a road</h3>
<p>Positive number describing the maximum Euclidian distance 
from the road where a school can be (or still be) considered a 
suitable location. If no such distance exists, the user can input 
a very large number.</p>
<h3>Minimum suitable distance to the road</h3>
<p>Positive number describing the minimum Euclidian distance from 
the road a school can be (or still be) considered a suitable location. 
If no such distance exists, the user can input 0.</p>
<h3>Are locations close to roads more suitable than locations further 
away from roads?</h3>
<p>This dichotomous option will take the suitable range (between the 
minimum and maximum distance from the road specified above) and determine 
whether high suitability should start closer or further to the road network. 
An illustrated example of this is presented in Figure 15 of  Vargas Mesa, 
Sheldon, Gagnon (forthcoming).</p>
<h3>Weight for the road sub-component</h3>
<p>Make sure that the sum of "Weight for the road sub-component" and "Weight 
for waterways sub-component" is equal to 100%.</p>
<h3>Waterways</h3>
<p>A vector layer containing the waterways network for a particular region. 
The program assumes that all waterways are equally useful for learners to go 
to school, fetching water, etc., so the user should only include those that 
suit this use before using this algorithm. The use of OpenStreetMap is 
encouraged when possible.</p>
<h3>Maximum suitable distance to a waterway</h3>
<p>Positive number describing the maximum Euclidian distance from the waterway 
a school can be to still be considered a suitable condition. If no such distance 
exists, the user can input a very large number. </p>
<h3>Minimum suitable distance to a waterway</h3>
<p>Positive number describing the minimum Euclidian distance from the waterway a 
school can be to still be considered a suitable condition. If no such distance 
exists, the user can input 0.</p>
<h3>Are locations close to waterways more suitable than locations further 
away from waterways?</h3>
<p>This dichotomous option will take the suitable range (between the minimum 
and maximum distance from the waterway specified above) and determine whether 
suitability should start closer or further to the waterway network. An illustrated 
example of this is presented in Figure 15 of Vargas Mesa, Sheldon, 
Gagnon (forthcoming).</p>
<h3>Weight for the waterways sub-component</h3>
<p>Make sure that the sum of "Weight for the road sub-component" and "Weight for 
waterways sub-component" is equal to 100%.</p>
<h3>Area of analysis</h3>
<p>A polygon vector layer delimiting the area of analysis.</p>
<h3>Projected reference system</h3>
<p>Select a local projected reference system. Note that failing to do so might 
lead to inaccuracies when calculations are performed far from the equator. </p>
<h2>Outputs</h2>
<h3>Economic suitability</h3>
<p>Raster layer ranging from 1 (More suitable) to 4 (Less suitable)</p>
<br><p>Algorithm author: Development team (development@iiep.unesco.org)</p>
<p>Help author: Development team (development@iiep.unesco.org)</p>
<p>Algorithm version: 1.0</p></body></html>"""

    def helpUrl(self):  # noqa: N802
        return (
            "https://github.com/iiepdev/mcda-site-classification-educational-facilities"
        )

    def createInstance(self):  # noqa: N802
        return EconomicSuitability()
