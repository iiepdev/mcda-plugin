"""
Model exported as python.
Name : Social suitability
Group : Multi-criteria decision analysis
With QGIS : 31600
"""

from typing import Any, Dict

import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
    QgsRasterLayer,
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
        # Use a multi-step feedback, so that individual child algorithm progress
        # reports are adjusted for the overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(7, feedback)
        self.feedback = feedback
        self.parameters = parameters
        self.context = context

        # first clip to area if provided. This will speed up the raster calculation
        # significantly, and lower the file size.
        if parameters["Studyarea"]:
            clipped_population = self._clip_raster_to_studyarea(
                parameters["PopulationDensity"]
            )
            clipped_schools = self._clip_vector_to_studyarea(parameters["Schools"])
        else:
            clipped_population = parameters["PopulationDensity"]
            clipped_schools = parameters["Schools"]
        if feedback.isCanceled():
            return {}

        feedback.setCurrentStep(1)
        # reproject layers to the same CRS so they can be merged
        projected_population = self._reproject_raster_to_crs(
            clipped_population, self.parameters["ProjectedReferenceSystem"]
        )
        if feedback.isCanceled():
            return {}

        feedback.setCurrentStep(2)
        # density to 1-bit bitmap (plus nodata, so we'll use 8bit for now)
        thresholded_population = self._classify_by_threshold(
            projected_population,
            100,
            parameters["Newschoolsshouldideallybelocatedinsparselypopulatedareas"],
        )
        if feedback.isCanceled():
            return {}

        feedback.setCurrentStep(3)
        # this will set sparsely populated to 0, urban to 1, non-populated to 0.
        # Is this intentional? I thought 0 is not part of the index.
        filled_population = self._fill_nodata(thresholded_population, 4)
        if feedback.isCanceled():
            return {}

        # TODO: Why do we need to fix area vector here? HRI didn't do that.
        # # Fix geometries
        # alg_params = {
        #     "INPUT": parameters["SiteAreavector"],
        #     "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        # }
        # outputs["FixGeometries"] = processing.run(
        #     "native:fixgeometries",
        #     alg_params,
        #     context=context,
        #     feedback=feedback,
        #     is_child_algorithm=True,
        # )

        # feedback.setCurrentStep(4)
        # if feedback.isCanceled():
        #     return {}

        feedback.setCurrentStep(4)
        # Rasterize (vector to raster)
        rasterized_schools = self._rasterize_vector(clipped_schools)
        if feedback.isCanceled():
            return {}

        feedback.setCurrentStep(5)
        # School proximity and classification
        school_classification = self._classify_by_distance(
            rasterized_schools,
            parameters["Minimumsuitabledistancetoanotherschool"],
            parameters["MaxDistancefromExistingSchools"],
            parameters[
                "Newschoolsshouldbelocatedfurtherfromexistingschoolsratherthanclosetothem"  # noqa
            ],
        )
        if feedback.isCanceled():
            return {}

        feedback.setCurrentStep(6)
        sum = self._merge_layers(
            [school_classification, filled_population],
            [self.parameters["SchoolWeight"], self.parameters["PopWeight"]],
        )
        return {"InfrastructureIndex": sum}
        # Merge
        # alg_params = {
        #     "DATA_TYPE": 5,
        #     "EXTRA": "",
        #     "INPUT": QgsExpression(
        #         "array( @School_classification_OUTPUT ,  @Clip_raster_by_mask_layer_OUTPUT  )"  # noqa
        #     ).evaluate(),
        #     "NODATA_INPUT": None,
        #     "NODATA_OUTPUT": None,
        #     "OPTIONS": "",
        #     "PCT": False,
        #     "SEPARATE": True,
        #     "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        # }
        # outputs["Merge"] = processing.run(
        #     "gdal:merge",
        #     alg_params,
        #     context=context,
        #     feedback=feedback,
        #     is_child_algorithm=True,
        # )
        # if feedback.isCanceled():
        #     return {}

        # # Raster calculator
        # alg_params = {
        #     "BAND_A": 1,
        #     "BAND_B": 2,
        #     "BAND_C": None,
        #     "BAND_D": None,
        #     "BAND_E": None,
        #     "BAND_F": None,
        #     "EXTRA": "",
        #     "FORMULA": QgsExpression(
        #         "concat('A*', to_string(@WeightforRoads) ,' + B*', to_string(@WeightforPopulation) )"  # noqa
        #     ).evaluate(),
        #     "INPUT_A": outputs["Merge"]["OUTPUT"],
        #     "INPUT_B": outputs["Merge"]["OUTPUT"],
        #     "INPUT_C": None,
        #     "INPUT_D": None,
        #     "INPUT_E": None,
        #     "INPUT_F": None,
        #     "NO_DATA": None,
        #     "OPTIONS": "",
        #     "RTYPE": 5,
        #     "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        # }
        # outputs["RasterCalculator"] = processing.run(
        #     "gdal:rastercalculator",
        #     alg_params,
        #     context=context,
        #     feedback=feedback,
        #     is_child_algorithm=True,
        # )

        # feedback.setCurrentStep(11)
        # if feedback.isCanceled():
        #     return {}

        # Clip raster by mask layer
        # alg_params = {
        #     "ALPHA_BAND": False,
        #     "CROP_TO_CUTLINE": True,
        #     "DATA_TYPE": 0,
        #     "EXTRA": "",
        #     "INPUT": outputs["RasterCalculator"]["OUTPUT"],
        #     "KEEP_RESOLUTION": False,
        #     "MASK": outputs["ReprojectSiteArea"]["OUTPUT"],
        #     "MULTITHREADING": False,
        #     "NODATA": None,
        #     "OPTIONS": "",
        #     "SET_RESOLUTION": False,
        #     "SOURCE_CRS": None,
        #     "TARGET_CRS": parameters["CRS"],
        #     "X_RESOLUTION": None,
        #     "Y_RESOLUTION": None,
        #     "OUTPUT": parameters["SocialSuitability"],
        # }
        # outputs["ClipRasterByMaskLayer"] = processing.run(
        #     "gdal:cliprasterbymasklayer",
        #     alg_params,
        #     context=context,
        #     feedback=feedback,
        #     is_child_algorithm=True,
        # )
        # results["SocialSuitability"] = outputs["ClipRasterByMaskLayer"]["OUTPUT"]
        # return results

    def _classify_by_threshold(
        self, input: QgsRasterLayer, threshold: int, invert: bool = False
    ) -> QgsRasterLayer:
        """
        Classify raster to 1-bit by threshold value
        """
        expression = f"A < {threshold}" if invert else f"A > {threshold}"
        # TODO: ask if we really mean to map all zeros to four, so we will get 1 OR 4?
        # Why don't we do it in the expression above, is the nodata solution below
        # easier?
        # a) This way, all non-inhabited and sparsely populated areas will get best
        # index value (1).
        # b) OR do we mean to set sparsely populated to 1 and BOTH non-inhabited
        # (no-data) AND densely populated to 4?
        alg_params = {
            "BAND_A": 1,
            "EXTRA": "",
            "FORMULA": expression,
            "INPUT_A": input,
            "NO_DATA": None,  # OR 0?
            # Current None-setting will result in three index values (0, 1 and 4)
            # after setting nodata to 4 in next step.
            # Is this intentional??
            "OPTIONS": "",
            "RTYPE": 0,  # We don't want a huge 32bit geotiff
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

    def name(self):
        return "Social suitability"

    def displayName(self):  # noqa: N802
        return "Social suitability"

    def group(self):
        return "Multi-criteria decision analysis"

    def groupId(self):  # noqa: N802
        return "Multi-criteria decision analysis"

    def createInstance(self):  # noqa: N802
        return InfrastructureSuitability()
