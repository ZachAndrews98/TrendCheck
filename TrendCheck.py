# Written by Zachary Andrews Allegheny College Class 2020

from getpass import getpass
import os
import re
import datetime

CSV_FILE = "./data/resnetWired.csv"
LEASE_FILE = "./data/dhcpd.leases"
SERVER = 'resnetregdev.allegheny.edu'
LEASE_PATH = "/var/lib/dhcpd/dhcpd.leases"

DEVICES = list()
LEASES = {}


def run():
    readCSV()
    print("There are " + str(len(DEVICES)) + " devices that do not have Trend Installed")
    # for device in DEVICES:
    #     print(device)
    # getLeaseFile()
    parseLeaseFile()
    print(len(LEASES))
    for key, value in LEASES.items():
        print(key)
        for key2, value2 in LEASES[key].items():
            print(key2 + ": " + str(LEASES[key][key2]))
        print()


def readCSV():
    csv_file = open(CSV_FILE, "r")
    for line in csv_file:
        items = line.split(',')
        device = {
            "IP": items[0],
            "MAC": "",
            "STATUS": items[4],
            "RESULT": items[5].replace("\"","").strip(),
            "PRODUCT": items[6],
            "PLATFORM": items[7],
        }
        if device['STATUS'] == "Not installed":
            DEVICES.append(device)


def getLeaseFile():
    import pysftp

    srvr = pysftp.Connection(
        SERVER, username=str(input("User: ")), password=getpass()
    )
    srvr.get(LEASE_PATH)
    os.replace('./dhcpd.leases', './data/dhcpd.leases')

    with open('./data/dhcpd.leases', 'r') as f:
        lines = f.readlines()
    with open('./data/dhcpd.leases', 'w') as f:
        for line in lines[2:]:
            if not "server-duid" in line:
                f.write(line)


def parseLeaseFile():
    leases = open(LEASE_FILE, "r")
    leases = leases.read().strip().split('}\n')
    for lease in leases:
        items = lease.split('\n')
        ip = items[0].split(' ')[1]
        start_date = datetime.date(
            int(items[1].strip().split(' ')[2].split('/')[0]),
            int(items[1].strip().split(' ')[2].split('/')[1]),
            int(items[1].strip().split(' ')[2].split('/')[2])
        )
        start_time = datetime.time(
            int(items[1].strip().split(' ')[3].split(':')[0]),
            int(items[1].strip().split(' ')[3].split(':')[0])
        )
        end_date = datetime.date(
            int(items[2].strip().split(' ')[2].split('/')[0]),
            int(items[2].strip().split(' ')[2].split('/')[1]),
            int(items[2].strip().split(' ')[2].split('/')[2])
        )
        end_time = datetime.time(
            int(items[2].strip().split(' ')[3].split(':')[0]),
            int(items[2].strip().split(' ')[3].split(':')[0])
        )
        mac = items[6].strip().split(' ')[2]
        LEASES[ip] = {
            'starts': datetime.datetime.combine(start_date, start_time),
            'ends': datetime.datetime.combine(end_date, end_time),
            'MAC': mac,
            'user': ''
        }


if __name__ == "__main__":
    run()