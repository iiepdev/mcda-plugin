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
<p>This algorithm creates a composite general suitability index 
for educational facilities in a particular region. It considers 
the suitability of a location depending on the results from the 
three previous suitability rasters (economic, environmental, 
and social). The user can define custom weights for each input. 
The result produces a raster ranging from 1 to 4, where 1 is Less 
suitable and 4 is More suitable.</p>
<h2>Input parameters</h2>
<h3>Economic suitability</h3>
<p>Raster layer ranging from 1 (More suitable) to 4 (Less suitable), 
created using the Economic suitability algorithm.</p>
<h3>Weight for Economic suitability</h3>
<p>Make sure that the sum of "Weight for economic suitability", 
"Weight for environmental suitability", and "Weight for social 
suitability" is equal to 100%.</p>
<h3>Environmental suitability</h3>
<p>Raster layer ranging from 1 (More suitable) to 4 (Less suitable), 
created using the Environmental suitability algorithm.</p>
<h3>Weight for Environmental suitability</h3>
<p>Make sure that the sum of "Weight for economic suitability", "Weight 
for environmental suitability", and "Weight for social suitability"
 is equal to 100%.</p>
<h3>Social suitability</h3>
<p>Raster layer ranging from 1 (More suitable) to 4 (Less suitable), 
created using the Social suitability algorithm.</p>
<h3>Weight for Social suitability</h3>
<p>Make sure that the sum of "Weight for economic suitability", 
"Weight for environmental suitability", and "Weight for social suitability" 
is equal to 100%.</p>
<h3>Site Area</h3>
<p>A polygon vector layer delimiting the area of analysis.</p>
<h3>Projected reference system</h3>
<p>Select a local projected reference system. Note that failing to do so
might lead to inaccuracies when calculations are performed far from the 
equator. </p>
<h2>Outputs</h2>
<h3>MCDA</h3>
<p>Raster layer ranging from 1 (More suitable) to 4 (Less suitable).</p>
<br><p>Algorithm author: Development unit at IIEP-UNESCO 
(development@iiep.unesco.org)</p><p>Help author: Development unit at 
IIEP-UNESCO (development@iiep.unesco.org)</p><p>Algorithm version: 1.0</p>
</body></html>
"""

    def createInstance(self):  # noqa: N802
        return Mcda()
