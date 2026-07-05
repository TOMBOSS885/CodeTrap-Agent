"""Project constants."""

APP_NAME = "CodeTrap-Agent"
VERSION_TAG = "0.1.0"
DEFAULT_DATA_DIR = ".codetrap-agent"
DEFAULT_MODEL_TEMPERATURE = 0.85
DEFAULT_TOP_P = 0.95

TRAP_DIMENSIONS = [
    "ambiguous_boundaries",
    "off_by_one",
    "duplicate_handling",
    "empty_or_singleton",
    "ordering_stability",
    "numeric_overflow_or_precision",
    "state_mutation",
    "unicode_or_escaping",
    "performance_cliff",
    "misleading_greedy",
]
