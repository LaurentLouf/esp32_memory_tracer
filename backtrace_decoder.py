#!/usr/bin/python2 -u
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import sys
import pexpect


def print_call_stack_info(call_stack, symbol_file, remove_from_path):
    # Print the call stack associated with this heap trace
    for address in call_stack:
        if address != "0x40000000":
            addr2line = pexpect.spawn("xtensa-esp32-elf-addr2line -pfiaC -e " + symbol_file + " " +
                                      address)
            addr2line.logfile = None
            match = addr2line.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=2)
            if match == 0:
                print(addr2line.before.strip().replace(remove_from_path, ""))
        else:
            print("0x40000000: top of call stack reached")

    print("")


if __name__ == "__main__":
    # Define an argument parser and parse the arguments
    parser = argparse.ArgumentParser("Decode the backtrace given as argument")
    parser.add_argument(
        "symbol_file",
        help=
        "Path to the symbol file corresponding to the executable that has been executed to produce the heap tracing",
        type=open)
    parser.add_argument("backtrace", help="Backtrace printed by the ESP32", nargs='*')
    parser.add_argument(
        "--remove_from_path",
        help="Remove a string from the paths displayed for a more concise display",
        default="")
    args = parser.parse_args()

    if args.backtrace is not None and args.symbol_file is not None:
        symbol_file = args.symbol_file.name
        if args.backtrace[0] != "Backtrace:":
            print(
                "Incorrect format detected, expected to receive a string beginning with \"Backtrace: \""
            )
            sys.exit(-1)

        backtrace = [address[0:address.find(":")] for address in reversed(args.backtrace[1:])]
        print_call_stack_info(backtrace, symbol_file, args.remove_from_path)
