#!/usr/bin/python2 -u
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import sys
import pexpect
import colorama
import re


def print_call_stack_info(call_stack, symbol_file, remove_from_path, tool):
    # Print the call stack associated with this heap trace
    for address in call_stack:
        if address != "0x40000000":
            if tool == "addr2line":
                addr2line = pexpect.spawn("xtensa-esp32-elf-addr2line -pfiaC -e " + symbol_file +
                                          " " + address)
                addr2line.logfile = None
                match = addr2line.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=2)
                if match == 0:
                    print(addr2line.before.strip().replace(remove_from_path, ""))
            elif tool == "gdb":
                gdb = pexpect.spawn("xtensa-esp32-elf-gdb --batch " + symbol_file +
                                    " -ex \"set listsize 1\" -ex \"l *" + address + "\"")
                gdb.logfile = None
                match = gdb.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=2)
                if match == 0:
                    output_filtered = gdb.before.strip().replace(remove_from_path, "")
                    components_normal = re.match(
                        r".*(?P<address>0x[0-9a-z]+) is in (?P<function>.*) \((?P<file>.*):(?P<line>[0-9]+)\)\.\s*?\n[0-9]+\s+(?P<code>(\s*\S*)*)",
                        output_filtered)
                    components_assembly = re.match(
                        r".*(?P<address>0x[0-9a-z]+) is at (?P<file>.*):(?P<line>[0-9]+)\.\s*?\n[0-9]+\s+(?P<code>(\s*\S*)*)",
                        output_filtered)

                    if components_normal is not None:
                        print(colorama.Style.RESET_ALL + colorama.Fore.RED +
                              components_normal.group('address') + colorama.Style.RESET_ALL +
                              " : " + colorama.Fore.GREEN + components_normal.group('function') +
                              colorama.Style.RESET_ALL + " in " + colorama.Fore.BLUE +
                              components_normal.group('file') + ":" + colorama.Style.BRIGHT +
                              components_normal.group('line'))
                    elif components_assembly is not None:
                        print(colorama.Style.RESET_ALL + colorama.Fore.RED +
                              components_assembly.group('address') + colorama.Style.RESET_ALL +
                              " : " + colorama.Fore.BLUE + components_assembly.group('file') + ":" +
                              colorama.Style.BRIGHT + components_assembly.group('line'))
                    else:
                        print(gdb.before.strip().replace(remove_from_path, ""))
                else:
                    print("xtensa-esp32-elf-gdb --batch " + symbol_file +
                          " -ex \"set listsize 1\" -ex \"l *" + address + "\"")
        else:
            print("0x40000000: top of call stack reached")

    print("")


def print_core_dump_info(symbol_file, path_core_dump_tool, core_dump):
    decoder = pexpect.spawn(path_core_dump_tool + " info_corefile --core-format b64 --core " +
                            core_dump + " " + symbol_file)
    decoder.logfile = None
    match = decoder.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=2)
    if match == 0:
        print(decoder.before.strip())


if __name__ == "__main__":
    colorama.init()

    # Define an argument parser and parse the arguments
    parser = argparse.ArgumentParser("Decode the backtrace given as argument")
    parser.add_argument(
        "--symbol_file",
        help=
        "Path to the symbol file corresponding to the executable that has been executed to produce the heap tracing",
        type=open)
    parser.add_argument(
        "--backtrace", help="Backtrace printed by the ESP32", type=argparse.FileType('r'))
    parser.add_argument(
        "--remove_from_path",
        help="Remove a string from the paths displayed for a more concise display",
        default="")
    parser.add_argument(
        "--tool",
        help="Specify the tool to use for address decoding",
        choices=['addr2line', 'gdb'],
        default='gdb')
    parser.add_argument(
        "--core_dump",
        help=
        "Core dump printed by the ESP32, corresponding to everything between the \"CORE DUMP START\" and \"CORE DUMP END\" lines",
        type=argparse.FileType('r'))
    parser.add_argument(
        "--path_core_dump_tool",
        help="Path to the \"espcoredump.py\" tool. Usually in esp-idf/components/espcoredump/ ",
        type=argparse.FileType('r'))

    args = parser.parse_args()

    # Backtrace decoding
    if args.backtrace is not None and args.symbol_file is not None:
        symbol_file = args.symbol_file.name
        backtrace = args.backtrace.readline().split(" ")

        if backtrace[0] != "Backtrace:":
            print(
                "Incorrect format detected, expected to receive a string beginning with \"Backtrace: \""
            )
            sys.exit(-1)

        backtrace = [address[0:address.find(":")] for address in reversed(backtrace[1:])]
        print_call_stack_info(backtrace, symbol_file, args.remove_from_path, args.tool)

    # Core dump decoding
    if args.core_dump is not None and args.path_core_dump_tool is not None:
        symbol_file = args.symbol_file.name
        path_core_dump_tool = args.path_core_dump_tool.name
        core_dump = args.core_dump.name

        print_core_dump_info(symbol_file, path_core_dump_tool, core_dump)
