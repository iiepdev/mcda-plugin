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
<br><p align="right">Algorithm author: Development unit at IIEP-UNESCO (development@iiep.unesco.org)</p><p align="right">Help author: Development unit at IIEP-UNESCO (development@iiep.unesco.org)</p><p align="right">Algorithm version: 1.0</p></body></html>"""  # noqa

    def helpUrl(self):  # noqa: N802
        return (
            "https://github.com/iiepdev/mcda-site-classification-educational-facilities"
        )

    def createInstance(self):  # noqa: N802
        return NaturalHazardRisksForSchools()
