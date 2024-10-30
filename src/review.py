import os
import re

import automatic_code_review_commons as commons


def review(config):
    path_source = config['path_source_v2']
    changes = config['merge']['changes']
    message_incorrect_path = config['messageIncorrectPath']
    message_incorrect_prefix = config['messageIncorrectPrefix']

    comments = []

    for change in changes:
        new_path = change['new_path']
        path = path_source + "/" + new_path

        if not path.endswith(('.h', '.cpp')):
            continue

        comments.extend(__review_by_file(message_incorrect_path, message_incorrect_prefix, path, path_source))

    return comments


def __check_regex_list(regex_list, text):
    for regex in regex_list:
        if re.match(regex, text):
            return True

    return False


def __review_by_file(message_incorrect_path, message_incorrect_prefix, path, path_source):
    with open(path, 'r') as arquivo:
        lines = arquivo.readlines()

    regex_list_to_ignore = [".*ui_.*", ".*\.moc"]

    if path.endswith(".cpp"):
        header_file = path.split("/")
        header_file = header_file[len(header_file) - 1]
        header_file = header_file.replace(".cpp", ".h")
        regex_list_to_ignore.insert(0, f"#include \"{header_file}\"")
        regex_list_to_ignore.insert(0, f"#include \".*/{header_file}\"")

    comments = []
    line_number = 0

    for line in lines:
        line_number += 1
        line = line.strip()

        if not line.startswith("#include "):
            continue

        if __check_regex_list(regex_list_to_ignore, line):
            continue

        comments.extend(__review_by_line(
            line=line,
            message_incorrect_path=message_incorrect_path,
            message_incorrect_prefix=message_incorrect_prefix,
            path=path,
            path_source=path_source,
            line_number=line_number
        ))

    return comments


def __review_by_line(line, message_incorrect_path, message_incorrect_prefix, path, path_source, line_number):
    comments = []
    line = line[9:]

    if line[0] == '"':
        comments.extend(__review_quote_is_ok(
            line=line,
            path=path,
            message_incorrect_path=message_incorrect_path,
            path_source=path_source,
            message_incorrect_prefix=message_incorrect_prefix,
            line_number=line_number
        ))

    if line[0] == '<':
        comments.extend(__review_bracket_is_ok(
            line=line,
            path=path,
            message_incorrect_prefix=message_incorrect_prefix,
            path_source=path_source,
            line_number=line_number
        ))

    return comments


def __review_quote_is_ok(line, path, message_incorrect_path, path_source, message_incorrect_prefix, line_number):
    comments = []
    is_relative, include_path, correct_path = __is_in_folder(line, path)

    if correct_path is not None and correct_path != include_path:
        comment_path = path.replace(path_source, "")[1:]
        comment_description = f"{message_incorrect_path}"
        comment_description = comment_description.replace("${CORRECT_PATH}", correct_path)
        comment_description = comment_description.replace("${INCORRECT_PATH}", include_path)
        comment_description = comment_description.replace("${FILE_PATH}", comment_path)

        comments.append(commons.comment_create(
            comment_id=commons.comment_generate_id(comment_description),
            comment_path=comment_path,
            comment_description=comment_description,
            comment_snipset=True,
            comment_end_line=line_number,
            comment_start_line=line_number,
            comment_language='c++',
        ))

    if not is_relative:
        comment_path = path.replace(path_source, "")[1:]
        comment_description = f"{message_incorrect_prefix}"
        comment_description = comment_description.replace("${CORRECT_PREFIX}", '<>')
        comment_description = comment_description.replace("${INCORRECT_PREFIX}", '""')
        comment_description = comment_description.replace("${INCLUDE}", include_path)
        comment_description = comment_description.replace("${FILE_PATH}", comment_path)

        comments.append(commons.comment_create(
            comment_id=commons.comment_generate_id(comment_description),
            comment_path=comment_path,
            comment_description=comment_description,
            comment_snipset=True,
            comment_end_line=line_number,
            comment_start_line=line_number,
            comment_language='c++',
        ))

    return comments


def __review_bracket_is_ok(line, path, message_incorrect_prefix, path_source, line_number):
    comments = []
    is_relative, include_path, correct_path = __is_in_folder(line, path)

    if is_relative:
        comment_path = path.replace(path_source, "")[1:]
        comment_description = f"{message_incorrect_prefix}"
        comment_description = comment_description.replace("${CORRECT_PREFIX}", '""')
        comment_description = comment_description.replace("${INCORRECT_PREFIX}", '<>')
        comment_description = comment_description.replace("${INCLUDE}", include_path)
        comment_description = comment_description.replace("${FILE_PATH}", comment_path)

        comments.append(commons.comment_create(
            comment_id=commons.comment_generate_id(comment_description),
            comment_path=comment_path,
            comment_description=comment_description,
            comment_snipset=True,
            comment_end_line=line_number,
            comment_start_line=line_number,
            comment_language='c++',
        ))

    return comments


def __is_in_folder(line, path):
    include_path = line[1:]
    include_path = include_path[0:len(include_path) - 1]

    parts = include_path.split('/')
    relative_path = path[0:path.rindex('/')]

    for i in range(0, len(parts)):
        current_parts = parts[i:]
        current_relative_path = "/".join(current_parts)
        check_path = f"{relative_path}/{current_relative_path}"

        if os.path.isfile(check_path):
            return True, include_path, current_relative_path

    return False, include_path, None
