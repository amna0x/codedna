"""Language plugins: the interface and the registry (D-018). Java is ``codedna-java`` (D-054)."""

from codedna.plugins.base import PLUGIN_API_VERSION, LanguagePlugin, api_compatible
from codedna.plugins.registry import ENTRY_POINT_GROUP, PluginRegistry, load_plugins

__all__ = ["ENTRY_POINT_GROUP", "PLUGIN_API_VERSION", "LanguagePlugin", "PluginRegistry",
           "api_compatible", "load_plugins"]
