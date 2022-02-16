#!/usr/local/bin/python3.8

import argparse
import json
import urllib.request as urlreq
from datetime import datetime, timedelta, timezone

ipHitron = "192.168.100.1"

modemPages = {
    "System Information":  "getSysInfo.asp",
    "DOCSIS Provisioning": "getCMInit.asp",
    "DOCSIS WAN":          [
        "getCmDocsisWAN.asp",
        "dsinfo.asp",
        "dsofdminfo.asp",
        "usinfo.asp",
        "usofdminfo.asp"
    ],
    "DOCSIS Event":        "status_log.asp",
    "LAN Port Status":     "getLinkStatus.asp"
}


def parse_args():
    parser = argparse.ArgumentParser()
    defaults = {
        "type":  str,
        "nargs": "?"
    }
    parser.add_argument(
            "-a", "--address", **defaults, default="192.168.100.1",
            help="IP address of Hitron modem (defaults to 192.168.100.1)"
    )
    parser.add_argument(
            "-of", "--output-format", **defaults, default="telegraf",
            choices=["telegraf", "syslog", "json"],
            help="Format for outputting modem data (defaults to \"telegraf\")"
    )
    parser.add_argument(
            "-ev", "--extra-values", action='append', nargs=2,
            help="Extra values to include with each metric in the format of "
    )
    defined_args, extra_args = parser.parse_known_args()
    return defined_args


def jsontotelegraf(json_string, **kwargs):
    o = list()
    if "output_format" in kwargs:
        del kwargs["output_format"]
    if "address" in kwargs:
        del kwargs["address"]
    for i in json_string:
        kwargs["portId"] = i.pop("portId")
        kwargs["channelId"] = i.pop("channelId")
        if "modtype" in i:
            i["modtype"] = '"{}"'.format(i["modtype"])
        if "scdmaMode" in i:
            i["scdmaMode"] = '"{}"'.format(i["scdmaMode"])
        o.append(
                ",".join(
                        ["modem"] + ["{}={}".format(j, k.split()[-1]) for j, k
                                     in
                                     kwargs.items()]
                ) + " " + ",".join(
                        ["{}={}".format(j, k.split()[-1])
                         for j, k in
                         i.items()]
                )
        )
    return o


def main():
    args = parse_args()
    if args.extra_values:
        args = dict(args._get_kwargs(), **{i: j for i, j in args.extra_values})
        del args['extra_values']
    else:
        del args.extra_values
        args = dict(args._get_kwargs())
    # Get timestamp
    t = datetime.now(tz=timezone(timedelta(hours=-4))).timestamp() * 1e9
    # Fetch upstream data
    upreq = urlreq.Request(
            "http://" + ipHitron + "/data/" + modemPages['DOCSIS WAN'][3]
    )
    upjson = json.loads(urlreq.urlopen(upreq).read().decode('utf-8'))
    # Fetch downstream data
    downreq = urlreq.Request(
            "http://" + ipHitron + "/data/" + modemPages['DOCSIS WAN'][1]
    )
    downjson = json.loads(urlreq.urlopen(downreq).read().decode('utf-8'))
    for metric in jsontotelegraf(upjson, **{**{"link": "up"}, **args}):
        print("{0} {1:.0f}".format(metric, t))
    for metric in jsontotelegraf(downjson, **{**{"link": "down"}, **args}):
        print("{0} {1:.0f}".format(metric, t))


if __name__ == '__main__':
    main()
