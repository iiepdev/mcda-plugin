"""
Model exported as python.
Name : Social suitability
Group : Multi-criteria decision analysis
With QGIS : 31600
"""

import processing
from qgis.core import (
    QgsExpression,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
)


class SocialSuitability(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):  # noqa: N802
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

    def processAlgorithm(self, parameters, context, model_feedback):  # noqa: N802
        # Use a multi-step feedback, so that individual child algorithm progress
        # reports are adjusted for the overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(12, model_feedback)
        results = {}
        outputs = {}

        # Population classification
        alg_params = {
            "BAND_A": 1,
            "BAND_B": None,
            "BAND_C": None,
            "BAND_D": None,
            "BAND_E": None,
            "BAND_F": None,
            "EXTRA": "",
            "FORMULA": QgsExpression(
                "CASE\r\nWHEN  @Newschoolsshouldideallybelocatedinsparselypopulatedareas = TRUE THEN '1*(A < 100)'\r\nELSE '1*(A > 100)'\r\nEND"  # noqa
            ).evaluate(),
            "INPUT_A": parameters["PopulationDensity"],
            "INPUT_B": None,
            "INPUT_C": None,
            "INPUT_D": None,
            "INPUT_E": None,
            "INPUT_F": None,
            "NO_DATA": None,
            "OPTIONS": "",
            "RTYPE": 4,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["PopulationClassification"] = processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Fill NoData cells
        alg_params = {
            "BAND": 1,
            "FILL_VALUE": 4,
            "INPUT": outputs["PopulationClassification"]["OUTPUT"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["FillNodataCells"] = processing.run(
            "native:fillnodata",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Reproject layer
        alg_params = {
            "INPUT": parameters["Existingschoollocations"],
            "OPERATION": "",
            "TARGET_CRS": parameters["CRS"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["ReprojectLayer"] = processing.run(
            "native:reprojectlayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Fix geometries
        alg_params = {
            "INPUT": parameters["SiteAreavector"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["FixGeometries"] = processing.run(
            "native:fixgeometries",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Rasterize (vector to raster)
        alg_params = {
            "BURN": 0,
            "DATA_TYPE": 5,
            "EXTENT": QgsExpression(
                "concat(  @Reproject_site_area_OUTPUT_minx ,',', @Reproject_site_area_OUTPUT_maxx ,',', @Reproject_site_area_OUTPUT_miny ,',', @Reproject_site_area_OUTPUT_maxy  )"  # noqa
            ).evaluate(),
            "EXTRA": "",
            "FIELD": parameters["Identifyingschoolvariable"],
            "HEIGHT": 100,
            "INIT": None,
            "INPUT": outputs["ReprojectLayer"]["OUTPUT"],
            "INVERT": False,
            "NODATA": 0,
            "OPTIONS": "",
            "UNITS": 1,
            "USE_Z": False,
            "WIDTH": 100,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["RasterizeVectorToRaster"] = processing.run(
            "gdal:rasterize",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Reproject site area
        alg_params = {
            "INPUT": outputs["FixGeometries"]["OUTPUT"],
            "OPERATION": "",
            "TARGET_CRS": parameters["CRS"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["ReprojectSiteArea"] = processing.run(
            "native:reprojectlayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # School Proximity
        alg_params = {
            "BAND": 1,
            "DATA_TYPE": 5,
            "EXTRA": "",
            "INPUT": outputs["RasterizeVectorToRaster"]["OUTPUT"],
            "MAX_DISTANCE": parameters["MaxDistancefromExistingSchools"],
            "NODATA": parameters["MaxDistancefromExistingSchools"],
            "OPTIONS": "",
            "REPLACE": 0,
            "UNITS": 0,
            "VALUES": "",
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["SchoolProximity"] = processing.run(
            "gdal:proximity",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Clip raster by mask layer
        alg_params = {
            "ALPHA_BAND": False,
            "CROP_TO_CUTLINE": True,
            "DATA_TYPE": 0,
            "EXTRA": "",
            "INPUT": outputs["FillNodataCells"]["OUTPUT"],
            "KEEP_RESOLUTION": False,
            "MASK": outputs["ReprojectSiteArea"]["OUTPUT"],
            "MULTITHREADING": False,
            "NODATA": None,
            "OPTIONS": "",
            "SET_RESOLUTION": False,
            "SOURCE_CRS": None,
            "TARGET_CRS": parameters["CRS"],
            "X_RESOLUTION": None,
            "Y_RESOLUTION": None,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["ClipRasterByMaskLayer"] = processing.run(
            "gdal:cliprasterbymasklayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # School classification
        alg_params = {
            "BAND_A": 1,
            "BAND_B": None,
            "BAND_C": None,
            "BAND_D": None,
            "BAND_E": None,
            "BAND_F": None,
            "EXTRA": "",
            "FORMULA": QgsExpression(
                "CASE\r\nWHEN  @Newschoolsshouldbelocatedfurthefromrfromexistingschoolsratherthanclosetothem  = TRUE THEN concat('4*(A<= ',to_string(  @Minimumsuitabledistancetoanotherschool ),') + 3*(A > ',to_string(  @Minimumsuitabledistancetoanotherschool ),')*(A <= ',to_string(   @MaxDistancefromExistingSchools/3  ),') + 2*(A > ',to_string(   @MaxDistancefromExistingSchools/3  ),')*(A  < ',to_string(   @MaxDistancefromExistingSchools*2/3  ),')+ 1*(A > ',to_string(   @MaxDistancefromExistingSchools*2/3  ),')*(A < ',to_string( @MaxDistancefromExistingSchools ),') + 4*(A >= ',to_string( @MaxDistancefromExistingSchools ),')')\r\nELSE concat('4*(A<= ',to_string(  @Minimumsuitabledistancetoanotherschool ),') + 1*(A > ',to_string(  @Minimumsuitabledistancetoanotherschool ),')*(A <= ',to_string(   @MaxDistancefromExistingSchools/3  ),') + 2*(A > ',to_string(   @MaxDistancefromExistingSchools/3  ),')*(A  < ',to_string(   @MaxDistancefromExistingSchools*2/3  ),')+ 3*(A > ',to_string(   @MaxDistancefromExistingSchools*2/3  ),')*(A < ',to_string( @MaxDistancefromExistingSchools ),') + 4*(A >= ',to_string( @MaxDistancefromExistingSchools ),')')\r\nEND"  # noqa
            ).evaluate(),
            "INPUT_A": outputs["SchoolProximity"]["OUTPUT"],
            "INPUT_B": None,
            "INPUT_C": None,
            "INPUT_D": None,
            "INPUT_E": None,
            "INPUT_F": None,
            "NO_DATA": None,
            "OPTIONS": "",
            "RTYPE": 4,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["SchoolClassification"] = processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Merge
        alg_params = {
            "DATA_TYPE": 5,
            "EXTRA": "",
            "INPUT": QgsExpression(
                "array( @School_classification_OUTPUT ,  @Clip_raster_by_mask_layer_OUTPUT  )"  # noqa
            ).evaluate(),
            "NODATA_INPUT": None,
            "NODATA_OUTPUT": None,
            "OPTIONS": "",
            "PCT": False,
            "SEPARATE": True,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["Merge"] = processing.run(
            "gdal:merge",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Raster calculator
        alg_params = {
            "BAND_A": 1,
            "BAND_B": 2,
            "BAND_C": None,
            "BAND_D": None,
            "BAND_E": None,
            "BAND_F": None,
            "EXTRA": "",
            "FORMULA": QgsExpression(
                "concat('A*', to_string(@WeightforRoads) ,' + B*', to_string(@WeightforPopulation) )"  # noqa
            ).evaluate(),
            "INPUT_A": outputs["Merge"]["OUTPUT"],
            "INPUT_B": outputs["Merge"]["OUTPUT"],
            "INPUT_C": None,
            "INPUT_D": None,
            "INPUT_E": None,
            "INPUT_F": None,
            "NO_DATA": None,
            "OPTIONS": "",
            "RTYPE": 5,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["RasterCalculator"] = processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Clip raster by mask layer
        alg_params = {
            "ALPHA_BAND": False,
            "CROP_TO_CUTLINE": True,
            "DATA_TYPE": 0,
            "EXTRA": "",
            "INPUT": outputs["RasterCalculator"]["OUTPUT"],
            "KEEP_RESOLUTION": False,
            "MASK": outputs["ReprojectSiteArea"]["OUTPUT"],
            "MULTITHREADING": False,
            "NODATA": None,
            "OPTIONS": "",
            "SET_RESOLUTION": False,
            "SOURCE_CRS": None,
            "TARGET_CRS": parameters["CRS"],
            "X_RESOLUTION": None,
            "Y_RESOLUTION": None,
            "OUTPUT": parameters["SocialSuitability"],
        }
        outputs["ClipRasterByMaskLayer"] = processing.run(
            "gdal:cliprasterbymasklayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        results["SocialSuitability"] = outputs["ClipRasterByMaskLayer"]["OUTPUT"]
        return results

    def name(self):
        return "Social suitability"

    def displayName(self):  # noqa: N802
        return "Social suitability"

    def group(self):
        return "Multi-criteria decision analysis"

    def groupId(self):  # noqa: N802
        return "Multi-criteria decision analysis"

    def createInstance(self):  # noqa: N802
        return SocialSuitability()
