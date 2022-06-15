import datetime
import re

from django.db import transaction

from uploader.models import AchillesResults

MONTHS = dict(
    map(
        lambda t: (t[1], f"{t[0] + 1:02}"),
        enumerate(
            (
                "JAN",
                "FEV",
                "MAR",
                "APR",
                "MAY",
                "JUN",
                "JUL",
                "AUG",
                "SEP",
                "OCT",
                "NOV",
                "DEC",
            )
        ),
    )
)

with_month = re.compile(r"(\d{2})-([A-Z]{3})-(\d{2})")  # 02-MAY-2020


def with_month_extractor(match: re.Match):
    day, month, year = match.groups()
    return f"20{year}", MONTHS[month], day


with_hiphen = re.compile(r"(\d{4})-(\d{2})-(\d{2})")  # 2020-12-02


def with_hiphen_extractor(match: re.Match):
    return match.groups()


no_hiphen = re.compile(r"(\d{4})(\d{2})(\d{2})")  # 20201202
no_hiphen_extractor = with_hiphen_extractor

no_hiphen_float = re.compile(r"(\d{4})(\d{2})(\d{2})\.\d")  # 20201202.0
no_hiphen_float_extractor = with_hiphen_extractor

with_slash_one_digit = re.compile(
    r"(\d{1,2})/(\d{1,2})/(\d{4})"
)  # 1/31/2020 or 12/1/2020 or 1/1/2020 or 12/31/2020


def with_slash_one_digit_extractor(match: re.Match):
    month, day, year = match.groups()
    return year, f"{int(month):02}", f"{int(day):02}"


with_slash_two_digits = re.compile(
    r"(\d{2})/(\d{2})/(\d{2,4})"
)  # 31/01/20 or 31/01/2020


def with_slash_two_digits_extractor(match: re.Match):
    day, month, year = match.groups()
    return ("" if len(year) == 4 else "20") + year, month, day


PATTERNS = (
    (with_month, with_month_extractor),
    (with_hiphen, with_hiphen_extractor),
    (no_hiphen, no_hiphen_extractor),
    (no_hiphen_float, no_hiphen_float_extractor),
    (
        with_slash_two_digits,
        with_slash_two_digits_extractor,
    ),  # try first with two digits then with one
    (with_slash_one_digit, with_slash_one_digit_extractor),
)


def _convert_value(valid_pattern: re.Pattern, value: str):
    for pattern, extractor in PATTERNS:
        if pattern == valid_pattern:
            continue
        match = pattern.fullmatch(value)
        if match:
            date_tuple = extractor(match)
            try:
                datetime.date(*map(int, date_tuple))
            except ValueError:
                continue
            return date_tuple
    if valid_pattern.fullmatch(value):
        return None
    # print(f"unexpected date format -{value}-")
    # return None
    raise Exception(f"unexpected date format -{value}-")


@transaction.atomic
def apply_changes():
    # fix generation_date
    for ar in AchillesResults.objects.filter(analysis_id=0):
        # upload = ar.data_source.uploadhistory_set.latest()
        # print("upload", upload.pk)
        if (
            ar.stratum_3
            and (new_date := _convert_value(no_hiphen, ar.stratum_3)) is not None
        ):
            year, month, day = new_date
            # old = ar.stratum_3
            ar.stratum_3 = f"{year}-{month}-{day}"
            # print("from", old, "to", ar.stratum_3)
            ar.save()
    for ar in AchillesResults.objects.filter(analysis_id=5000):
        # upload = ar.data_source.uploadhistory_set.latest()
        # print("upload", upload.pk)
        # fix source release date
        if (
            ar.stratum_2
            and (new_date := _convert_value(with_hiphen, ar.stratum_2)) is not None
        ):
            year, month, day = new_date
            # old = ar.stratum_2
            ar.stratum_2 = f"{year}-{month}-{day}"
            # print("source release from", old, "to", ar.stratum_2)
            ar.save()
        # fix cdm release date
        if (
            ar.stratum_3
            and (new_date := _convert_value(with_hiphen, ar.stratum_3)) is not None
        ):
            year, month, day = new_date
            # old = ar.stratum_3
            ar.stratum_3 = f"{year}-{month}-{day}"
            # print("cdm release from", old, "to", ar.stratum_3)
            ar.save()
