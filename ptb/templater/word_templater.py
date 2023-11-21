import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta

import requests
import re
from lxml import etree

CITY = "חריש"


replacements = {
}

TOKENIZED_PATTERN = re.compile(r"\w*{{(.*)}}\w*")


def add_minutes_to_time(time_str, minutes):
    datetime_obj = datetime.strptime(time_str, '%H:%M')
    new_datetime_obj = datetime_obj + timedelta(minutes=minutes)
    return new_datetime_obj.time().strftime('%H:%M')


def get_times(city):
    response = requests.get(f"https://www.yeshiva.org.il/calendar/shabatot?place={city}")
    if response.status_code != 200:
        raise Exception("Failed to get next times")
    times = re.search(r"defaultData = JSON\.parse\(\'(.*?)\'\);", response.text).groups()[0]
    times = times.replace("\\\\", "\\")
    times = times.replace("'", "\"")
    json_times = json.loads(times)
    if json_times["place"]["name"] != CITY:
        raise Exception("Wrong city")
    return json_times


def init_replacements(city):
    global replacements
    json_times = get_times(city)
    # TODO: check next holiday
    next_shabbat = json_times["nextShabbat"]
    parsed_times = {k["name"]: k["value"] for k in next_shabbat["times"]}

    replacements = {
        "parasha": next_shabbat["shabat_name"],
        "enter_time": parsed_times["כניסת שבת"],
        "exit_time": parsed_times["צאת שבת"],
        "rabino_tam": parsed_times['צאת שבת ר"ת'],
        "sunset": next_shabbat["skiah"],
    }


def get_token(word):
    result = re.search(TOKENIZED_PATTERN, word)
    return result


def get_replacement(token):
    global replacements
    return replacements.get(token, token)

def parse_token(token):
    global replacements
    token = token.replace(" ", "")
    # assuming we got token in the form of {{.*}} so we remove the {{ and }}
    token = token[2:-2]

    splited_token = token.split("=")
    if len(splited_token) > 2:
        raise Exception("Wrong token")

    if len(splited_token) == 2:
        replacements[splited_token[0]] = calculate_token(splited_token[1])
        return replacements[splited_token[0]]

    return calculate_token(splited_token[0])


def calculate_token(token):
    if get_replacement(token) != token:
        return get_replacement(token)
    calculated_token = "0"
    current_word = ""
    next_action = "+"
    for c in token:
        if c == "+" or c == "-":
            if calculated_token.isnumeric() and current_word.isnumeric():
                calculated_token = str(int(calculated_token) + int(next_action+current_word))
            else:
                calculated_token = call_correct_function(calculated_token, current_word, next_action)

            next_action = c
            current_word = ""
        else:
            current_word += c
    calculated_token = call_correct_function(calculated_token, current_word, next_action)
    return calculated_token


def call_correct_function(calculated_token, current_word, next_action):
    if not calculated_token.isnumeric():
        calculated_token = get_replacement(calculated_token)
        calculated_token = add_minutes_to_time(get_replacement(calculated_token),
                                               int(next_action + current_word))
    elif not current_word.isnumeric():
        current_word = get_replacement(current_word)
        calculated_token = add_minutes_to_time(current_word,
                                               int(next_action + calculated_token))
    return calculated_token


def replace_if_needed(inner_content):
    token = get_token(inner_content.text)
    if token:
        inner_content.text = get_replacement(token)


def remove_element_from_xml(element):
    element.getparent().remove(element)


def fill_template(template_file_name, target_directory, city):
    init_replacements(city)
    with tempfile.TemporaryDirectory() as dir_name:
        shutil.copy(template_file_name, f"{dir_name}/input.zip")
        # shutil.copy(f"{dir_name}/input.zip", f"{target_directory}/output.docx", )

        with zipfile.ZipFile(f"{dir_name}/input.zip", 'r') as zip_ref:
            extracted_path = dir_name + "/extracted"
            zip_ref.extractall(extracted_path)

            template_file_name = f"{extracted_path}/word/document.xml"

            tree = etree.parse(template_file_name)
            root = tree.getroot()
            text_elements = root.xpath("//*[local-name()='t']")

            maybe_token = False
            cross_line_token = []
            for text_element in text_elements:
                index = 0
                replaced_text = ""
                while index < len(text_element.text):
                    if text_element.text[index:index+2] == '{{':
                        start_index = index
                        maybe_token = True
                        index += 2
                        replaced_text += text_element.text[start_index:index]
                    elif maybe_token and text_element.text[index:index+2] == '}}':
                        end_index = index + 2
                        maybe_token = False
                        if not cross_line_token:
                            token = text_element.text[start_index:end_index]
                            replaced_text = replaced_text[:start_index] + parse_token(token)
                        else:
                            token = "".join([t.text for t in cross_line_token])
                            token += text_element.text[:end_index]
                            token = token[start_index:]

                            cross_line_token[0].text = cross_line_token[0].text[start_index+2:]
                            cross_line_token.pop(0)

                            for c in cross_line_token:
                                c.text = ''
                            replaced_text = parse_token(token)
                            cross_line_token = []
                            start_index = 0
                        index += 2
                    else:
                        replaced_text += text_element.text[index]
                        index += 1
                text_element.text = replaced_text
                if maybe_token:
                    cross_line_token.append(text_element)
            tree.write(template_file_name)
            shutil.make_archive(f"{target_directory}/output", 'zip', extracted_path)
            file_name = f"לוז שבת פרשת {replacements['parasha']}"
            shutil.move(f"{target_directory}/output.zip", f"{target_directory}/{file_name}.docx")
            return f"{target_directory}/{file_name}.docx"