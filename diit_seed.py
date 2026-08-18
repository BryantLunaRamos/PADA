"""
Default seed list for diit_pipeline.py's flagging step.

A seed module (passed via --seed-module) must define:
  KEYWORDS         list[str] - substring/TF-IDF seed terms that mark a contract
                    as belonging to the target category
  EXCLUDE_PHRASES   list[str] - phrases that veto a keyword/similarity match
                    (false-positive guard)

Point --seed-module at a different .py file (or importable module name) to
run this pipeline against a different dataset's target category.
"""

KEYWORDS = [
    "DIIT", "information technology", "instructional technology", "technology",
    "software", "hardware", "network", "server", "laptop", "desktop", "tablet",
    "chromebook", "wireless", "data center", "cabling", "IT services",
    "IT support", "IT consulting", "cloud", "digital", "computer", "device",
    "cyber", "telecommunications", "infrastructure", "system",
]

EXCLUDE_PHRASES = [
    "family child care", "crisis management system", "system-wide", "systemwide",
    "system wide", "fire alarm", "fire suppression", "sprinkler", "standpipe",
    "security system", "hvac", "air condition", "boiler", "plumbing", "backflow",
    "fuel oil", "public address system", "gas leak detection", "de-watering",
    "kitchen exhaust", "water treatment", "direct digital control",
    "window shades", "legal process server",
    "vendor does not have order in system", "doc posted in city",
    "cancelled as instructed",
]
