import glob
import json
import pathlib
import shutil
import tempfile
import zipfile

import requests
import re
import os
from lxml import etree
from abc import ABC, abstractmethod

from . import exceptions, lex

TOKENIZED_PATTERN = re.compile(r"\w*{{(.*)}}\w*")
TEMPLATER_PARSER = lex.TemplaterParser()

class UnsupportedFileType(Exception):
    pass

class Templater(ABC):
    def __init__(self):
        self.templater_parser = lex.TemplaterParser()

    @abstractmethod
    def get_text_from_element(self, element):
        pass

    @abstractmethod
    def set_text_in_element(self, element, text):
        pass

    @abstractmethod
    def get_next_element(self):
        pass

    def parse_token(self, token):
        return self.templater_parser.parse(token[2:-2])

    def fill_template(self, city, *args, **kwargs):
        self.templater_parser.set_names(init_replacements(city))
        maybe_token = False
        cross_line_token = []
        while True:
            element = self.get_next_element()
            if element is None:
                break

            text_element = self.get_text_from_element(element)
            replaced_text = ""
            index = 0
            while text_element and index < len(text_element):
                if text_element[index:index + 2] == '{{':
                    start_index = index
                    maybe_token = True
                    index += 2
                    replaced_text += text_element[start_index:index]
                elif maybe_token and text_element[index:index + 2] == '}}':
                    end_index = index + 2
                    maybe_token = False
                    if not cross_line_token:
                        token = text_element[start_index:end_index]
                        replaced_text = replaced_text[:start_index] + self.parse_token(token)
                    else:
                        token = "".join([self.get_text_from_element(t) for t in cross_line_token])
                        token += text_element[:end_index]
                        token = token[start_index:]

                        self.set_text_in_element(cross_line_token[0],
                                                 self.get_text_from_element(cross_line_token[0])[:start_index])
                        cross_line_token.pop(0)

                        for c in cross_line_token:
                            self.set_text_in_element(c, "")
                        replaced_text = self.parse_token(token)
                        cross_line_token = []
                        start_index = 0
                    index += 2
                else:
                    replaced_text += text_element[index]
                    index += 1
            self.set_text_in_element(element, replaced_text)
            if maybe_token:
                cross_line_token.append(element)


class XMLTemplater(Templater):
    def __init__(self):
        super().__init__()
        self.tree = None
        self.xml_file_path = None
        self.text_elements = None
        self.index = None

    def init_xml(self, xml_file_path, xpath="//*[local-name()='t']"):
        self.xml_file_path = xml_file_path
        self.tree = etree.parse(xml_file_path)
        root = self.tree.getroot()
        self.text_elements = root.xpath(xpath)
        self.index = 0

    def get_text_from_element(self, element):
        return element.text

    def set_text_in_element(self, element, text):
        element.text = text

    def get_next_element(self):
        if self.index >= len(self.text_elements):
            return None
        element = self.text_elements[self.index]
        self.index += 1
        return element

    def fill_template(self, city, xml_file_path, *args, **kwargs):
        self.init_xml(xml_file_path)
        super().fill_template(city)
        self.tree.write(self.xml_file_path)



class OfficeTemplater(XMLTemplater, ABC):
    @abstractmethod
    def glob_path(self):
        pass

    @abstractmethod
    def file_extension(self):
        pass

    def fill_template(self, city, office_file_name, target_directory, *args, **kwargs):
        with tempfile.TemporaryDirectory() as dir_name:
            shutil.copy(office_file_name, f"{dir_name}/input.zip")
            with zipfile.ZipFile(f"{dir_name}/input.zip", 'r') as zip_ref:
                extracted_path = dir_name + "/extracted"
                zip_ref.extractall(extracted_path)
                for file in glob.glob(os.path.join(extracted_path, self.glob_path())):
                    self.init_xml(file)
                    super().fill_template(city, file)
                    self.tree.write(file)

            shutil.make_archive(f"{target_directory}/output", 'zip', extracted_path)
            file_name = f"לוז שבת פרשת {self.templater_parser.names['parasha']}"
            target_path = f"{target_directory}/{file_name}.{self.file_extension()}"
            shutil.move(f"{target_directory}/output.zip", target_path)
            return target_path


class WordTemplater(OfficeTemplater):
    def glob_path(self):
        return "word/document.xml"

    def file_extension(self):
        return "docx"

class PowerPointTemplater(OfficeTemplater):
    def glob_path(self):
        return "ppt/slides/slide*.xml"

    def file_extension(self):
        return "pptx"

def resolve_cities_id_dictionary(file_name):
    pattern = r'<option value="(\d+)">([^<]+)</option>'

    with open(file_name, encoding='utf-8') as f:
        cities_dict = {name: int(city_id) for city_id, name in re.findall(pattern, f.read())}

    return cities_dict

def get_times(city):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    places_file = os.path.join(script_dir, "places.txt")
    cities_dict = resolve_cities_id_dictionary(places_file)
    if city not in cities_dict:
        raise Exception("City not found")
    response = requests.get(f"https://www.yeshiva.org.il/api/times/AllDailyTimes?cacheVer=51&place={cities_dict[city]}", headers={"Referer": "https://www.yeshiva.org.il/"})
    if response.status_code != 200:
        raise Exception("Failed to get next times")
    json_times = response.json()
    if json_times["standardTimes"]["place"]["name"] != city:
        raise Exception("Wrong city")
    return json_times


def init_replacements(city):
    json_times = get_times(city)
    # TODO: check next holiday
    next_shabbat = json_times["standardTimes"]["shabat"]
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
    additional_times = json_times["standardTimes"]["times"]
    parsed_times = {k["name"].replace(" ", "_").replace('"', "").replace(")", "_").replace("(","_"): k["value"] for k in additional_times}
    replacements.update(parsed_times)
    return replacements


def parse_token(token):
    return TEMPLATER_PARSER.parse(token[2:-2])

def fill_template(city, office_file_name, target_directory):
    extension = pathlib.Path(office_file_name).suffix
    if extension == ".docx":
        templater = WordTemplater()
    elif extension == ".pptx":
        templater = PowerPointTemplater()
    else:
        raise UnsupportedFileType(extension)
    return templater.fill_template(city, office_file_name, target_directory)
