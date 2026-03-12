"""Simple CSV parser."""


def parse_csv(text: str) -> list[list[str]]:
    """Parse CSV text into rows of fields."""
    rows = []
    for line in text.strip().split("\n"):
        # Bug: simple split doesn't handle quoted fields with commas
        fields = line.split(",")
        rows.append([f.strip() for f in fields])
    return rows


def parse_row(line: str) -> list[str]:
    """Parse a single CSV row."""
    return line.split(",")
