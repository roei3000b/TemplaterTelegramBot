import json
import shutil
import tempfile
import zipfile

import requests
import re
import os
from lxml import etree

from . import exceptions, lex

TOKENIZED_PATTERN = re.compile(r"\w*{{(.*)}}\w*")
TEMPLATER_PARSER = lex.TemplaterParser()


def get_times(city):
    response = requests.get(f"https://www.yeshiva.org.il/calendar/shabatot?place={city}")
    if response.status_code != 200:
        raise Exception("Failed to get next times")
    times = re.search(r"defaultData = JSON\.parse\(\'(.*?)\'\);", response.text).groups()[0]
    times = times.replace("\\\\", "\\")
    times = times.replace("'", "\"")
    json_times = json.loads(times)
    if json_times["place"]["name"] != city:
        raise exceptions.NoSuchCity("Wrong city")
    return json_times


def init_replacements(city):
    json_times = get_times(city)
    # TODO: check next holiday
    next_shabbat = json_times["nextShabbat"]
    parsed_times = {k["name"]: k["value"] for k in next_shabbat["times"]}

    replacements = {
        # english
        "parasha": next_shabbat["shabat_name"],
        "enter_time": parsed_times["כניסת שבת"],
        "exit_time": parsed_times["צאת שבת"],
        "rabino_tam": parsed_times['צאת שבת ר"ת'],
        "sunset": next_shabbat["skiah"],

        # hebrew
        "פרשה": next_shabbat["shabat_name"],
        "כניסת_שבת": parsed_times["כניסת שבת"],
        "צאת_שבת": parsed_times["צאת שבת"],
        "רבינו_תם": parsed_times['צאת שבת ר"ת'],
        "שקיעה": next_shabbat["skiah"],
    }
    return replacements


def parse_token(token):
    return TEMPLATER_PARSER.parse(token[2:-2])


def fill_word_template(template_file_name, target_directory, city):
    TEMPLATER_PARSER.set_names(init_replacements(city))
    with tempfile.TemporaryDirectory() as dir_name:
        shutil.copy(template_file_name, f"{dir_name}/input.zip")
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
                while text_element.text and index < len(text_element.text):
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

                            cross_line_token[0].text = cross_line_token[0].text[:start_index]
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
            file_name = f"לוז שבת פרשת {TEMPLATER_PARSER.names['parasha']}"
            shutil.move(f"{target_directory}/output.zip", f"{target_directory}/{file_name}.docx")
            return f"{target_directory}/{file_name}.docx"

def fill_ppt_template(template_file_name, target_directory, city):
    TEMPLATER_PARSER.set_names(init_replacements(city))
    with tempfile.TemporaryDirectory() as dir_name:
        shutil.copy(template_file_name, f"{dir_name}/input.zip")
        with zipfile.ZipFile(f"{dir_name}/input.zip", 'r') as zip_ref:
            extracted_path = dir_name + "/extracted"
            zip_ref.extractall(extracted_path)

            template_file_dir = f"{extracted_path}/ppt/slides"
            for slide in os.listdir(template_file_dir):
                template_file_name = f"{template_file_dir}/{slide}"
                if not template_file_name.endswith(".xml"):
                    continue
                tree = etree.parse(template_file_name)
                root = tree.getroot()
                text_elements = root.xpath("//*[local-name()='t']")

                maybe_token = False
                cross_line_token = []
                for text_element in text_elements:
                    index = 0
                    replaced_text = ""
                    while text_element.text and index < len(text_element.text):
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

                                cross_line_token[0].text = cross_line_token[0].text[:start_index]
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
            file_name = f"לוז שבת פרשת {TEMPLATER_PARSER.names['parasha']}"
            shutil.move(f"{target_directory}/output.zip", f"{target_directory}/{file_name}.pptx")
            return f"{target_directory}/{file_name}.pptx"