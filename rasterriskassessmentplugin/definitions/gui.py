"""Definitions for GUI concepts."""
import enum

from qgis.core import QgsApplication
from qgis.PyQt.QtGui import QIcon

from ..qgis_plugin_tools.tools.resources import resources_path


class Panels(enum.Enum):
    """Panels in the Dialog"""

    # Note that we cannot use the same icon twice!
    # The icon serves as the enum here. Reusing an icon
    # will redefine the enum, not create a new one.
    # HazardRiskIndex = {"icon": "/mActionMapSettings.svg"}
    # Infrastructure = {"icon": "/mIconPolygonLayer.svg"}
    # EconomicSuitability = {"icon": "/mIconLineLayer.svg"}
    # EnvironmentalSuitability = {"icon": "/mIconRaster.svg"}
    # MultiCriteriaSuitability = {"icon": "/mActionShowRasterCalculator.png"}
    # Help = {"icon": "/mActionHelpContents.svg"}
    # About = {"icon": "/mIconInfo.svg"}
    """HazardRiskIndex = {"icon": "hazardIndex2.png"}
    Infrastructure = {"icon": "infra2optimized.svg"}
    EconomicSuitability = {"icon": "g3825.png"}
    EnvironmentalSuitability = {"icon": "environmental2.svg"}
    MultiCriteriaSuitability = {"icon": "help2help.svg"}
    Help = {"icon": "iiepLogo2plain.svg"}
    About = {"icon": "contactUS2.svg"}"""

    # Note that we cannot use the same icon twice!
    # The icon serves as the enum here. Reusing an icon
    # will redefine the enum, not create a new one.
    HazardRiskIndex = {"icon": "hri.png"}
    Infrastructure = {"icon": "infrastructure.png"}
    EconomicSuitability = {"icon": "economic.png"}
    EnvironmentalSuitability = {"icon": "environmental.png"}
    MultiCriteriaSuitability = {"icon": "mcda.png"}
    Help = {"icon": "help.png"}
    About = {"icon": "contact_us.png"}

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
