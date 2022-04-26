"""Definitions for GUI concepts."""
import enum

from qgis.core import QgsApplication
from qgis.PyQt.QtGui import QIcon

from ..qgis_plugin_tools.tools.resources import resources_path


class Panels(enum.Enum):
    """Panels in the Dialog"""

    Infrastructure = {"icon": "/mIconPolygonLayer.svg"}
    HazardRiskIndex = {"icon": "/mActionMapSettings.svg"}
    EconomicSuitability = {"icon": "/mIconRaster.svg"}
    EnvironmentalSuitability = {"icon": "/mIconRaster.svg"}
    MultiCriteriaSuitability = {"icon": "/mActionShowRasterCalculator.png"}
    About = {"icon": "/mActionHelpContents.svg"}

    @property
    def icon(self) -> QIcon:
        _icon: str = self.value["icon"]

        # QGIS icons
        # https://github.com/qgis/QGIS/tree/master/images/themes/default
        if _icon.startswith("/"):
            return QgsApplication.getThemeIcon(_icon)
        else:
            # Internal icons
            return QIcon(resources_path("icons", _icon))
