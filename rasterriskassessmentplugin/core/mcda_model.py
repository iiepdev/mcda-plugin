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

    def createInstance(self):  # noqa: N802
        return Mcda()
