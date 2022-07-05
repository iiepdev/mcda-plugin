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
    HazardRiskIndex = {"icon": "hazard_index.svg"}
    Infrastructure = {"icon": "infrastructure.svg"}
    EconomicSuitability = {"icon": "economic.png"}
    EnvironmentalSuitability = {"icon": "environmental.png"}
    MultiCriteriaSuitability = {"icon": "mcda_logo.svg"}
    Help = {"icon": "help.png"}
    About = {"icon": "contact_us.svg"}

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
