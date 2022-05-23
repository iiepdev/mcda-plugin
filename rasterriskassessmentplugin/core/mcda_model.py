"""
Model exported as python.
Name : MCDA
Group : Multi-criteria decision analysis
With QGIS : 31600
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterCrs
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsExpression
import processing


class Mcda(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('Economicsuitability', 'Economic suitability', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('WeightforEconomicsuitability', 'Weight for Economic suitability', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=0.3333))
        self.addParameter(QgsProcessingParameterRasterLayer('Environmentalsuitability', 'Environmental suitability', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('WeightforEnvironmentalsuitability', 'Weight for Environmental suitability', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=0.333))
        self.addParameter(QgsProcessingParameterRasterLayer('Socialsuitability', 'Social suitability', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('WeightforSocialsuitability', 'Weight for Social suitability', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=1, defaultValue=0.3333))
        self.addParameter(QgsProcessingParameterCrs('CRS', 'CRS', defaultValue='EPSG:4326'))
        self.addParameter(QgsProcessingParameterVectorLayer('SiteArea', 'Site Area', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Mcda', 'MCDA', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(5, model_feedback)
        results = {}
        outputs = {}

        # Merge
        alg_params = {
            'DATA_TYPE': 5,
            'EXTRA': '',
            'INPUT': QgsExpression('array( @Economicsuitability , @Environmentalsuitability , @Socialsuitability )').evaluate(),
            'NODATA_INPUT': None,
            'NODATA_OUTPUT': None,
            'OPTIONS': '',
            'PCT': False,
            'SEPARATE': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Merge'] = processing.run('gdal:merge', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Raster calculator
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 2,
            'BAND_C': 3,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': QgsExpression('concat(\'A*\',to_string( @WeightforEconomicsuitability ),\' + B*\', to_string( @WeightforEnvironmentalsuitability ),\' + C*\',to_string( @WeightforSocialsuitability ))').evaluate(),
            'INPUT_A': outputs['Merge']['OUTPUT'],
            'INPUT_B': outputs['Merge']['OUTPUT'],
            'INPUT_C': outputs['Merge']['OUTPUT'],
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterCalculator'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Fix geometries
        alg_params = {
            'INPUT': parameters['SiteArea'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FixGeometries'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Reproject layer
        alg_params = {
            'INPUT': outputs['FixGeometries']['OUTPUT'],
            'OPERATION': '',
            'TARGET_CRS': parameters['CRS'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectLayer'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
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
            'MASK': outputs['ReprojectLayer']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': None,
            'TARGET_CRS': None,
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': parameters['Mcda']
        }
        outputs['ClipRasterByMaskLayer'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Mcda'] = outputs['ClipRasterByMaskLayer']['OUTPUT']
        return results

    def name(self):
        return 'MCDA'

    def displayName(self):
        return 'MCDA'

    def group(self):
        return 'Multi-criteria decision analysis'

    def groupId(self):
        return 'Multi-criteria decision analysis'

    def createInstance(self):
        return Mcda()
