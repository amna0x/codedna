"""Map changed line ranges to Java declarations (classes, methods, fields...)."""

from codedna.java_analysis.mapping import (
    DeclarationChange,
    JavaFileAnalysis,
    OutsideChange,
    UnresolvedChange,
    analyze_changes,
    attach_java_declarations,
)
from codedna.java_analysis.parser import Declaration, JavaParseResult, parse_java

__all__ = [
    "Declaration",
    "DeclarationChange",
    "JavaFileAnalysis",
    "JavaParseResult",
    "OutsideChange",
    "UnresolvedChange",
    "analyze_changes",
    "attach_java_declarations",
    "parse_java",
]
