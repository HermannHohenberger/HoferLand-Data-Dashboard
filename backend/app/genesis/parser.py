import re


YEAR_PATTERN = re.compile(r"(19|20)\d{2}")
ROW_CODE_PATTERN = re.compile(r"^([A-Z0-9]{2,5});")


def _to_number(value: str) -> float | None:
    normalized = value.strip()
    if not normalized or normalized in {"-", ".", "x", "/"}:
        return None
    normalized = normalized.replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _normalize(text: str) -> str:
    lowered = text.lower()
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
    }
    for source, target in replacements.items():
        lowered = lowered.replace(source, target)
    return lowered


def _clean_line(line: str) -> str:
    return line.lstrip("\ufeff").strip("\r")


def _matches_selector(label: str, selector_tokens: tuple[str, ...]) -> bool:
    if not selector_tokens:
        return True
    for token in selector_tokens:
        normalized_token = _normalize(token)
        exact = False
        if normalized_token.startswith("="):
            exact = True
            normalized_token = normalized_token[1:]
        alternatives = [item.strip() for item in normalized_token.split("|") if item.strip()]
        if not alternatives:
            continue
        if exact:
            if label not in alternatives:
                return False
            continue
        if not any(option in label for option in alternatives):
            return False
    return True


def parse_population_csv(csv_text: str) -> list[dict[str, float]]:
    lines = [_clean_line(line) for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return []

    date_line = next((line for line in lines if line.startswith(";;31.12.")), None)
    gender_line = next((line for line in lines if line.startswith(";;Insgesamt;")), None)
    data_line = next((line for line in lines if re.match(r"^\d{5};", line)), None)

    if date_line is None or gender_line is None or data_line is None:
        return []

    dates = date_line.split(";")[2:]
    genders = gender_line.split(";")[2:]
    values = data_line.split(";")[2:]

    aggregated: dict[int, float] = {}
    for raw_date, raw_gender, raw_value in zip(dates, genders, values):
        if raw_gender.strip().lower() != "insgesamt":
            continue

        year_match = YEAR_PATTERN.search(raw_date)
        if not year_match:
            continue
        year = int(year_match.group(0))

        value = _to_number(raw_value)
        if value is None:
            continue

        aggregated[year] = value

    return [{"year": year, "value": aggregated[year]} for year in sorted(aggregated.keys())]


def parse_population_csv_by_region(csv_text: str) -> dict[str, list[dict[str, float]]]:
    lines = [_clean_line(line) for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return {}

    date_line = next((line for line in lines if line.startswith(";;31.12.")), None)
    gender_line = next((line for line in lines if line.startswith(";;Insgesamt;")), None)
    if date_line is None or gender_line is None:
        return {}

    dates = date_line.split(";")[2:]
    genders = gender_line.split(";")[2:]
    relevant_indices: list[tuple[int, int]] = []
    for index, (raw_date, raw_gender) in enumerate(zip(dates, genders)):
        if raw_gender.strip().lower() != "insgesamt":
            continue
        year_match = YEAR_PATTERN.search(raw_date)
        if not year_match:
            continue
        relevant_indices.append((index, int(year_match.group(0))))

    if not relevant_indices:
        return {}

    by_region: dict[str, dict[int, float]] = {}
    for line in lines:
        match = ROW_CODE_PATTERN.match(line)
        if not match:
            continue
        code = match.group(1).strip()
        values = line.split(";")[2:]
        for index, year in relevant_indices:
            if index >= len(values):
                continue
            value = _to_number(values[index])
            if value is None:
                continue
            by_region.setdefault(code, {})[year] = value

    result: dict[str, list[dict[str, float]]] = {}
    for code, year_map in by_region.items():
        result[code] = [
            {"year": year, "value": year_map[year]}
            for year in sorted(year_map.keys())
        ]
    return result


def parse_metric_csv_by_region(
    csv_text: str,
    selector_tokens: tuple[str, ...],
) -> dict[str, list[dict[str, float]]]:
    lines = [_clean_line(line) for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return {}

    header_lines = [line for line in lines if line.startswith(";;")]
    data_lines = [line for line in lines if ROW_CODE_PATTERN.match(line)]
    if not header_lines or not data_lines:
        return {}

    split_headers = [line.split(";") for line in header_lines]
    max_cols = max(len(parts) for parts in split_headers)
    token_norm = tuple(_normalize(token) for token in selector_tokens)

    year_by_col: dict[int, int] = {}
    label_by_col: dict[int, str] = {}
    for col in range(2, max_cols):
        year: int | None = None
        labels: list[str] = []
        for parts in split_headers:
            cell = parts[col] if col < len(parts) else ""
            labels.append(cell.strip())
            match = YEAR_PATTERN.search(cell)
            if match:
                year = int(match.group(0))
        if year is None:
            continue
        year_by_col[col] = year
        label_by_col[col] = _normalize(" ".join(labels))

    if not year_by_col:
        return {}

    selected_cols: list[tuple[int, int]] = []
    for col, year in year_by_col.items():
        label = label_by_col.get(col, "")
        if token_norm and not _matches_selector(label, token_norm):
            continue
        selected_cols.append((col, year))

    if not selected_cols:
        # Fallback: if selector was too strict, use all numeric columns per year.
        selected_cols = list(year_by_col.items())

    by_region: dict[str, dict[int, float]] = {}
    for line in data_lines:
        match = ROW_CODE_PATTERN.match(line)
        if not match:
            continue
        code = match.group(1).strip()
        values = line.split(";")
        region_map = by_region.setdefault(code, {})
        for col, year in selected_cols:
            if col >= len(values):
                continue
            value = _to_number(values[col])
            if value is None:
                continue
            region_map[year] = value

    result: dict[str, list[dict[str, float]]] = {}
    for code, year_map in by_region.items():
        if not year_map:
            continue
        result[code] = [
            {"year": year, "value": year_map[year]}
            for year in sorted(year_map.keys())
        ]
    return result


def parse_foreign_population_csv_by_region(csv_text: str) -> dict[str, list[dict[str, float]]]:
    lines = [_clean_line(line) for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return {}

    by_region: dict[str, dict[int, float]] = {}
    for line in lines:
        parts = line.split(";")
        if len(parts) < 11:
            continue
        # Layout: date;ags;name;age_group;...;auslaendisch insgesamt;...
        year_match = YEAR_PATTERN.search(parts[0])
        if not year_match:
            continue
        if parts[3].strip().lower() != "insgesamt":
            continue
        region_code = parts[1].strip()
        value = _to_number(parts[10])
        if value is None:
            continue
        by_region.setdefault(region_code, {})[int(year_match.group(0))] = value

    return {
        code: [{"year": year, "value": year_map[year]} for year in sorted(year_map.keys())]
        for code, year_map in by_region.items()
        if year_map
    }


def parse_unemployment_csv_by_region(
    csv_text: str,
    column: str,
) -> dict[str, list[dict[str, float]]]:
    lines = [_clean_line(line) for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return {}

    year_line = next((line for line in lines if line.lower().startswith("jahr:")), "")
    year_match = YEAR_PATTERN.search(year_line)
    if not year_match:
        return {}
    year = int(year_match.group(0))

    column_index_map = {
        "total": 2,
        "foreign": 3,
        "longterm": 8,
    }
    col_idx = column_index_map.get(column)
    if col_idx is None:
        return {}

    by_region: dict[str, list[dict[str, float]]] = {}
    for line in lines:
        match = ROW_CODE_PATTERN.match(line)
        if not match:
            continue
        parts = line.split(";")
        if len(parts) <= col_idx:
            continue
        value = _to_number(parts[col_idx])
        if value is None:
            continue
        by_region[match.group(1).strip()] = [{"year": year, "value": value}]
    return by_region


def parse_unemployment_rate_csv_by_region(csv_text: str) -> dict[str, list[dict[str, float]]]:
    lines = [_clean_line(line) for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return {}

    by_region: dict[str, dict[int, float]] = {}
    for line in lines:
        parts = line.split(";")
        # Layout: year;ags;name;arbeitslosenquote;...
        if len(parts) < 4:
            continue
        year = _to_number(parts[0])
        if year is None:
            continue
        region_code = parts[1].strip()
        value = _to_number(parts[3])
        if value is None:
            continue
        by_region.setdefault(region_code, {})[int(year)] = value

    return {
        code: [{"year": year, "value": year_map[year]} for year in sorted(year_map.keys())]
        for code, year_map in by_region.items()
        if year_map
    }


def parse_migration_over_county_csv_by_region(
    csv_text: str,
    direction: str,
) -> dict[str, list[dict[str, float]]]:
    lines = [_clean_line(line) for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return {}

    year_line = next((line for line in lines if line.lower().startswith("jahr:")), "")
    year_match = YEAR_PATTERN.search(year_line)
    if not year_match:
        return {}
    year = int(year_match.group(0))

    # Layout:
    # code;name;altersgruppe;zuzuege_insg;z_m;z_w;fortzuege_insg;f_m;f_w
    column_index_map = {
        "inflow": 3,
        "outflow": 6,
    }
    col_idx = column_index_map.get(direction)
    if col_idx is None:
        return {}

    by_region: dict[str, list[dict[str, float]]] = {}
    for line in lines:
        match = ROW_CODE_PATTERN.match(line)
        if not match:
            continue
        parts = line.split(";")
        if len(parts) <= col_idx:
            continue
        if len(parts) < 3:
            continue
        if _normalize(parts[2].strip()) != "insgesamt":
            continue
        value = _to_number(parts[col_idx])
        if value is None:
            continue
        by_region[match.group(1).strip()] = [{"year": year, "value": value}]
    return by_region


def parse_migration_timeseries_csv_by_region_name(
    csv_text: str,
    direction: str,
) -> dict[str, list[dict[str, float]]]:
    lines = [_clean_line(line) for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return {}

    years_line = next((line for line in lines if line.startswith(";;;20")), "")
    if not years_line:
        return {}
    year_values = [int(value) for value in re.findall(r"(?:19|20)\d{2}", years_line)]
    if not year_values:
        return {}

    direction_token = (
        "zuzuege ueber die kreisgrenzen"
        if direction == "inflow"
        else "fortzuege ueber die kreisgrenzen"
    )
    by_region: dict[str, dict[int, float]] = {}
    for line in lines:
        if line.startswith(";"):
            continue
        parts = line.split(";")
        if len(parts) < 4:
            continue
        region_name = parts[0].strip()
        metric_name = _normalize(parts[1].strip())
        if direction_token not in metric_name:
            continue

        values = parts[3 : 3 + len(year_values)]
        for year, raw_value in zip(year_values, values):
            value = _to_number(raw_value)
            if value is None:
                continue
            by_region.setdefault(region_name, {})[year] = value

    return {
        region_name: [{"year": year, "value": year_map[year]} for year in sorted(year_map.keys())]
        for region_name, year_map in by_region.items()
        if year_map
    }


def parse_average_age_timeseries_csv_by_region_name(
    csv_text: str,
) -> dict[str, list[dict[str, float]]]:
    lines = [_clean_line(line) for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return {}

    years_line = next(
        (
            line
            for line in lines
            if line.startswith(";;;")
            and len(re.findall(r"(?:19|20)\d{2}", line)) >= 1
        ),
        "",
    )
    if not years_line:
        return {}
    year_values = [int(value) for value in re.findall(r"(?:19|20)\d{2}", years_line)]
    if not year_values:
        return {}

    by_region: dict[str, dict[int, float]] = {}
    for line in lines:
        if line.startswith(";"):
            continue
        parts = line.split(";")
        if len(parts) < 4:
            continue
        metric_name = _normalize(parts[1].strip())
        if "durchschnittsalter" not in metric_name:
            continue

        region_name = parts[0].strip()
        values = parts[3 : 3 + len(year_values)]
        for year, raw_value in zip(year_values, values):
            value = _to_number(raw_value)
            if value is None:
                continue
            by_region.setdefault(region_name, {})[year] = value

    return {
        region_name: [{"year": year, "value": year_map[year]} for year in sorted(year_map.keys())]
        for region_name, year_map in by_region.items()
        if year_map
    }


def _age_group_midpoint(age_group_label: str) -> float | None:
    normalized = _normalize(age_group_label)
    if normalized == "insgesamt":
        return None

    range_match = re.search(r"(\d+)\s+bis\s+unter\s+(\d+)\s+jahre?", normalized)
    if range_match:
        lower = int(range_match.group(1))
        upper = int(range_match.group(2))
        return (lower + upper) / 2.0

    open_end_match = re.search(r"(\d+)\s+jahre?\s+und\s+mehr", normalized)
    if open_end_match:
        lower = int(open_end_match.group(1))
        # Open-ended classes require an assumption; 2.5 years keeps bins comparable.
        return lower + 2.5

    under_match = re.search(r"^unter\s+(\d+)\s+jahre?", normalized)
    if under_match:
        upper = int(under_match.group(1))
        return upper / 2.0

    return None


def parse_average_age_nationality_csv_by_region(
    csv_text: str,
) -> tuple[dict[str, list[dict[str, float]]], dict[str, list[dict[str, float]]]]:
    lines = [_clean_line(line) for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return {}, {}

    german_weighted: dict[str, dict[int, float]] = {}
    german_totals: dict[str, dict[int, float]] = {}
    foreign_weighted: dict[str, dict[int, float]] = {}
    foreign_totals: dict[str, dict[int, float]] = {}

    for line in lines:
        parts = line.split(";")
        if len(parts) < 13:
            continue

        year_match = YEAR_PATTERN.search(parts[0])
        if not year_match:
            continue
        year = int(year_match.group(0))
        region_code = parts[1].strip()
        midpoint = _age_group_midpoint(parts[3])
        if midpoint is None:
            continue

        german_count = _to_number(parts[7])
        foreign_count = _to_number(parts[10])

        if german_count is not None and german_count > 0:
            german_weighted.setdefault(region_code, {}).setdefault(year, 0.0)
            german_totals.setdefault(region_code, {}).setdefault(year, 0.0)
            german_weighted[region_code][year] += midpoint * german_count
            german_totals[region_code][year] += german_count

        if foreign_count is not None and foreign_count > 0:
            foreign_weighted.setdefault(region_code, {}).setdefault(year, 0.0)
            foreign_totals.setdefault(region_code, {}).setdefault(year, 0.0)
            foreign_weighted[region_code][year] += midpoint * foreign_count
            foreign_totals[region_code][year] += foreign_count

    def _finalize(
        weighted_sums: dict[str, dict[int, float]],
        totals: dict[str, dict[int, float]],
    ) -> dict[str, list[dict[str, float]]]:
        result: dict[str, list[dict[str, float]]] = {}
        for region_code, year_map in weighted_sums.items():
            values: list[dict[str, float]] = []
            for year, weighted_sum in sorted(year_map.items()):
                total = totals.get(region_code, {}).get(year, 0.0)
                if total <= 0:
                    continue
                values.append({"year": year, "value": weighted_sum / total})
            if values:
                result[region_code] = values
        return result

    return _finalize(german_weighted, german_totals), _finalize(foreign_weighted, foreign_totals)


def parse_unemployment_groups_timeseries_csv_by_region_name(
    csv_text: str,
    category_tokens: tuple[str, ...],
) -> dict[str, list[dict[str, float]]]:
    lines = [_clean_line(line) for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return {}

    years_line = next(
        (
            line
            for line in lines
            if line.startswith(";;")
            and len(re.findall(r"(?:19|20)\d{2}", line)) >= 2
        ),
        "",
    )
    if not years_line:
        return {}
    year_values = [int(value) for value in re.findall(r"(?:19|20)\d{2}", years_line)]
    if not year_values:
        return {}

    token_norm = tuple(_normalize(token) for token in category_tokens)
    by_region: dict[str, dict[int, float]] = {}
    for line in lines:
        if line.startswith(";"):
            continue
        parts = line.split(";")
        if len(parts) < 3:
            continue
        category = _normalize(parts[0].strip())
        if token_norm and not _matches_selector(category, token_norm):
            continue
        region_name = parts[1].strip()
        values = parts[2 : 2 + len(year_values)]
        for year, raw_value in zip(year_values, values):
            value = _to_number(raw_value)
            if value is None:
                continue
            by_region.setdefault(region_name, {})[year] = value

    return {
        region_name: [{"year": year, "value": year_map[year]} for year in sorted(year_map.keys())]
        for region_name, year_map in by_region.items()
        if year_map
    }


def parse_unemployment_metrics_timeseries_csv_by_region_name(
    csv_text: str,
    metric_tokens: tuple[str, ...],
) -> dict[str, list[dict[str, float]]]:
    lines = [_clean_line(line) for line in csv_text.splitlines() if line.strip()]
    if not lines:
        return {}

    years_line = next(
        (
            line
            for line in lines
            if line.startswith(";;;")
            and len(re.findall(r"(?:19|20)\d{2}", line)) >= 2
        ),
        "",
    )
    if not years_line:
        return {}
    year_values = [int(value) for value in re.findall(r"(?:19|20)\d{2}", years_line)]
    if not year_values:
        return {}

    token_norm = tuple(_normalize(token) for token in metric_tokens)
    by_region: dict[str, dict[int, float]] = {}
    for line in lines:
        if line.startswith(";"):
            continue
        parts = line.split(";")
        if len(parts) < 4:
            continue
        region_name = parts[0].strip()
        metric_name = _normalize(parts[1].strip())
        if token_norm and not _matches_selector(metric_name, token_norm):
            continue
        values = parts[3 : 3 + len(year_values)]
        for year, raw_value in zip(year_values, values):
            value = _to_number(raw_value)
            if value is None:
                continue
            by_region.setdefault(region_name, {})[year] = value

    return {
        region_name: [{"year": year, "value": year_map[year]} for year in sorted(year_map.keys())]
        for region_name, year_map in by_region.items()
        if year_map
    }
