"""
Model exported as python.
Name : MCDA
Group : Multi-criteria decision analysis
With QGIS : 31600
"""

from .combine_rasters import CombineRasters


class Mcda(CombineRasters):
    def name(self):
        return "MCDA"

    def displayName(self):  # noqa: N802
        return "MCDA"

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
        return Mcda()
