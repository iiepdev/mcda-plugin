"""
Model exported as python.
Name : Economic suitability
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
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterVectorLayer,
)


class EconomicSuitability(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):  # noqa: N802
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

    def processAlgorithm(self, parameters, context, model_feedback):  # noqa: N802
        # Use a multi-step feedback, so that individual child algorithm progress
        # reports are adjusted for the overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(18, model_feedback)
        results = {}
        outputs = {}

        # Create spatial index
        alg_params = {"INPUT": parameters["SiteAreavector"]}
        outputs["CreateSpatialIndex"] = processing.run(
            "native:createspatialindex",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Fix roads geometries
        alg_params = {
            "INPUT": parameters["Roads"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["FixRoadsGeometries"] = processing.run(
            "native:fixgeometries",
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
            "INPUT": outputs["CreateSpatialIndex"]["OUTPUT"],
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
            "INPUT": outputs["ReprojectLayer"]["OUTPUT"],
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

        # Fix waterways geometries
        alg_params = {
            "INPUT": parameters["Waterways"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["FixWaterwaysGeometries"] = processing.run(
            "native:fixgeometries",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Clip roads
        alg_params = {
            "INPUT": outputs["FixRoadsGeometries"]["OUTPUT"],
            "OVERLAY": outputs["FixGeometries"]["OUTPUT"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["ClipRoads"] = processing.run(
            "native:clip",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Reproject layer - Roads
        alg_params = {
            "INPUT": outputs["ClipRoads"]["OUTPUT"],
            "OPERATION": "",
            "TARGET_CRS": parameters["CRS"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["ReprojectLayerRoads"] = processing.run(
            "native:reprojectlayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Clip waterways
        alg_params = {
            "INPUT": outputs["FixWaterwaysGeometries"]["OUTPUT"],
            "OVERLAY": outputs["FixGeometries"]["OUTPUT"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["ClipWaterways"] = processing.run(
            "native:clip",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Reproject layer - Waterways
        alg_params = {
            "INPUT": outputs["ClipWaterways"]["OUTPUT"],
            "OPERATION": "",
            "TARGET_CRS": parameters["CRS"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["ReprojectLayerWaterways"] = processing.run(
            "native:reprojectlayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Rasterize (vector to raster) - Roads
        alg_params = {
            "BURN": 0,
            "DATA_TYPE": 5,
            "EXTENT": QgsExpression(
                "concat(  @Fix_geometries_OUTPUT_minx  ,',',  @Fix_geometries_OUTPUT_maxx  ,',',  @Fix_geometries_OUTPUT_miny  ,',',  @Fix_geometries_OUTPUT_maxy  ) "  # noqa
            ).evaluate(),
            "EXTRA": "",
            "FIELD": "osm_id",
            "HEIGHT": 100,
            "INIT": None,
            "INPUT": outputs["ReprojectLayerRoads"]["OUTPUT"],
            "INVERT": False,
            "NODATA": 0,
            "OPTIONS": "",
            "UNITS": 1,
            "USE_Z": False,
            "WIDTH": 100,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["RasterizeVectorToRasterRoads"] = processing.run(
            "gdal:rasterize",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Rasterize (vector to raster) - Waterways
        alg_params = {
            "BURN": 0,
            "DATA_TYPE": 5,
            "EXTENT": QgsExpression(
                "concat(  @Fix_geometries_OUTPUT_minx  ,',',  @Fix_geometries_OUTPUT_maxx  ,',',  @Fix_geometries_OUTPUT_miny  ,',',  @Fix_geometries_OUTPUT_maxy  ) "  # noqa
            ).evaluate(),
            "EXTRA": "",
            "FIELD": "osm_id",
            "HEIGHT": 100,
            "INIT": None,
            "INPUT": outputs["ReprojectLayerWaterways"]["OUTPUT"],
            "INVERT": False,
            "NODATA": 0,
            "OPTIONS": "",
            "UNITS": 1,
            "USE_Z": False,
            "WIDTH": 100,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["RasterizeVectorToRasterWaterways"] = processing.run(
            "gdal:rasterize",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Water Proximity
        alg_params = {
            "BAND": 1,
            "DATA_TYPE": 5,
            "EXTRA": "",
            "INPUT": outputs["RasterizeVectorToRasterWaterways"]["OUTPUT"],
            "MAX_DISTANCE": parameters["MaxWaterDistance"],
            "NODATA": parameters["MaxWaterDistance"],
            "OPTIONS": "",
            "REPLACE": 0,
            "UNITS": 0,
            "VALUES": "",
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["WaterProximity"] = processing.run(
            "gdal:proximity",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Road Proximity
        alg_params = {
            "BAND": 1,
            "DATA_TYPE": 5,
            "EXTRA": "",
            "INPUT": outputs["RasterizeVectorToRasterRoads"]["OUTPUT"],
            "MAX_DISTANCE": parameters["MaxRoadDistance"],
            "NODATA": None,
            "OPTIONS": "",
            "REPLACE": 0,
            "UNITS": 0,
            "VALUES": "",
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["RoadProximity"] = processing.run(
            "gdal:proximity",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Water classification
        alg_params = {
            "BAND_A": 1,
            "BAND_B": None,
            "BAND_C": None,
            "BAND_D": None,
            "BAND_E": None,
            "BAND_F": None,
            "EXTRA": "",
            "FORMULA": QgsExpression(
                "CASE\r\nWHEN  @Arelocationsclosetowaterwaysmoresuitable = TRUE THEN\r\nconcat('4*(A >=',to_string( @MaxWaterDistance ),' ) + 3*(A<',to_string( @MaxWaterDistance),')*(A>=',to_string( @MaxWaterDistance*2/3 ),') + 2*(A<',to_string( @MaxWaterDistance*2/3 ),')*(A>=',to_string( @MaxWaterDistance*1/3 ),') + 1*(A<',to_string( @MaxWaterDistance*1/3 ),')*(A>=', to_string(@Minimumsuitabledistancetoawaterway) ,') + 4*(A<',to_string( @Minimumsuitabledistancetoawaterway ),')')   \r\nELSE \r\nconcat('4*(A >=',to_string( @MaxWaterDistance ),' ) + 1*(A<',to_string( @MaxWaterDistance),')*(A>=',to_string( @MaxWaterDistance*2/3 ),') + 2*(A<',to_string( @MaxWaterDistance*2/3 ),')*(A>=',to_string( @MaxWaterDistance*1/3 ),') + 3*(A<',to_string( @MaxWaterDistance*1/3 ),')*(A>=', to_string(@Minimumsuitabledistancetoawaterway) ,') + 4*(A<',to_string( @Minimumsuitabledistancetoawaterway ),')')    \r\nEND "  # noqa
            ).evaluate(),
            "INPUT_A": outputs["WaterProximity"]["OUTPUT"],
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
        outputs["WaterClassification"] = processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Road classification
        alg_params = {
            "BAND_A": 1,
            "BAND_B": None,
            "BAND_C": None,
            "BAND_D": None,
            "BAND_E": None,
            "BAND_F": None,
            "EXTRA": "",
            "FORMULA": QgsExpression(
                "concat('4*(A >=',to_string( @MaxRoadDistance ),' ) + 3*(A<',to_string( @MaxRoadDistance),')*(A>=',to_string( @MaxRoadDistance*2/3 ),') + 2*(A<',to_string( @MaxRoadDistance*2/3 ),')*(A>=',to_string( @MaxRoadDistance*1/3 ),') + 1*(A<',to_string( @MaxRoadDistance*1/3 ),')*(A>=', to_string(@Minimumsuitabledistancetotheroad) ,') + 4*(A<',to_string( @Minimumsuitabledistancetotheroad ),')')"  # noqa
            ).evaluate(),
            "INPUT_A": outputs["RoadProximity"]["OUTPUT"],
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
        outputs["RoadClassification"] = processing.run(
            "gdal:rastercalculator",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Merge
        alg_params = {
            "DATA_TYPE": 5,
            "EXTRA": "",
            "INPUT": QgsExpression(
                "array( @Water_classification_OUTPUT , @Road_classification_OUTPUT )"
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

        feedback.setCurrentStep(16)
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
                "concat('A*', to_string(@WeightforRoads),' + B*',to_string( @WeightforWaterways ))"  # noqa
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

        feedback.setCurrentStep(17)
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
            "TARGET_CRS": None,
            "X_RESOLUTION": None,
            "Y_RESOLUTION": None,
            "OUTPUT": parameters["EconomicSuitability"],
        }
        outputs["ClipRasterByMaskLayer"] = processing.run(
            "gdal:cliprasterbymasklayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        results["EconomicSuitability"] = outputs["ClipRasterByMaskLayer"]["OUTPUT"]
        return results

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
