#!/usr/bin/env python3

import os
import sys
import re
import argparse
import json

def parse_options(operations=[]):
    '''
    parse cli
    '''
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
                          '--directory',
                          type=str,
                          help='Folder with Terraform files - Gets checked recursively including subdirectories',
                          default='./terraform'
                          #required=True
                        )

    return parser.parse_args()

def Get_tf_files_in_dir(dir):

  regex_tf_file = re.compile('\S+\.tf')
  terraform_files = {}

  for r, d, f in os.walk(dir):
    for file in f:
      if regex_tf_file.match(file):
        x = os.path.join(r, file)
        terraform_files.update({x:'null'})

  return terraform_files


def Subtitute_tf_vars(line):

  i = -1
  stack = 0
  initial_dollar = 0
  tf_var = ''
  var_replacement = 'some-var-here'

  for char in line:
    i += 1
    if line[i - 1] != '\\' and stack > 0:
      if char == '{' and initial_dollar != (i - 1):
        stack += 1
      if char == '}':
        stack -= 1
        if stack == 0:
          tf_var = line[initial_dollar - 1:i + 1]

    if char == '{' and line[i - 1] == '$' and line[i - 2] != '\\' and stack == 0:
      initial_dollar = i
      stack = 1

    if tf_var != '':
      lin_len = len(line)
      line = line.replace(tf_var, var_replacement)
      line = line.replace('""', '"')
      i -= lin_len - len(line)
      tf_var = ''

  return line


def Get_definition_from_tf_files(terraform_files):

  regex_definition_start = re.compile('\s*\S+\s=\s<<DEFINITION')
  regex_definition_end = re.compile('DEFINITION')
  output = {}

  for key in terraform_files:
    with open(key) as file:
      capture_lines = False
      definition = ''
      set_of_definitions = set()
      for line in file:
        if capture_lines and 'DEFINITION' not in line:
          line = Subtitute_tf_vars(line)
          definition += line
        if not capture_lines and regex_definition_start.match(line):
          capture_lines = True
        if capture_lines and regex_definition_end.match(line):
          capture_lines = False
          set_of_definitions.add(definition)
          definition = ''

      if len(set_of_definitions) > 0:
        output.update({key:set_of_definitions})

  return output


def Validate_json(terraform_files):

  errors = {}

  for key in terraform_files:
    definitions = terraform_files.get(key)
    for definition in definitions:
      try:
        json.loads(definition)
      except ValueError as err:
        errors.update({key:err})

  return(errors)


def Print_status(errors):
  if len(errors) > 0:
    print('Invalid JSON found!\n')
    for tf_file in errors:
      print('In "%s" the following JSON error was found:\n===> %s\n' %
        (tf_file, str(errors.get(tf_file)))
      )

    return 1

  else:
    print('All JSONs seem to be valid - You are good to go!')
    return 0


def main():

  DIR = vars(parse_options()).get('directory')

  tf_files_dictionary = Get_tf_files_in_dir(DIR)

  task_definitions = Get_definition_from_tf_files(tf_files_dictionary)

  errors = Validate_json(task_definitions)

  exit_code = Print_status(errors)

  sys.exit(exit_code)

if __name__ == "__main__":
  main()