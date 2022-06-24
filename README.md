# MySymptoms Safe Foods


## Description
Python script that uses data from the MySymptoms app to find the safest foods for you to eat. Ideal for starting or restarting an elimination diet. As the app stands right now, the only analysis it provides is showing the most likely culprit for a given symptom. This list of culprits doesn't factor in intensity and only shows the top foods responsible.

Foods will be printed to an output file in order of safety. Safety is determined by the danger score, which is calculated by adding up all the associated symptom intensities. 

## Usage

Download "mysymptoms.csv"

    1. Open the MySymptoms app.
    2. Navigate to the "More" tab.
    3. Select "Diary Report" then "CSV".
    4. Send the CSV from your phone to the computer, wherever you are running this program.

Run mysymptoms.py on your csv file. Use -h for help. You can update config.json to configure the app and/or use command line arguments, which are all optional.

```
usage: mysymptoms.py [-h] [-i INPUT_FILE] [-o OUTPUT_FILE] [-c CONSUMABLES [CONSUMABLES ...]] [-s SYMPTOMS [SYMPTOMS ...]] [-m MIN_TIMES_CONSUMED] [-w SYMPTOM_WARNING_SCORE] [-soh SYMPTOM_ONSET_HOURS]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input_file INPUT_FILE
                        csv input file (with extension)
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        json output file (with extension)
  -c CONSUMABLES [CONSUMABLES ...], --consumables CONSUMABLES [CONSUMABLES ...]
                        list of consumables to analyze, for example, 'Breakfast', 'Snack', and 'Medication'
  -s SYMPTOMS [SYMPTOMS ...], --symptoms SYMPTOMS [SYMPTOMS ...]
                        list of symptoms to analyze
  -m MIN_TIMES_CONSUMED, --min_times_consumed MIN_TIMES_CONSUMED
                        lower threshold of when to analyze a consumable, for example the data may not be useful for a food you've only eaten once
  -w SYMPTOM_WARNING_SCORE, --symptom_warning_score SYMPTOM_WARNING_SCORE
                        the program will print out a warning once a consumable has an average symptom score that passes the given threshold
  -soh SYMPTOM_ONSET_HOURS, --symptom_onset_hours SYMPTOM_ONSET_HOURS
                        number of hours to look for symptoms after a consumable has been taken
```