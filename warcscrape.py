#! /usr/bin/env python3
import os
import re
import argparse
import warc
import sys
import mimetypes
from urllib.parse import urlparse, unquote
from pprint import pprint
import shutil

counts = {}

class filterObject:
    """Basic object for storing filters."""
    def __init__(self, string):
        self.result = True
        if string[0] == "!":
            self.result = False
            string = string[1:]

        _list = string.lower().split(":")

        self.http = (_list[0] == 'http')
        if self.http:
            del _list[0]

        self.k = _list[0]
        self.v = _list[1]

def inc(obj, header=False, dic=False):
    """Short script for counting entries."""
    if header:
        try:
            obj = obj[header]
        except KeyError:
            obj = None

    holder = counts
    if dic:
        if dic not in counts:
            counts[dic] = {}
        holder = counts[dic]

    if obj in holder:
        holder[obj] += 1
    else:
        holder[obj] = 1

def warc_records(string, path):
    """Iterates over warc records in path."""
    for filename in os.listdir(path):
        if re.search(string, filename) and ".warc" in filename:
            print("parsing", filename)
            with warc.open(path + filename) as warc_file:
                for record in warc_file:
                    yield record

def checkFilter(filters, record):
    """Check record against filters."""
    for i in filters:
        if i.http:
            if not record.http:
                return False
            value = record.http
        else:
            value = record.header

        string = value.get(i.k, None)
        if not string or (i.v in string) != i.result:
            return False
    return True

def parse(args):
    #Clear output warc file.
    if args.dump == "warc":
        print("Recording", args.dump, "to", args.output + ".")
        with open(args.output_path + args.output, "wb"):
            pass

    for record in warc_records(args.string, args.path):
        try:
            #Filter out unwanted entries.
            if not checkFilter(args.filter, record):
                continue

            #Increment Index counters.
            if args.silence:
                inc("records")
                inc(record,"warc-type", "types")
                inc(record, "content_type", "warc-content")
                if record.http:
                    inc(record.http, "content_type", "http-content")
                    inc(record.http, "error", "status")

            #Dump records to file.
            if args.dump == "warc":
                with open(args.output_path + args.output, "ab") as output:
                    record.write_to(output)

            if args.dump == "content":
                url = urlparse(unquote(record['WARC-Target-URI']))

                #Set up folder
                index = url.path.rfind("/") + 1
                file = url.path[index:]
                path = url.path[:index]

                #Process filename
                if "." not in file:
                    path += file
                    if not path.endswith("/"):
                        path += "/"

                    file = 'index.html'

                #Final fixes.
                path = path.replace(".", "-")
                host = url.hostname.replace('www.', '', 1)
                path = args.output_path + host + path

                #Create new directories
                if not os.path.exists(path):
                    try:
                        os.makedirs(path)
                    except OSError:
                        path = "/".join([i[:25] for i in path.split("/")])
                        os.makedirs(path)

                #Test if file has a proper extension.
                index = file.index(".")
                suffix = file[index:]
                content = record.http.get("content_type", "")
                slist = mimetypes.guess_all_extensions(content)
                if suffix not in slist:
                    #Correct suffix if we can.
                    suffix = mimetypes.guess_extension(content)
                    if suffix:
                        file = file[:index] + suffix
                    else:
                        inc(record.http, "content_type", "unknown mime type")

                #Check for gzip compression.
                if record.http.get("content-encoding", None) == "gzip":
                    file += ".gz"

                path += file

                #If Duplicate file then insert numbers
                index = path.rfind(".")
                temp = path
                n = 0
                while os.path.isfile(temp):
                    n +=1
                    temp = path[:index] + "("+ str(n) + ")" + path[index:]
                path = temp

                #Write file.
                with open(path, 'wb') as fp:
                    record.http.write_payload_to(fp)
        except:
            if args.error:
                print("Error in record. Recording to error.warc.")
                with open(args.output_path + "error.warc", "wb") as fp:
                    record.write_to(fp)
            else:
                raise

    #print results
    if args.silence:
        print("-----------------------------")
        for i in counts:
            print("\nCount of {}.".format(i))
            pprint(counts[i])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extracts attributes from warc files.')
    parser.add_argument("filter", nargs='*', help="Attributes to filter by. Entries that do not contain filtered elements are ignored. Example: warc-type:response, would ignore all warc entries that are not responses. Attributes in an HTTP object should be prefixed by 'http'. Example, http:error:200.")
    parser.add_argument("-silence", action="store_false", help="Silences output of warc data.")
    parser.add_argument("-error", action="store_true", help="Silences most errors and records problematic warc entries to error.warc.")
    parser.add_argument("-string", default="", help="Regular expression to limit parsed warc files. Defaults to empty string.")
    parser.add_argument("-path", default="./", help="Path to folder containing warc files. Defaults to current folder.")
    parser.add_argument("-output_path", default="data/", help="Path to folder to dump content files. Defaults to data/ folder.")
    parser.add_argument("-output", default="output.warc", help="File to output warc contents. Defaults to 'output.warc'.")
    parser.add_argument("-dump", choices=['warc', 'content'], type=str, help="Dumps all entries that survived filter. 'warc' creates a filtered warc file. 'content' tries to reproduce file structure of archived websites.")
    args = parser.parse_args()

    if args.path[-1] != "/":
        args.path += "/"

    if args.output_path[-1] != "/":
        args.output_path += "/"

    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)

    #Forced filters
    if args.dump == "content":
        args.filter.append("warc-type:response")
        args.filter.append("content-type:application/http")

    args.filter = [filterObject(i) for i in args.filter]

    args.string = re.compile(args.string)
    parse(args)
