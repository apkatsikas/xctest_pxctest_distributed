import subprocess
import glob
import os
from subprocess import Popen
import math
import time

import json

with open('ios_tests.json') as f:
    IOS_TESTS_DICT = json.load(f)

COMMANDS_ETC = IOS_TESTS_DICT['commands_etc']
DIRECTORY = IOS_TESTS_DICT['directory']
SIM_DIRECTORY = IOS_TESTS_DICT['simulator_dir']
REPO_DIRECTORY = DIRECTORY + COMMANDS_ETC['project_string']
NUMBER_OF_SIMULATORS = IOS_TESTS_DICT['number_of_simulators']
LIST_OF_LIST_OF_TESTS = []
TESTS_PER_SIMULATOR = 1
TESTS_DIR = IOS_TESTS_DICT['tests_dir']


def get_list_of_tests():
    list_of_tests = [os.path.basename(x) for x in glob.glob(REPO_DIRECTORY + '/' + TESTS_DIR + '/*Test.swift')]
    trimmed_list_of_tests = []
    for test in list_of_tests:
        trimmed_list_of_tests.append(test[:test.index('.swift')])
    return trimmed_list_of_tests


def build_list_of_lists():
    list_of_lists = []
    tests = get_list_of_tests()
    number_of_tests = len(tests)
    tests_to_add = number_of_tests
    TESTS_PER_SIMULATOR = math.floor(number_of_tests / int(NUMBER_OF_SIMULATORS))
    while tests_to_add >= 1:
        temp_list = []
        for num in range(1, int(TESTS_PER_SIMULATOR) + 1):
            if tests_to_add > 0:
                temp_list.append(tests[tests_to_add - 1])
                tests_to_add -= 1
        list_of_lists.append(temp_list)
    return list_of_lists


def get_comma_separated_string(list_of_string):
    return ','.join(list_of_string)


def call_subprocess(command, cwd=REPO_DIRECTORY):
    print('calling process in directory - ' + cwd + ' - ' + command)
    subprocess.check_call(command, cwd=cwd, shell=True)


def create_simulator_directory(sim_num):
    os.makedirs(REPO_DIRECTORY + '/' + SIM_DIRECTORY + '/' + sim_num)


def build_simulator(sim_num):
    call_subprocess(COMMANDS_ETC['build_simulators'] % (REPO_DIRECTORY + '/' + SIM_DIRECTORY + '/' + sim_num))


def iterate_over_simulators(passed_func):
    for num in range(1, int(NUMBER_OF_SIMULATORS) + 1):
        passed_func(str(num))


def create_directories():
    iterate_over_simulators(create_simulator_directory)


def build_simulators():
    iterate_over_simulators(build_simulator)


def run_tests(commands_param):
    print('running processes in ' + REPO_DIRECTORY + '- ')
    for cmd in commands_param:
        print(cmd)
    processes = [Popen(cmd, cwd=REPO_DIRECTORY, shell=True) for cmd in commands_param]
    for p in processes:
        p.wait()


def build_test_commands():
    commands_inner = []
    for num in range(1, int(NUMBER_OF_SIMULATORS) + 1):
        # if its the final simulator
        if num == int(NUMBER_OF_SIMULATORS):
            # if there is more than 1 list left
            if num != len(LIST_OF_LIST_OF_TESTS):
                # add the rest of the tests
                commands_inner.append(build_test_command(str(num), get_comma_separated_string(
                    LIST_OF_LIST_OF_TESTS[num - 1]) + ',' + get_comma_separated_string(LIST_OF_LIST_OF_TESTS[num])))
                return commands_inner
        commands_inner.append(build_test_command(str(num), get_comma_separated_string(LIST_OF_LIST_OF_TESTS[num - 1])))
    return commands_inner


def build_test_command(sim_num, string_of_tests):
    return COMMANDS_ETC['run_test'] % (
        REPO_DIRECTORY + '/' + SIM_DIRECTORY + '/' + sim_num, REPO_DIRECTORY + '/' + SIM_DIRECTORY + '/' + sim_num,
        REPO_DIRECTORY, ':' + string_of_tests)


# execute commands
try:
    start_time = time.time()
    call_subprocess(COMMANDS_ETC['clone_statement'], cwd=DIRECTORY)
    call_subprocess(COMMANDS_ETC['checkout_branch'])
    call_subprocess(COMMANDS_ETC['pod_install'])
    call_subprocess(COMMANDS_ETC['xcode_build'] % REPO_DIRECTORY)
    LIST_OF_LIST_OF_TESTS = build_list_of_lists()
    create_directories()
    commands = build_test_commands()
    build_simulators()
    run_tests(commands)
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    print('done. took ' + str(total_time) + ' minutes')
except subprocess.CalledProcessError as e:
    print('Test exited with non-zero code:', e)
