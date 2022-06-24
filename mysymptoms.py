import csv
from datetime import datetime, timedelta
import sys
import os
import argparse
import json
from typing import List, Tuple


DATE_COLUMN = 0
TIME_COLUMN = 1
CATEGORIZATION_COLUMN = 2


class Config:
    """
    The config reads from the config.json file and the user-supplied CLI parameters to initialize settings for this program.
    """
    config_file = "config.json"

    def __init__(self) -> Tuple[str, str]:
        """grab user supplied arguments using the argparse library. Any argument not supplied is pulled from config.json."""
        default_json = self._load_config_file()
        args = self._parse_arguments(default_json)
        self.input_file = args.input_file
        self.output_file = args.output_file
        self.consumables = args.consumables
        self.symptoms = args.symptoms
        self.min_times_consumed = args.min_times_consumed
        self.symptom_warning_score = args.symptom_warning_score
        # change integer into a timedelta object to use for time comparison later
        self.symptom_onset_hours = timedelta(hours=args.symptom_onset_hours)

    def _load_config_file(self) -> dict:
        """returns python object from the json configuration file"""
        with open(self.config_file) as config_file:
            return json.load(config_file)

    def _parse_arguments(self, defaults: dict):
        """grab user supplied arguments using the argparse library. Any argument not supplied is pulled from the dict of defaults."""
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--input_file", required=False, default=defaults["input_file"],
                            help="csv input file (with extension)", type=str)
        parser.add_argument("-o", "--output_file", required=False, default=defaults["output_file"],
                            help="json output file (with extension)", type=str)
        parser.add_argument("-c", "--consumables", required=False, default=defaults["consumables"],
                            help="list of consumables to analyze, for example, 'Breakfast', 'Snack', and 'Medication'", nargs='+',)
        parser.add_argument("-s", "--symptoms", required=False, default=defaults["symptoms"],
                            help="list of symptoms to analyze",nargs='+',)
        parser.add_argument("-m", "--min_times_consumed", required=False, default=defaults["min_times_consumed"],
                            help="lower threshold of when to analyze a consumable, for example the data may not be useful for a food you've only eaten once", type=int)
        parser.add_argument("-w", "--symptom_warning_score", required=False, default=defaults["symptom_warning_score"],
                            help="the program will print out a warning once a consumable has an average symptom score that passes the given threshold", type=int)
        parser.add_argument("-soh", "--symptom_onset_hours", required=False, default=defaults["symptom_onset_hours"],
                            help="number of hours to look for symptoms after a consumable has been taken", type=int)
        args = parser.parse_args()
        self._is_valid_file(parser, args.input_file)
        return args

    def _is_valid_file(self, parser: object, file_name: str) -> None:
        """ensure that the input_file exists."""
        if not os.path.exists(file_name):
            parser.error("the file '{}' does not exist!".format(file_name))
            sys.exit(1)

class MySymptomsCSV:
    """
    Represents information from a my symptoms CSV. The csv file is converted into a dictionary of consumables and of symptoms.
    Each symptom that occurs within the symptom_onset_hours after a consumable will be added to that consumable's symptom list.
    """
    def __init__(self, include_symptoms: list, symptom_onset_hours: timedelta, consumables: list):
        '''
        Get settings from config object and initialize dicts.
        If include_symptoms is empty, then all symptoms will be included in the analysis.
        '''
        self.include_symptoms = include_symptoms
        self.symptom_onset_hours = symptom_onset_hours
        self.valid_consumables = consumables
        self.consumables = {} # name : consumable objext
        self.symptoms = {} # name : symptom object

    def import_file(self, input_file: str) -> None:
        """
        Opens the given csv file and converts the data into a list of consumables and a list of symptoms.
        """
        with open(input_file) as csvfile:
            filereader = csv.reader(csvfile)
            next(filereader)  # skip header

            for row in filereader:
                datetime = convert_to_date_time(
                    row[DATE_COLUMN], row[TIME_COLUMN])
                category = clean_data(row[CATEGORIZATION_COLUMN])

                if category in config.consumables:
                    self._update_consumables(row, datetime)

                if category == "Symptom":
                    self._update_symptoms(row, datetime)

    def _update_consumables(self, row: list, datetime: datetime) -> None:
        """
        Updates or creates a new object for each consumable from a single entry of consumables.
        CSV row example - 03/30/2022, 18:57, Dinner, "Sushi, Cucumber Rolls", "Seaweed", "Cucumber", "White rice"
        """
        # each column after the categorization column will be a consumable or a specified amount of a consumable (the amounts will be ignored)
        for i in range(CATEGORIZATION_COLUMN + 1, len(row)):
            item = clean_data(row[i])
            if ignore_item(item):
                continue

            if item in self.consumables:
                consumable = self.consumables[item]
                consumable.update_last_consumed(datetime)
            else:
                self.consumables[item] = Consumable(item, datetime)


    def _update_symptoms(self, row: list, datetime: datetime) -> None:
        """
        Updates or creates a new object for each symptom from a single entry of symptoms.
        Connects an occurence of a symptom to a consumable if the symptom occurred within the 
        symptom_onset_hours.
        """
        for consumable in self.consumables.values():
            if not (datetime - consumable.last_consumed) < self.symptom_onset_hours:
                continue

            # each symptom row is in the format [symptom, intensity, symptom, intensity, ...]
            for i in range(CATEGORIZATION_COLUMN + 1, len(row), 2):
                symptom_name = clean_data(row[i])

                # ignore duration values and only analyze specified symptoms
                if symptom_name.startswith("Duration") or (self.include_symptoms and symptom_name not in self.include_symptoms):
                    continue

                symptom_intensity = int(row[i + 1].replace(" Intensity: ", ""))

                if symptom_name in self.symptoms:
                    symptom = self.symptoms[symptom_name]
                else:
                    symptom = Symptom(symptom_name)
                    self.symptoms[symptom_name] = symptom
                occurence = SymptomOccurence(symptom, datetime, symptom_intensity)
                consumable.add_symptom_occurence(occurence)


def clean_data(data: str) -> str:
    """removes unnecessary characters from a cell"""
    return data.strip(" ").replace('"', "")


def convert_to_date_time(date: str, time: str) -> object:
    """ converts date and time strings into one datetime object """
    datetime_string = clean_data(date + time)
    datetime_obj = datetime.strptime(datetime_string, "%m/%d/%Y %H:%M")
    return datetime_obj


def ignore_item(item: str) -> bool:
    """Ignores data unused in the current calculations"""
    return item.startswith("[")


class Symptom:
    """
    Currently only stores the symptom name
    """
    def __init__(self, name: str) -> None:
        self.name = name


class SymptomOccurence:
    """
    A single entry of a symptom and its intensity. Tagged with the date so we can correlate this occurence with the ingestion of a consumable.
    """
    def __init__(self, symptom: Symptom, date: datetime, intensity: int) -> None:
        self.symptom = symptom
        self.date = date
        self.intensity = intensity


class Consumable:
    """
    Has a list of symptoms
    """

    def __init__(self, name: str, last_consumed: datetime) -> None:
        self.name = name
        self.last_consumed = last_consumed
        self.times_consumed = 1
        self.symptom_occurrences = []
        self.associated_symptoms = set()

    def update_last_consumed(self, date: datetime):
        self.last_consumed = date
        self.times_consumed += 1

    def add_symptom_occurence(self, occurence: SymptomOccurence) -> None:
        self.associated_symptoms.add(occurence.symptom)
        self.symptom_occurrences.append(occurence)

    def total_danger_score(self) -> float:
        """ calculates the average intensity of a symptom (1-10) after the given item has been consumed.
        Gives a warning for concerning symptoms.
        """
        # calculate symptom score for consumable
        total_symptom_intensity = sum([symptom.intensity for symptom in self.symptom_occurrences])

        average_symptom_intensity = total_symptom_intensity / \
            self.times_consumed if total_symptom_intensity else 0
        return round(average_symptom_intensity, 2)

    def average_symptom_intensities(self, warning_threshold: int) -> dict:
        """ calculates the average intensity of a symptom (1-10) after the given item has been consumed.
        Gives a warning for concerning symptoms.
        """
        symptom_scores = {}
        for symptom in self.associated_symptoms:
            symptom_score = sum([occurence.intensity for occurence in self.symptom_occurrences if occurence.symptom == symptom])
            if symptom_score:
                average_symptom_score = round(symptom_score/self.times_consumed, 2) if symptom_score else 0
            else: 
                average_symptom_score = 0
            symptom_scores[symptom.name] = average_symptom_score
            if average_symptom_score > warning_threshold:
                print("warning!", self.name, symptom.name, average_symptom_score)
        return symptom_scores



def calculate_safest_consumables(consumables: list, min_times_consumed: int, warning_threshold: int) -> dict:
    """
    Calculates an overall danger score and the average expected symptom intensity for each symptom in relation to each consumable.
    """
    symptom_scores = []
    for consumable in consumables:
        times_consumed = consumable.times_consumed
        if times_consumed < min_times_consumed:
            continue
        entry = {"item": consumable.name, "danger_score": consumable.total_danger_score(), "symptoms":  consumable.average_symptom_intensities(warning_threshold)}
        symptom_scores.append(entry)

    # sort from least to most dangerous consumables
    sorted_by_danger = sorted(symptom_scores, key= lambda x: x["danger_score"])
    return sorted_by_danger

def save_to_file(data: object, output_file: str):
    """creates a file and writes the given json data into it"""
    with open(output_file, "w") as json_file:
        json.dump(data, json_file, indent=4, default=vars)

if __name__ == "__main__":
    config = Config()
    csv_data = MySymptomsCSV(config.symptoms, config.symptom_onset_hours, config.consumables)
    csv_data.import_file(config.input_file)
    safe_foods = calculate_safest_consumables(csv_data.consumables.values(), config.min_times_consumed, config.symptom_warning_score)
    save_to_file(safe_foods, config.output_file)