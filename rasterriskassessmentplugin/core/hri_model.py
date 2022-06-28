"""
Model exported as python.
Name : Natural Hazard Risks for Schools
Group : Final models
With QGIS : 31600
"""

from .combine_rasters import CombineRasters


class NaturalHazardRisksForSchools(CombineRasters):
    def name(self):
        return "Natural Hazard Risks for Schools"

    def displayName(self):  # noqa: N802
        return "Natural Hazard Risks for Schools"

    def group(self):
        return "Final models"

    def groupId(self):  # noqa: N802
        return "Final models"

    @classmethod
    def shortHelpString(cls):  # noqa: N802
        return """<html><body><h2>Algorithm description</h2>
<p>This algorithm creates a composite hazard risk index by using anywhere from 2 to 6 different raster hazard risk layers. The user can define custom weights for each raster. The result includes a raster ranging from 1 to 4, where 1 is Lower risk and 4 is Higher risk, plus a sampled point layer for schools with the corresponding risk index.</p>
<h2>Input parameters</h2>
<h3>Number of risks to compute</h3>
<p>Any whole number between 2 and 6</p>
<h3>Hazard layers</h3>
<p>All hazard layers can have any range (e.g., 1 to 100, 0 to 5, etc.), as long as the classification runs from less risk (lower values) to higher risk (higher values). If this is not the case, the user should begin by multiplying the raster layer by -1 before running this process. </p>
<h3>Weight for Hazard layers</h3>
<p>Please make sure that all weights add up to 100%</p>
<h3>Schools</h3>
<p>A point vector layer with one observation for each school in the area of analysis</p>
<h3>Study area</h3>
<p>A polygon vector layer delimiting the area of analysis.</p>
<h3>Hazard index</h3>
<p>Raster layer ranging from 1 (Less risky) to 4 (More risky)</p>
<h3>Hazard Index - Schools</h3>
<p>The original point layer file with the information on the composite hazard index that corresponds to the location of the school, ranging from 1 (Less risky) to 4 (More risky).</p>
<h3>Projected reference system</h3>
<p>Select a local projected reference system. Note that failing to do so might lead to inaccuracies when calculations are performed far from the equator. </p><h2>Outputs</h2>
<h3>Hazard index</h3>
<p>Raster layer ranging from 1 (Less risky) to 4 (More risky)</p>
<h3>Hazard Index - Schools</h3>
<p>The original point layer file with the information on the composite hazard index that corresponds to the location of the school, ranging from 1 (Less risky) to 4 (More risky).</p>
<br><p>Algorithm author: Development unit at IIEP-UNESCO (development@iiep.unesco.org)</p><p>Help author: Development unit at IIEP-UNESCO (development@iiep.unesco.org)</p><p>Algorithm version: 1.0</p></body></html>
"""

    def helpUrl(self):  # noqa: N802
        return (
            "https://github.com/iiepdev/mcda-site-classification-educational-facilities"
        )

    def createInstance(self):  # noqa: N802
        return NaturalHazardRisksForSchools()
