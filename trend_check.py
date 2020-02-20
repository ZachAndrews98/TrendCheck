""" Tool for determining what devices on AC Network are not in compliance """
# Written by Zachary Andrews Allegheny College Class 2020

from getpass import getpass
import os
import datetime
import pysftp

CSV_FILE = "./data/resnetWired.csv"
LEASE_FILE = "./data/dhcpd.leases.120220191150"
REG_FILE = "./data/dhcpd.conf.012920201723"

SERVER = 'resnetregdev.allegheny.edu'
LEASE_PATH = "/var/lib/dhcpd/dhcpd.leases"
REG_PATH = "/etc/dhcp/"

TEST_START = None
TEST_END = None

DEVICES = list()
REMOVE = list()
LEASES = {}


def run():
    """ Main function to determine device compliance """
    set_time()
    parse_csv()
    print("There are " + str(len(DEVICES)) +
          " devices that do not have Trend Installed")
    # getFiles()
    parse_lease_file()
    # pairs up leases with devices, if there is no associated lease, remove #
    # the device #
    for device in DEVICES:
        if device['IP'] in LEASES:
            device['LEASE'] = LEASES[device['IP']]
        else:
            REMOVE.append(device)
    remove_devices()
    print("There are " + str(len(DEVICES)) + " corresponding leases")
    # checks each device's lease time to determine if it is valid #
    for device in DEVICES:
        if check_time(device['LEASE']['starts'], device['LEASE']['ends']):
            REMOVE.append(device)
    remove_devices()
    # Check device mac against reg file, remove devices that don't have a
    # match #
    for device in DEVICES:
        device['USER'], device['PLATFORM'] = parse_reg_file(
            device['LEASE']['MAC'])
        if device['USER'] is None:
            REMOVE.append(device)
    remove_devices()
    check_platforms()
    remove_devices()
    print("Matched " + str(len(DEVICES)) + " devices with users")
    output()


def set_time():
    """ Set the start and end times and dates for the test """
    # pylint: disable=W0603
    global TEST_START
    # pylint: disable=W0603
    global TEST_END
    start_date = str(
        input("Enter the start date of the test (y/m/d): ")).split('/')
    end_date = str(
        input("Enter the end date of the test (if different than start): ")
        ).split('/')
    start_time = str(
        input("Enter the start time of the test (24 hr:min): ")).split(':')
    end_time = str(
        input("Enter the end time of the test (24 hr:min): ")).split(':')
    if end_date == [""]:
        end_date = start_date
    err = 0
    if len(start_date) < 3:
        print("\nERROR: Start date must be in y/m/d format")
        err = err + 1
    if len(end_date) < 3:
        print("\nERROR: End date must be in y/m/d format")
        err = err + 1
    if len(start_time) < 2:
        print("\nERROR: Start time must be in 24hr:minute format")
        err = err + 1
    if len(end_time) < 2:
        print("\nERROR: End time must be in 24hr:minute format")
        err = err + 1
    if err == 0:
        TEST_START = datetime.datetime(
            int(start_date[0]), int(start_date[1]), int(start_date[2]),
            hour=int(start_time[0]), minute=int(start_time[1])
        )
        TEST_END = datetime.datetime(
            int(end_date[0]), int(end_date[1]), int(end_date[2]),
            hour=int(end_time[0]), minute=int(end_time[1])
        )
    else:
        print()
        set_time()


def parse_csv():
    """ Parses CSV_FILE and stores each device """
    csv_file = open(CSV_FILE, "r")
    for line in csv_file:
        items = line.split(',')
        device = {
            "IP": items[0],
            "STATUS": items[4],
            "RESULT": items[5].replace("\"", "").strip(),
            "PRODUCT": items[6],
            "PLATFORM": items[7],
            'LEASE': {},
            'USER': ""
        }
        if device['STATUS'] == "Not installed":
            DEVICES.append(device)


def get_files():
    """ Downloads LEASE and REG files from server using sftp """
    srvr = pysftp.Connection(
        SERVER, username=str(input("User: ")), password=getpass()
    )
    srvr.get(LEASE_PATH)
    os.replace('./dhcpd.leases', './data/dhcpd.leases')
    srvr.get(REG_PATH)
    os.replace('./tempname.txt', './data/tempname.txt')

    with open('./data/dhcpd.leases', 'r') as file:
        lines = file.readlines()
    with open('./data/dhcpd.leases', 'w') as file:
        for line in lines[2:]:
            if "server-duid" not in line:
                file.write(line)


def parse_lease_file():
    """ Parses LEASE file and breaks each lease up into a dictionary """
    leases = open(LEASE_FILE, "r")
    leases = leases.read().strip().split('}\n')
    for lease in leases:
        items = lease.split('\n')
        ip_address = items[0].strip().split(' ')[1]
        if "141.195" in ip_address:
            pass
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
        if items[6].strip().split(' ')[2] != "state":
            mac = items[6].strip().split(' ')[2].replace(';', '')
        elif items[7].strip().split(' ')[2] != "state":
            mac = items[7].strip().split(' ')[2].replace(';', '')
        elif items[8].strip().split(' ')[2] != "state":
            mac = items[8].strip().split(' ')[2].replace(';', '')
        LEASES[ip_address] = {
            'starts': datetime.datetime.combine(start_date, start_time),
            'ends': datetime.datetime.combine(end_date, end_time),
            'MAC': mac,
        }


def check_time(start, end):
    """ Checks to see if a lease's time is valid """
    if TEST_START <= start and end >= TEST_END:
        return True
    return False


def remove_devices():
    """ Removes devices that are deamed to be in compliance """
    for device in REMOVE:
        DEVICES.remove(device)
    REMOVE.clear()


def parse_reg_file(mac):
    """ Parses REG file and matches MAC to User """
    user = None
    platform = "NA"
    regs = open(REG_FILE, 'r')
    for reg in regs:
        if "host" not in reg:
            pass
        else:
            info = reg.split('#')
            if mac == info[0].split(' ')[5]:
                user = info[0].split(' ')[1]
                platform = info[8]
            else:
                pass
    return user, platform


def check_platforms():
    """ Checks the platform of devices and removes ones that are approved """
    for device in DEVICES:
        platform = device['PLATFORM']
        if 'Laptop' in platform or 'Desktop' in platform:
            pass
        else:
            REMOVE.append(device)


def print_devices():
    """ Prints out all unremoved devices that have been detected """
    for device in DEVICES:
        print("IP: " + device['IP'])
        print("Status: " + device['STATUS'])
        print("Result: " + device['RESULT'])
        print("Platform: " + device['PLATFORM'])
        for key, value in device['LEASE'].items():
            print(key + ": " + str(value))
        print("User: " + device['USER'])
        print()


def output():
    """ Creates an output file with the final list of non-compliant devices """
    filename = "./output/output_" + \
        str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            ).replace(" ", "_") + ".txt"
    with open(filename, "w") as file:
        file.write(
            "Test Run: " +
            str(TEST_START) +
            " to " +
            str(TEST_END) +
            "\n\n")
        for device in DEVICES:
            file.write("User: " + device['USER'] + "\n")
            file.write("IP: " + device['IP'] + "\n" +
                       # "Status: " + device['STATUS'] + "\n" +
                       # "Result: " + device['RESULT'] + "\n" +
                       "Platform: " + device['PLATFORM'] + "\n")
            for key, value in device['LEASE'].items():
                file.write(key + ": " + str(value) + "\n")
            file.write("\n")
    file.close()
    print("Generated output file:", filename)


if __name__ == "__main__":
    run()

# parse_reg_file()
