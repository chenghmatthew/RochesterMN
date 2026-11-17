"""Turn the workbook's free-text business hours into the 'schedule' the map uses to say "Open now" / "Closed".

    parse_hours("Monday - Friday 8 a.m. to 5 p.m.; Closed Saturday - Sunday")
    -> {"type": "weekly", "days": {"1": [[480, 1020]], ..., "5": [[480, 1020]]}}

Day keys are 0 = Sunday ... 6 = Saturday (JavaScript's getDay); times are minutes after midnight.
Result types: "weekly" (parsed), "always" (24 hours), "varies" (couldn't be read with confidence; the page
then shows "Hours vary" and the original text is still displayed on the card).
Hours that run past midnight ("11 a.m. to 1 a.m.") are split: the late part is added to the next day.
"""

import re

DAY_NAMES = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
DAY_RE = r"(?:sun|mon|tue|wed|thu|fri|sat)[a-z]*\.?"
TIME_RE = re.compile(r"(\d{1,2})(?::(\d{2})?)?\s*([ap])\.?\s*m\b\.?|\b(noon)\b|\b(midnight)\b")
RANGE_RE = re.compile(rf"\b({DAY_RE})\s*(?:-|to|through|thru)\s*({DAY_RE})")
DAY_WORD_RE = re.compile(rf"\b{DAY_RE}")
ALL_DAYS = [0, 1, 2, 3, 4, 5, 6]


def day_number(word):
    return DAY_NAMES[word[:3]]


def expand_days(text):
    """Day numbers named in text: ranges ('Mon - Fri', wrapping allowed), lists and single days."""
    days = []
    for a, b in RANGE_RE.findall(text):
        i = day_number(a)
        while True:
            days.append(i)
            if i == day_number(b):
                break
            i = (i + 1) % 7
    rest = RANGE_RE.sub(" ", text)
    days += [day_number(w) for w in DAY_WORD_RE.findall(rest)]
    if re.search(r"\b(daily|every ?day|7 days)\b", text):
        days += ALL_DAYS
    return sorted(set(days))


def minutes(match):
    hour, minute, ap, noon, midnight = match.groups()
    if noon:
        return 720
    if midnight:
        return 0
    value = int(hour) % 12 * 60 + int(minute or 0) + (720 if ap == "p" else 0)
    return value


def time_ranges(text):
    """List of (start, end) minute pairs, or None when the times can't be paired up. end may exceed 1440."""
    found = list(TIME_RE.finditer(text))
    if not found or len(found) % 2:
        return None
    ranges = []
    for first, second in zip(found[0::2], found[1::2]):
        start, end = minutes(first), minutes(second)
        if end <= start:
            if end <= 5 * 60 or second.group(5):  # "to 1 a.m." / "to midnight": closes after midnight
                end += 1440
            elif second.group(3) == "a" and end + 720 > start:  # "9:30 a.m. to 6:30 a.m." is a typo for p.m.
                end += 720
            else:
                return None
        ranges.append((start, end))
    return ranges


def segments(text):
    """Split into one piece per day-group: on ';' and line breaks, but keep a day line and its time line together."""
    pieces, current = [], ""
    for line in re.split(r"[;\n]", text):
        current = (current + " " + line).strip()
        has_day = bool(DAY_WORD_RE.search(current)) or "daily" in current
        has_what = bool(TIME_RE.search(current)) or "closed" in current or "24 hours" in current
        if has_day and has_what:
            pieces.append(current)
            current = ""
    if current and (DAY_WORD_RE.search(current) or TIME_RE.search(current)):  # drop notes like "source listing"
        pieces.append(current)
    return pieces


def parse_hours(text):
    clean = re.sub(r"[–—�]", "-", str(text or "").lower())
    clean = re.sub(r"\b(open|hours?)\s*:", " ", clean)
    if not clean.strip() or re.search(r"appointment|vary|varies|not confirmed|contact|visit ", clean):
        return {"type": "varies"}
    if re.search(r"24 hours|24/7", clean) and not DAY_WORD_RE.search(clean.replace("front desk", "")):
        return {"type": "always"}
    schedule = {d: [] for d in ALL_DAYS}
    clean = re.sub(r"\bseasonal[^.;]*\.?|\bholiday[^.;]*\.?", " ", clean)
    for piece in segments(clean.strip(" .")):
        days = expand_days(TIME_RE.sub(" ", piece)) or (ALL_DAYS if TIME_RE.search(piece) else [])
        if "closed" in piece and not TIME_RE.search(piece):
            continue  # those days stay closed
        ranges = [(0, 1440)] if "24 hours" in piece else time_ranges(piece)
        if not days or ranges is None:
            return {"type": "varies"}
        for day in days:
            for start, end in ranges:
                schedule[day].append([start, min(end, 1440)])
                if end > 1440:
                    schedule[(day + 1) % 7].append([0, end - 1440])
    if not any(schedule.values()):
        return {"type": "varies"}
    return {"type": "weekly", "days": {str(d): sorted(v) for d, v in schedule.items() if v}}
