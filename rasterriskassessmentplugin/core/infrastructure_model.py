"""
Model exported as python.
Name : Social suitability
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
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
)

from .base_model import BaseModel


class InfrastructureSuitability(BaseModel):
    def initAlgorithm(self, config=None):  # noqa: N802
        # TODO: add rest of the proper parameters if we want to use the algorithm in
        # QGIS processing tool?
        self.addParameter(
            QgsProcessingParameterCrs("CRS", "CRS", defaultValue="EPSG:4326")
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "Existingschoollocations",
                "Existing school locations",
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                "Identifyingschoolvariable",
                "Identifying school variable",
                type=QgsProcessingParameterField.Numeric,
                parentLayerParameterName="Existingschoollocations",
                allowMultiple=False,
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "MaxDistancefromExistingSchools",
                "Maximum suitable distance to another school",
                type=QgsProcessingParameterNumber.Integer,
                minValue=0,
                maxValue=10000,
                defaultValue=1500,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "Minimumsuitabledistancetoanotherschool",
                "Minimum suitable distance to another school",
                type=QgsProcessingParameterNumber.Integer,
                minValue=0,
                maxValue=100000,
                defaultValue=50,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                "Newschoolsshouldbelocatedfurthefromrfromexistingschoolsratherthanclosetothem",  # noqa
                "New schools should be located further from existing schools, rather than close to them",  # noqa
                defaultValue=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "WeightforRoads",
                "Weight for Schools",
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                maxValue=1,
                defaultValue=0.5,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                "PopulationDensity", "Population Density", defaultValue=None
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                "Newschoolsshouldideallybelocatedinsparselypopulatedareas",
                "New schools should ideally be located in sparsely populated areas",
                defaultValue=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "WeightforPopulation",
                "Weight for Population",
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                maxValue=1,
                defaultValue=0.5,
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
                "SocialSuitability",
                "Social suitability",
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

        # first clip to area if provided. This will speed up the raster calculation
        # significantly, and lower the file size.
        if self.studyarea:
            clipped_population = self._clip_raster_to_studyarea(
                parameters["PopulationDensity"]
            )
            clipped_schools = self._clip_vector_to_studyarea(parameters["Schools"])
        else:
            clipped_population = parameters["PopulationDensity"]
            clipped_schools = parameters["Schools"]
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(1)
        # reproject layers to the same CRS so they can be merged
        projected_population = self._reproject_raster_to_crs(
            clipped_population, self.parameters["ProjectedReferenceSystem"]
        )
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(2)
        # density to 1-bit bitmap (plus nodata, so we'll use 8bit for now)
        thresholded_population = self._classify_by_threshold(
            projected_population,
            parameters["PopulationThreshold"],
            parameters["Newschoolsshouldideallybelocatedinsparselypopulatedareas"],
        )
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(3)
        # Rasterize (vector to raster)
        rasterized_schools = self._rasterize_vector(clipped_schools)
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(4)
        # School proximity and classification
        school_classification = self._classify_by_distance(
            rasterized_schools,
            parameters["Minimumsuitabledistancetoanotherschool"],
            parameters["MaxDistancefromExistingSchools"],
            further_is_better=parameters[
                "Newschoolsshouldbelocatedfurtherfromexistingschoolsratherthanclosetothem"  # noqa
            ],
            # if schools further away are favored, too_far areas should have class 1
            too_far_classification=1
            if parameters[
                "Newschoolsshouldbelocatedfurtherfromexistingschoolsratherthanclosetothem"  # noqa
            ]
            else 4,
        )
        if self.feedback.isCanceled():
            return {}

        self.feedback.setCurrentStep(5)
        sum = self._merge_layers(
            [school_classification, thresholded_population],
            [self.parameters["SchoolWeight"], self.parameters["PopWeight"]],
            write_to_layer=self.parameters["InfrastructureSuitability"],
        )
        return {"InfrastructureSuitability": sum}

    def name(self):
        return "Social suitability"

    def displayName(self):  # noqa: N802
        return "Social suitability"

    def group(self):
        return "Multi-criteria decision analysis"

    def groupId(self):  # noqa: N802
        return "Multi-criteria decision analysis"

    @classmethod
    def shortHelpString(cls):  # noqa: N802
        return """<html><body><h2>Algorithm description</h2>
<p> Help menu to be added... </p>
<h2>Input parameters</h2>
<h2>Outputs</h2>
<br><p align="right">Algorithm author: Development unit at IIEP-UNESCO (development@iiep.unesco.org)</p><p align="right">Help author: Development unit at IIEP-UNESCO (development@iiep.unesco.org)</p><p align="right">Algorithm version: 1.0</p></body></html>"""  # noqa

    def createInstance(self):  # noqa: N802
        return InfrastructureSuitability()
