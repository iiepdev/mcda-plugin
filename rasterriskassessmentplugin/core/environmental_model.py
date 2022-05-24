"""
Model exported as python.
Name : Environmental suitability
Group : Multi-criteria decision analysis
With QGIS : 31600
"""

import processing
from qgis.core import (
    QgsExpression,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterCrs,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
)


class EnvironmentalSuitability(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):  # noqa: N802
        self.addParameter(
            QgsProcessingParameterCrs("CRS", "CRS", defaultValue="EPSG:4326")
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

    def processAlgorithm(self, parameters, context, model_feedback):  # noqa: N802
        # Use a multi-step feedback, so that individual child algorithm progress
        # reports are adjusted for the overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(13, model_feedback)
        results = {}
        outputs = {}

        # Warp slope
        alg_params = {
            "DATA_TYPE": 0,
            "EXTRA": "",
            "INPUT": parameters["DigitalElevationModel"],
            "MULTITHREADING": False,
            "NODATA": None,
            "OPTIONS": "",
            "RESAMPLING": 0,
            "SOURCE_CRS": None,
            "TARGET_CRS": parameters["CRS"],
            "TARGET_EXTENT": None,
            "TARGET_EXTENT_CRS": None,
            "TARGET_RESOLUTION": None,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["WarpSlope"] = processing.run(
            "gdal:warpreproject",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Warp forest
        alg_params = {
            "DATA_TYPE": 0,
            "EXTRA": "",
            "INPUT": parameters["ForestVegetationClassifed"],
            "MULTITHREADING": False,
            "NODATA": None,
            "OPTIONS": "",
            "RESAMPLING": 0,
            "SOURCE_CRS": None,
            "TARGET_CRS": parameters["CRS"],
            "TARGET_EXTENT": None,
            "TARGET_EXTENT_CRS": None,
            "TARGET_RESOLUTION": None,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["WarpForest"] = processing.run(
            "gdal:warpreproject",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Forest classification
        alg_params = {
            "BAND_A": 1,
            "BAND_B": None,
            "BAND_C": None,
            "BAND_D": None,
            "BAND_E": None,
            "BAND_F": None,
            "EXTRA": "",
            "FORMULA": "1*(A<1) + 4*(A>=1)",
            "INPUT_A": outputs["WarpForest"]["OUTPUT"],
            "INPUT_B": None,
            "INPUT_C": None,
            "INPUT_D": None,
            "INPUT_E": None,
            "INPUT_F": None,
            "NO_DATA": None,
            "OPTIONS": "",
            "RTYPE": 1,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["ForestClassification"] = processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Warp multi-hazard
        alg_params = {
            "DATA_TYPE": 0,
            "EXTRA": "",
            "INPUT": parameters["MultiHazardRisk"],
            "MULTITHREADING": False,
            "NODATA": None,
            "OPTIONS": "",
            "RESAMPLING": 0,
            "SOURCE_CRS": None,
            "TARGET_CRS": parameters["CRS"],
            "TARGET_EXTENT": None,
            "TARGET_EXTENT_CRS": None,
            "TARGET_RESOLUTION": None,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["WarpMultihazard"] = processing.run(
            "gdal:warpreproject",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(4)
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

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Raster layer statistics
        alg_params = {"BAND": 1, "INPUT": outputs["WarpMultihazard"]["OUTPUT"]}
        outputs["RasterLayerStatistics"] = processing.run(
            "native:rasterlayerstatistics",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Slope
        alg_params = {
            "AS_PERCENT": False,
            "BAND": 1,
            "COMPUTE_EDGES": False,
            "EXTRA": "",
            "INPUT": outputs["WarpSlope"]["OUTPUT"],
            "OPTIONS": "",
            "SCALE": 1,
            "ZEVENBERGEN": False,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["Slope"] = processing.run(
            "gdal:slope",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Raster calculator
        alg_params = {
            "BAND_A": 1,
            "BAND_B": None,
            "BAND_C": None,
            "BAND_D": None,
            "BAND_E": None,
            "BAND_F": None,
            "EXTRA": "",
            "FORMULA": QgsExpression(
                "concat('(A - ',to_string(replace(to_string(  @Raster_layer_statistics_MIN  ),'.',',')),')/(',to_string(replace(to_string(  @Raster_layer_statistics_MAX  ),'.',',')),' - ',to_string(replace(to_string(  @Raster_layer_statistics_MIN  ),'.',',')),')*4')"  # noqa
            ).evaluate(),
            "INPUT_A": outputs["WarpMultihazard"]["OUTPUT"],
            "INPUT_B": None,
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

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Hazard classification
        alg_params = {
            "BAND_A": 1,
            "BAND_B": None,
            "BAND_C": None,
            "BAND_D": None,
            "BAND_E": None,
            "BAND_F": None,
            "EXTRA": "",
            "FORMULA": "1*(A<=1) + 2*(A>1)*(A<=2) + 3*(A>2)*(A<=3) + 4*(A>3)",
            "INPUT_A": outputs["RasterCalculator"]["OUTPUT"],
            "INPUT_B": None,
            "INPUT_C": None,
            "INPUT_D": None,
            "INPUT_E": None,
            "INPUT_F": None,
            "NO_DATA": None,
            "OPTIONS": "",
            "RTYPE": 1,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["HazardClassification"] = processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Slope classification
        alg_params = {
            "BAND_A": 1,
            "BAND_B": None,
            "BAND_C": None,
            "BAND_D": None,
            "BAND_E": None,
            "BAND_F": None,
            "EXTRA": "",
            "FORMULA": "1*(A<1) + 2*(A>=1)*(A<10) + 3*(A>=10)*(A<20) + 4*(A>=20)",
            "INPUT_A": outputs["Slope"]["OUTPUT"],
            "INPUT_B": None,
            "INPUT_C": None,
            "INPUT_D": None,
            "INPUT_E": None,
            "INPUT_F": None,
            "NO_DATA": None,
            "OPTIONS": "",
            "RTYPE": 1,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["SlopeClassification"] = processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Merge
        alg_params = {
            "DATA_TYPE": 4,
            "EXTRA": "",
            "INPUT": QgsExpression(
                "array( @Forest_classification_OUTPUT , @Hazard_classification_OUTPUT , @Slope_classification_OUTPUT )"  # noqa
            ).evaluate(),
            "NODATA_INPUT": None,
            "NODATA_OUTPUT": None,
            "OPTIONS": "",
            "PCT": True,
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

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Raster calculator
        alg_params = {
            "BAND_A": 1,
            "BAND_B": 2,
            "BAND_C": 3,
            "BAND_D": None,
            "BAND_E": None,
            "BAND_F": None,
            "EXTRA": "",
            "FORMULA": QgsExpression(
                "concat('A*', to_string(@WeightforVegetation) ,' + B*', to_string(@WeightforMultiHazardRisk) ,' + C*',  to_string(@WeightforElevation) )"  # noqa
            ).evaluate(),
            "INPUT_A": outputs["Merge"]["OUTPUT"],
            "INPUT_B": outputs["Merge"]["OUTPUT"],
            "INPUT_C": outputs["Merge"]["OUTPUT"],
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

        feedback.setCurrentStep(12)
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
            "MASK": outputs["FixGeometries"]["OUTPUT"],
            "MULTITHREADING": False,
            "NODATA": None,
            "OPTIONS": "",
            "SET_RESOLUTION": False,
            "SOURCE_CRS": None,
            "TARGET_CRS": parameters["CRS"],
            "X_RESOLUTION": None,
            "Y_RESOLUTION": None,
            "OUTPUT": parameters["EnvironmentalSuitability"],
        }
        outputs["ClipRasterByMaskLayer"] = processing.run(
            "gdal:cliprasterbymasklayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        results["EnvironmentalSuitability"] = outputs["ClipRasterByMaskLayer"]["OUTPUT"]
        return results

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
