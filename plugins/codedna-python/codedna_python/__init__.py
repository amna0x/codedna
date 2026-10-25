"""CodeDNA's Python language plugin: parsing, code graph, test discovery and runs."""

__version__ = "0.1.0"


def __getattr__(name: str):
    # Lazy, like codedna_java: reading __version__ imports nothing else.
    if name == "PythonPlugin":
        from codedna_python.plugin import PythonPlugin
        return PythonPlugin
    raise AttributeError(name)


__all__ = ["PythonPlugin", "__version__"]
