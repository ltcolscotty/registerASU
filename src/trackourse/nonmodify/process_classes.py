import re
from datetime import datetime

import trackourse.const_config as cc


def remove_extra_newlines(uncleaned: str):
    """Removes extra newline characters
    Args:
        uncleaned: str

    Returns:
        str: removed extra newline characters
    """
    lines = uncleaned.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    return "\n".join(non_empty_lines)


def group_class_strings(class_string):
    """Groups classes together
    Args:
        class_string: str - unprocessed string

    Returns:
        list[str]: list of partitioned classes for standardize_reg and hybrid to standardize
    """
    # Regular expression to match the entire class entry
    class_string = remove_extra_newlines(class_string)

    pattern = r"([A-Z0-9]{3}\s\d{3}[A-Z]?\n.*?)\n(\d+ of \d+)(?=\n\n[A-Z0-9]{3}\s\d{3}[A-Z]?|\Z)"
    matches = re.finditer(pattern, class_string, re.DOTALL)

    result = []
    for match in matches:
        class_info = match.group(1).strip()
        capacity = match.group(2)
        result.append(f"{class_info}\n{capacity}")

    return result


def standardize_reg(input_data):
    """Standardizes format for regular classes
    Args:
        input_data: one class that is unstandardized

    Returns:
        str: standardized format string
    """
    lines = input_data.split("\n")
    standardized_lines = []

    for idx, line in enumerate(lines):
        cleaned_line = line.strip().replace("�", "")
        if cleaned_line:
            if idx == 0 or idx == 1:
                standardized_lines.append(cleaned_line)
            elif idx == 2:
                standardized_lines.append(cleaned_line)
            elif "|" in cleaned_line:
                standardized_lines.append(cleaned_line)
            elif re.search(r"\d+ of \d+", cleaned_line):
                standardized_lines.append(cleaned_line)

    return "\n".join(standardized_lines)


def standardize_hybrid(input_data):
    """Standardizes format for hybrid classes
    Args:
        input_data: one hybrid class that is unstandardized

    Returns:
        str: standardized format string
    """

    if cc.dev_mode:
        print("Standardizing hybrid class")

    lines = input_data.split("\n")
    corrected_lines = []

    time_info = ""
    for i, line in enumerate(lines):
        cleaned_line = line.strip().replace("�", "")

        if not cleaned_line:
            continue

        if "Multiple dates and times" in cleaned_line or "Hybrid" in cleaned_line:
            time_info = cleaned_line.replace("Multiple dates and times", "Hybrid")
        elif "-" in cleaned_line and time_info:
            time_info += cleaned_line
            corrected_lines.append(time_info)
            time_info = ""
        elif "Tempe" in cleaned_line or "Internet - Hybrid" in cleaned_line:
            continue
        else:
            corrected_lines.append(cleaned_line)

    return "\n".join(corrected_lines)


def is_not_hybrid(course_input):
    """Checks if entry is a hybrid class or not for processing
    Args:
        course_input: str - one course information

    Returns:
        bool: true if course is a regular course
    """
    lines = course_input.split("\n")

    # Check if the entry has at least 6 lines (non-hybrid entries have exactly 6 lines)
    if len(lines) != 6:
        return False

    # Check if the location doesn't contain "Internet - Hybrid"
    if "Internet - Hybrid" in lines[4]:
        return False

    # If all checks pass, it's a non-hybrid course
    return True


def standardize(input):
    """Standardizes total input
    Args:
        input: str - raw preprocessed input
    Returns:
        list[str]: Standardized info
    """

    info_list = group_class_strings(input)

    print(f"Info List: {info_list}")

    for i, course in enumerate(info_list):
        if is_not_hybrid(course):
            info_list[i] = standardize_reg(course)
        else:
            info_list[i] = standardize_hybrid(course)

    return info_list


def process_class(input_string):
    """puts one class into a dictionary information format
    Args:
        input_string: str - one class's standardized information

    Returns:
        dict: one dictionary entry for the input class
    """
    lines = input_string.strip().split("\n")

    if len(lines) != 5:
        raise ValueError("Input must contain exactly 5 lines.")

    course = lines[0].strip()
    course_id = lines[1].strip()
    instructor = lines[2].strip()
    schedule_line = lines[3].strip()
    capacity_line = lines[4].strip()

    if "Hybrid" in schedule_line:
        days = "Hybrid"
        time_info = schedule_line.split("|")[1].strip()
    else:
        days, time_info = schedule_line.split("|")
        days = days.strip()

    start_time, end_time = time_info.strip().split("-")
    start_time = start_time.strip()
    end_time = end_time.strip()

    open_spots, total_spots = map(int, capacity_line.split("of"))
    is_open = open_spots > 0

    result = {
        "Course": course,
        "ID": course_id,
        "Instructor": instructor,
        "Days": days,
        "Start time": start_time,
        "End time": end_time,
        "Open": is_open,
    }

    return result


def filter_info(agg_data, ID_list):
    """Processes dictionary data
    Args:
        agg_data: Dict - processed data in dictionary format
        workingClass: class_info.class_info - class of interest
    Returns:
        list[int] - class codes that match and have spots
    """

    returned_ids = []
    for class_data in agg_data:
        if ID_list is not None and class_data["ID"] in ID_list:
            returned_ids.append(
                {
                    "ID": class_data["ID"],
                    "Professors": class_data["Instructor"],
                    "Start time": class_data["Start time"],
                    "End time": class_data["End time"],
                    "Days": class_data["Days"],
                }
            )

    return returned_ids


def isAfter(input_time: str, target: datetime):
    """Determines if the input is after the target (input is after target)
    Args:
        input_time: str - time to compare
        target: datetime - time to compare to
    Returns:
        bool: whether input is after target
    """
    input_time = datetime.strptime(input_time, "%I:%M %p")
    return input_time > target


def isBefore(input_time: str, target: datetime):
    """Determines if the input is before the target (input is before target)
    Args:
        input_time: str - time to compare
        target: datetime - time to compare to
    Returns:
        bool: Whether input is before target
    """
    input_time = datetime.strptime(input_time, "%I:%M %p")
    return input_time < target


def compare_results(prev_results, cur_results):
    """Compares results and returns the difference if there are any
    Args:
        prev_results: list[dict] - list of classes from previous update
        cur_results: list[dict] - list of classes from current update to be processed

    Returns:
        list[dict] - list of new classes
    """

    if not prev_results:
        return cur_results

    ids_prev = {course["ID"] for course in prev_results}
    return [course for course in cur_results if course["ID"] not in ids_prev]
