#!/usr/bin/python2 -u
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import re
import sys
import pexpect


class terminal_colors:
    CEND = '\33[0m'
    CBOLD = '\33[1m'
    CITALIC = '\33[3m'
    CURL = '\33[4m'
    CBLINK = '\33[5m'
    CBLINK2 = '\33[6m'
    CSELECTED = '\33[7m'
    CBLACK = '\33[30m'
    CRED = '\33[31m'
    CGREEN = '\33[32m'
    CYELLOW = '\33[33m'
    CBLUE = '\33[34m'
    CVIOLET = '\33[35m'
    CBEIGE = '\33[36m'
    CWHITE = '\33[37m'
    CBLACKBG = '\33[40m'
    CREDBG = '\33[41m'
    CGREENBG = '\33[42m'
    CYELLOWBG = '\33[43m'
    CBLUEBG = '\33[44m'
    CVIOLETBG = '\33[45m'
    CBEIGEBG = '\33[46m'
    CWHITEBG = '\33[47m'
    CGREY = '\33[90m'
    CRED2 = '\33[91m'
    CGREEN2 = '\33[92m'
    CYELLOW2 = '\33[93m'
    CBLUE2 = '\33[94m'
    CVIOLET2 = '\33[95m'
    CBEIGE2 = '\33[96m'
    CWHITE2 = '\33[97m'
    CGREYBG = '\33[100m'
    CREDBG2 = '\33[101m'
    CGREENBG2 = '\33[102m'
    CYELLOWBG2 = '\33[103m'
    CBLUEBG2 = '\33[104m'
    CVIOLETBG2 = '\33[105m'
    CBEIGEBG2 = '\33[106m'
    CWHITEBG2 = '\33[107m'


# Function to print a log line with the color corresponding to its log level
def print_log_line(line):
    if len(line) > 0:
        pattern_debug_level = re.compile("(?P<level>[A-Z]) \([0-9]+\)")
        match = pattern_debug_level.match(line)
        if match:
            if match.group("level") == "E":
                print(terminal_colors.CRED + line + terminal_colors.CEND)
            elif match.group("level") == "W":
                print(terminal_colors.CYELLOW + line + terminal_colors.CEND)
            elif match.group("level") == "I":
                print(terminal_colors.CBLUE + line + terminal_colors.CEND)
            elif match.group("level") == "D":
                print(terminal_colors.CVIOLET + line + terminal_colors.CEND)
            elif match.group("level") == "V":
                print(terminal_colors.CVIOLET2 + line + terminal_colors.CEND)
        else:
            print(line)


def print_call_stack_info(call_stack, symbol_file, remove_from_path):
    # Print the call stack associated with this heap trace
    for address in call_stack:
        if address != "0x40000000":
            addr2line = pexpect.spawn("xtensa-esp32-elf-addr2line -pfiaC -e " + symbol_file + " " +
                                      address)
            addr2line.logfile = None
            match = addr2line.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=2)
            if match == 0:
                print(terminal_colors.CYELLOW +
                      addr2line.before.strip().replace(remove_from_path, "") + terminal_colors.CEND)
        else:
            print(terminal_colors.CYELLOW + "0x40000000: " + terminal_colors.CEND)

    print("")


def heap_trace_in_list(heap_trace_search, heap_traces):
    for index, heap_trace in enumerate(heap_traces):
        if heap_trace == heap_trace_search:
            return index

    return -1


if __name__ == "__main__":
    # Define an argument parser and parse the arguments
    parser = argparse.ArgumentParser("Decode the heap tracing output saved in a file")
    parser.add_argument(
        "input_file", help="Path to the file containing the output of the heap tracing", type=open)
    parser.add_argument(
        "symbol_file",
        help=
        "Path to the symbol file corresponding to the executable that has been executed to produce the heap tracing",
        type=open)
    parser.add_argument(
        "--min_allocation_bytes",
        help=
        "Keep heap traces only for allocations greater than number specified (default 0, all traces kept)",
        type=int,
        default=0)
    parser.add_argument(
        "--remove_from_path",
        help="Remove a string from the paths displayed for a more concise display",
        default="")
    args = parser.parse_args()

    if args.input_file is not None and args.symbol_file is not None:
        symbol_file = args.symbol_file.name
        lines = args.input_file.readlines()

        # Initialize what to search for
        pattern_start = re.compile("[0-9]+ allocations trace \([0-9]+ entry buffer\)")
        pattern_end = re.compile("total allocations [0-9]+ total frees [0-9]+")
        pattern_heap_trace = re.compile(
            "(?P<nb_bytes>[0-9]+) bytes \(@ (?P<memory_location>[0-9a-z]+)\) allocated CPU [0-9]+ ccount (?P<cpu_count>[0-9a-z]+) caller (?P<call_stack>[0-9a-z:]+)"
        )
        start_block_detected = False
        heap_traces = []

        # Iterate through the lines
        for line in lines:
            line = line.strip()
            match_start_block = pattern_start.match(line)
            match_end_block = pattern_end.match(line)
            match_heap_trace = pattern_heap_trace.match(line)

            # Beginning of new block
            if start_block_detected is False and match_start_block is not None:
                start_block_detected = True
            # End of heap trace block
            elif start_block_detected is True and match_end_block is not None:
                start_block_detected = False
            # Inside a heap trace block on a heap trace line
            elif start_block_detected is True and match_end_block is None and match_heap_trace is not None:
                heap_trace = {
                    "nb_bytes": match_heap_trace.group("nb_bytes"),
                    "memory_location": match_heap_trace.group("memory_location"),
                    "cpu_count": match_heap_trace.group("cpu_count"),
                    "call_stack": match_heap_trace.group("call_stack").strip(":").split(":")
                }

                index_in_list = heap_trace_in_list(heap_trace, heap_traces)
                if heap_trace["nb_bytes"] > args.min_allocation_bytes and index_in_list < 0:
                    heap_traces.append(heap_trace)
                    print(terminal_colors.CRED + line + terminal_colors.CEND)
                    print_call_stack_info(heap_trace["call_stack"], symbol_file,
                                          args.remove_from_path)

            elif start_block_detected is False and match_start_block is None:
                print_log_line(line)
