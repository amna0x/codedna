"""Language plugins: the interface, the registry and the built-in Java plugin (D-018)."""

from codedna.plugins.base import PLUGIN_API_VERSION, LanguagePlugin
from codedna.plugins.registry import ENTRY_POINT_GROUP, PluginRegistry, load_plugins

__all__ = ["ENTRY_POINT_GROUP", "PLUGIN_API_VERSION", "LanguagePlugin", "PluginRegistry",
           "load_plugins"]
