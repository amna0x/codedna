"""CodeDNA's Java language plugin: parsing, code graph, test discovery and runs."""

__version__ = "0.1.0"


def __getattr__(name: str):
    # Lazy, so reading __version__ (e.g. during packaging) needs no tree-sitter.
    if name == "JavaPlugin":
        from codedna_java.plugin import JavaPlugin
        return JavaPlugin
    raise AttributeError(name)


__all__ = ["JavaPlugin", "__version__"]
