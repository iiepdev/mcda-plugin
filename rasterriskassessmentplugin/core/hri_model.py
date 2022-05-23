"""
Model exported as python.
Name : Natural Hazard Risks for Schools
Group : Final models
With QGIS : 31600
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterCrs
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression
import processing


class NaturalHazardRisksForSchools(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterNumber('Numberofriskstocompute', 'Number of risks to compute', type=QgsProcessingParameterNumber.Integer, minValue=2, maxValue=6, defaultValue=6))
        self.addParameter(QgsProcessingParameterRasterLayer('Hazardlayer1', 'Hazard layer 1', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('WeightforHazardlayer1', 'Weight for Hazard layer 1', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=1))
        self.addParameter(QgsProcessingParameterRasterLayer('Hazardlayer2', 'Hazard layer 2', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('WeightforHazardlayer2', 'Weight for Hazard layer 2', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=1))
        self.addParameter(QgsProcessingParameterRasterLayer('Hazardlayer3', 'Hazard layer 3', optional=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('WeightforHazardlayer3', 'Weight for Hazard layer 3', optional=True, type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=1))
        self.addParameter(QgsProcessingParameterRasterLayer('Hazardlayer4', 'Hazard layer 4', optional=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('WeightforHazardlayer4', 'Weight for Hazard layer 4', optional=True, type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=1))
        self.addParameter(QgsProcessingParameterRasterLayer('Hazardlayer5', 'Hazard layer 5', optional=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('WeightforHazardlayer5', 'Weight for Hazard layer 5', optional=True, type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=1))
        self.addParameter(QgsProcessingParameterRasterLayer('Hazardlayer6', 'Hazard layer 6', optional=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('WeightforHazardlayer6', 'Weight for Hazard layer 6', optional=True, type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=1))
        self.addParameter(QgsProcessingParameterCrs('ProjectedReferenceSystem', 'Projected Reference System', defaultValue='EPSG:4326'))
        self.addParameter(QgsProcessingParameterVectorLayer('Schools', 'Schools', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('Studyarea', 'Study area', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('HazardIndex', 'Hazard index', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Layer1', 'Layer 1', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Layer2', 'Layer 2', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Layer3', 'Layer 3', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('HazardIndexSchools', 'Hazard Index - Schools', type=QgsProcessing.TypeVectorPoint, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(27, model_feedback)
        results = {}
        outputs = {}

        # Reproject hazard layer 1
        alg_params = {
            'DATA_TYPE': 0,
            'EXTRA': '',
            'INPUT': parameters['Hazardlayer1'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,
            'SOURCE_CRS': None,
            'TARGET_CRS': parameters['ProjectedReferenceSystem'],
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectHazardLayer1'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Has at least 6 hazard risks
        alg_params = {
        }
        outputs['HasAtLeast6HazardRisks'] = processing.run('native:condition', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Has at least 4 hazard risks
        alg_params = {
        }
        outputs['HasAtLeast4HazardRisks'] = processing.run('native:condition', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Raster layer statistics layer 1
        alg_params = {
            'BAND': 1,
            'INPUT': outputs['ReprojectHazardLayer1']['OUTPUT']
        }
        outputs['RasterLayerStatisticsLayer1'] = processing.run('native:rasterlayerstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Has at least 3 hazard risks
        alg_params = {
        }
        outputs['HasAtLeast3HazardRisks'] = processing.run('native:condition', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Standardizing layer 1
        alg_params = {
            'BAND_A': 1,
            'BAND_B': None,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': QgsExpression('concat(\'(A - \',to_string(replace(to_string(  @Raster_layer_statistics_layer_1_MIN  ),\'.\',\',\')),\')/(\',to_string(replace(to_string(  @Raster_layer_statistics_layer_1_MAX  ),\'.\',\',\')),\' - \',to_string(replace(to_string(  @Raster_layer_statistics_layer_1_MIN  ),\'.\',\',\')),\')*4\')').evaluate(),
            'INPUT_A': outputs['ReprojectHazardLayer1']['OUTPUT'],
            'INPUT_B': None,
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,
            'OUTPUT': parameters['Layer1']
        }
        outputs['StandardizingLayer1'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Layer1'] = outputs['StandardizingLayer1']['OUTPUT']

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Has at least 5 hazard risks
        alg_params = {
        }
        outputs['HasAtLeast5HazardRisks'] = processing.run('native:condition', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Clip
        alg_params = {
            'INPUT': parameters['Schools'],
            'OVERLAY': parameters['Studyarea'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Clip'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Reproject hazard layer 2
        alg_params = {
            'DATA_TYPE': 0,
            'EXTRA': '',
            'INPUT': parameters['Hazardlayer2'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,
            'SOURCE_CRS': None,
            'TARGET_CRS': parameters['ProjectedReferenceSystem'],
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectHazardLayer2'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Raster layer statistics layer 2
        alg_params = {
            'BAND': 1,
            'INPUT': outputs['ReprojectHazardLayer2']['OUTPUT']
        }
        outputs['RasterLayerStatisticsLayer2'] = processing.run('native:rasterlayerstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Reproject hazard layer 3
        alg_params = {
            'DATA_TYPE': 0,
            'EXTRA': '',
            'INPUT': parameters['Hazardlayer3'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,
            'SOURCE_CRS': None,
            'TARGET_CRS': parameters['ProjectedReferenceSystem'],
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectHazardLayer3'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Standardizing layer 2
        alg_params = {
            'BAND_A': 1,
            'BAND_B': None,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': QgsExpression('concat(\'(A - \',to_string(replace(to_string(  @Raster_layer_statistics_layer_2_MIN  ),\'.\',\',\')),\')/(\',to_string(replace(to_string(  @Raster_layer_statistics_layer_2_MAX  ),\'.\',\',\')),\' - \',to_string(replace(to_string(  @Raster_layer_statistics_layer_2_MIN  ),\'.\',\',\')),\')*4\')').evaluate(),
            'INPUT_A': outputs['ReprojectHazardLayer2']['OUTPUT'],
            'INPUT_B': None,
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,
            'OUTPUT': parameters['Layer2']
        }
        outputs['StandardizingLayer2'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Layer2'] = outputs['StandardizingLayer2']['OUTPUT']

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Raster layer statistics layer 3
        alg_params = {
            'BAND': 1,
            'INPUT': outputs['ReprojectHazardLayer3']['OUTPUT']
        }
        outputs['RasterLayerStatisticsLayer3'] = processing.run('native:rasterlayerstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Reproject hazard layer 4
        alg_params = {
            'DATA_TYPE': 0,
            'EXTRA': '',
            'INPUT': parameters['Hazardlayer4'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,
            'SOURCE_CRS': None,
            'TARGET_CRS': parameters['ProjectedReferenceSystem'],
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectHazardLayer4'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Reproject hazard layer 5
        alg_params = {
            'DATA_TYPE': 0,
            'EXTRA': '',
            'INPUT': parameters['Hazardlayer5'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,
            'SOURCE_CRS': None,
            'TARGET_CRS': parameters['ProjectedReferenceSystem'],
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectHazardLayer5'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Raster layer statistics layer 4
        alg_params = {
            'BAND': 1,
            'INPUT': outputs['ReprojectHazardLayer4']['OUTPUT']
        }
        outputs['RasterLayerStatisticsLayer4'] = processing.run('native:rasterlayerstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Raster layer statistics layer 5
        alg_params = {
            'BAND': 1,
            'INPUT': outputs['ReprojectHazardLayer5']['OUTPUT']
        }
        outputs['RasterLayerStatisticsLayer5'] = processing.run('native:rasterlayerstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Standardizing layer 3
        alg_params = {
            'BAND_A': 1,
            'BAND_B': None,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': QgsExpression('concat(\'(A - \',to_string(replace(to_string(  @Raster_layer_statistics_layer_3_MIN  ),\'.\',\',\')),\')/(\',to_string(replace(to_string(  @Raster_layer_statistics_layer_3_MAX  ),\'.\',\',\')),\' - \',to_string(replace(to_string(  @Raster_layer_statistics_layer_3_MIN  ),\'.\',\',\')),\')*4\')').evaluate(),
            'INPUT_A': outputs['ReprojectHazardLayer3']['OUTPUT'],
            'INPUT_B': None,
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,
            'OUTPUT': parameters['Layer3']
        }
        outputs['StandardizingLayer3'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Layer3'] = outputs['StandardizingLayer3']['OUTPUT']

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Standardizing layer 4
        alg_params = {
            'BAND_A': 1,
            'BAND_B': None,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': QgsExpression('concat(\'(A - \',to_string(replace(to_string(  @Raster_layer_statistics_layer_4_MIN  ),\'.\',\',\')),\')/(\',to_string(replace(to_string(  @Raster_layer_statistics_layer_4_MAX  ),\'.\',\',\')),\' - \',to_string(replace(to_string(  @Raster_layer_statistics_layer_4_MIN  ),\'.\',\',\')),\')*4\')').evaluate(),
            'INPUT_A': outputs['ReprojectHazardLayer4']['OUTPUT'],
            'INPUT_B': None,
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['StandardizingLayer4'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Standardizing layer 5
        alg_params = {
            'BAND_A': 1,
            'BAND_B': None,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': QgsExpression('concat(\'(A - \',to_string(replace(to_string(  @Raster_layer_statistics_layer_5_MIN  ),\'.\',\',\')),\')/(\',to_string(replace(to_string(  @Raster_layer_statistics_layer_5_MAX  ),\'.\',\',\')),\' - \',to_string(replace(to_string(  @Raster_layer_statistics_layer_5_MIN  ),\'.\',\',\')),\')*4\')').evaluate(),
            'INPUT_A': outputs['ReprojectHazardLayer5']['OUTPUT'],
            'INPUT_B': None,
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['StandardizingLayer5'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # Reproject hazard layer 6
        alg_params = {
            'DATA_TYPE': 0,
            'EXTRA': '',
            'INPUT': parameters['Hazardlayer6'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,
            'SOURCE_CRS': None,
            'TARGET_CRS': parameters['ProjectedReferenceSystem'],
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectHazardLayer6'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # Raster layer statistics layer 6
        alg_params = {
            'BAND': 1,
            'INPUT': outputs['ReprojectHazardLayer6']['OUTPUT']
        }
        outputs['RasterLayerStatisticsLayer6'] = processing.run('native:rasterlayerstatistics', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # Standardizing layer 6
        alg_params = {
            'BAND_A': 1,
            'BAND_B': None,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': QgsExpression('concat(\'(A - \',to_string(replace(to_string(  @Raster_layer_statistics_layer_6_MIN  ),\'.\',\',\')),\')/(\',to_string(replace(to_string(  @Raster_layer_statistics_layer_6_MAX  ),\'.\',\',\')),\' - \',to_string(replace(to_string(  @Raster_layer_statistics_layer_6_MIN  ),\'.\',\',\')),\')*4\')').evaluate(),
            'INPUT_A': outputs['ReprojectHazardLayer6']['OUTPUT'],
            'INPUT_B': None,
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['StandardizingLayer6'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # Merge
        alg_params = {
            'DATA_TYPE': 5,
            'EXTRA': '',
            'INPUT': QgsExpression('CASE\r\nWHEN  @Numberofriskstocompute =2 THEN array(  @Standardizing_layer_1_OUTPUT , @Standardizing_layer_2_OUTPUT ) \r\nWHEN  @Numberofriskstocompute =3 THEN array(  @Standardizing_layer_1_OUTPUT , @Standardizing_layer_2_OUTPUT , @Standardizing_layer_3_OUTPUT ) \r\nWHEN  @Numberofriskstocompute =4 THEN array(  @Standardizing_layer_1_OUTPUT , @Standardizing_layer_2_OUTPUT , @Standardizing_layer_3_OUTPUT , @Standardizing_layer_4_OUTPUT )\r\nWHEN  @Numberofriskstocompute =5 THEN array(  @Standardizing_layer_1_OUTPUT , @Standardizing_layer_2_OUTPUT , @Standardizing_layer_3_OUTPUT , @Standardizing_layer_4_OUTPUT , @Standardizing_layer_5_OUTPUT )\r\nWHEN  @Numberofriskstocompute =6 THEN array(  @Standardizing_layer_1_OUTPUT , @Standardizing_layer_2_OUTPUT , @Standardizing_layer_3_OUTPUT , @Standardizing_layer_4_OUTPUT , @Standardizing_layer_5_OUTPUT , @Standardizing_layer_6_OUTPUT  ) \r\nEND\r\n').evaluate(),
            'NODATA_INPUT': None,
            'NODATA_OUTPUT': None,
            'OPTIONS': '',
            'PCT': False,
            'SEPARATE': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Merge'] = processing.run('gdal:merge', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        # Raster calculator
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 2,
            'BAND_C': QgsExpression('CASE\r\nWHEN @Numberofriskstocompute =3 OR @Numberofriskstocompute =4 OR @Numberofriskstocompute =5 OR  @Numberofriskstocompute =6 THEN 3\r\nEND').evaluate(),
            'BAND_D': QgsExpression('CASE\r\nWHEN  @Numberofriskstocompute =4 OR @Numberofriskstocompute =5 OR  @Numberofriskstocompute =6 THEN 4\nEND').evaluate(),
            'BAND_E': QgsExpression('CASE\r\nWHEN @Numberofriskstocompute =5 OR  @Numberofriskstocompute =6 THEN 5\nEND').evaluate(),
            'BAND_F': QgsExpression('CASE\r\nWHEN @Numberofriskstocompute =6 THEN 6\r\nEND').evaluate(),
            'EXTRA': '',
            'FORMULA': QgsExpression('CASE\r\nWHEN  @Numberofriskstocompute =2 THEN concat(\'A*\',to_string( @WeightforHazardlayer1),\'+B*\',to_string( @WeightforHazardlayer2))\r\nWHEN  @Numberofriskstocompute =3 THEN concat(\'A*\',to_string( @WeightforHazardlayer1),\'+B*\',to_string( @WeightforHazardlayer2), \'+C*\',to_string( @WeightforHazardlayer3))\r\nWHEN  @Numberofriskstocompute =4 THEN concat(\'A*\',to_string( @WeightforHazardlayer1),\'+B*\',to_string( @WeightforHazardlayer2), \'+C*\',to_string( @WeightforHazardlayer3), \'+D*\',to_string( @WeightforHazardlayer4))\r\nWHEN  @Numberofriskstocompute =5 THEN concat(\'A*\',to_string( @WeightforHazardlayer1),\'+B*\',to_string( @WeightforHazardlayer2), \'+C*\',to_string( @WeightforHazardlayer3), \'+D*\',to_string( @WeightforHazardlayer4), \'+E*\',to_string( @WeightforHazardlayer5))\r\nWHEN  @Numberofriskstocompute =6 THEN concat(\'A*\',to_string( @WeightforHazardlayer1),\'+B*\',to_string( @WeightforHazardlayer2), \'+C*\',to_string( @WeightforHazardlayer3), \'+D*\',to_string( @WeightforHazardlayer4), \'+E*\',to_string( @WeightforHazardlayer5), \'+F*\',to_string( @WeightforHazardlayer6 ))\r\nEND').evaluate(),
            'INPUT_A': outputs['Merge']['OUTPUT'],
            'INPUT_B': outputs['Merge']['OUTPUT'],
            'INPUT_C': QgsExpression('CASE\r\nWHEN @Numberofriskstocompute =3 OR @Numberofriskstocompute =4 OR @Numberofriskstocompute =5 OR  @Numberofriskstocompute =6 THEN @Merge_OUTPUT \r\nEND').evaluate(),
            'INPUT_D': QgsExpression('CASE\r\nWHEN  @Numberofriskstocompute =4 OR @Numberofriskstocompute =5 OR  @Numberofriskstocompute =6 THEN @Merge_OUTPUT \r\nEND').evaluate(),
            'INPUT_E': QgsExpression('CASE\r\nWHEN  @Numberofriskstocompute =5 OR  @Numberofriskstocompute =6 THEN @Merge_OUTPUT \r\nEND').evaluate(),
            'INPUT_F': QgsExpression('CASE\r\nWHEN  @Numberofriskstocompute = 6 THEN @Merge_OUTPUT \r\nEND').evaluate(),
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterCalculator'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}

        # Clip raster by mask layer
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,
            'EXTRA': '',
            'INPUT': outputs['RasterCalculator']['OUTPUT'],
            'KEEP_RESOLUTION': False,
            'MASK': parameters['Studyarea'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': None,
            'TARGET_CRS': None,
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': parameters['HazardIndex']
        }
        outputs['ClipRasterByMaskLayer'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['HazardIndex'] = outputs['ClipRasterByMaskLayer']['OUTPUT']

        feedback.setCurrentStep(26)
        if feedback.isCanceled():
            return {}

        # Sample raster values
        alg_params = {
            'COLUMN_PREFIX': 'HazardIndex',
            'INPUT': outputs['Clip']['OUTPUT'],
            'RASTERCOPY': outputs['RasterCalculator']['OUTPUT'],
            'OUTPUT': parameters['HazardIndexSchools']
        }
        outputs['SampleRasterValues'] = processing.run('native:rastersampling', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['HazardIndexSchools'] = outputs['SampleRasterValues']['OUTPUT']
        return results

    def name(self):
        return 'Natural Hazard Risks for Schools'

    def displayName(self):
        return 'Natural Hazard Risks for Schools'

    def group(self):
        return 'Final models'

    def groupId(self):
        return 'Final models'

    def shortHelpString(self):
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
<br><p align="right">Algorithm author: Development unit at IIEP-UNESCO (development@iiep.unesco.org)</p><p align="right">Help author: Development unit at IIEP-UNESCO (development@iiep.unesco.org)</p><p align="right">Algorithm version: 1.0</p></body></html>"""

    def helpUrl(self):
        return 'https://github.com/iiepdev/mcda-site-classification-educational-facilities'

    def createInstance(self):
        return NaturalHazardRisksForSchools()
