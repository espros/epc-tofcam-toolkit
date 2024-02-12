"""https://github.com/GIJack/python-generate_mac"""
import random
import string

_valid_char = "0123456789ABCDEF"
_valid_bcast_char = "02468ACE"
_valid_vendors = set()
_vid_table = {
    '36': 2,
    '32': 3,
    '28': 4,
    None: 6,
}


def _strip_comments(in_list):
    """Proccesses out comments using # as the comment character"""
    file_lines = []
    for line in in_list:
        line = line.strip()
        if not line.startswith("#") and line != "":
            file_lines.append(line.split("#")[0])
    return (file_lines)


def _read_vid_file(vid_file):
    """Reads a VID file and returns a list nested list of line contents
    Every line is [MAC,Vendor,Comment]"""
    out_lines = []
    try:
        in_file = open(vid_file, "r", encoding="utf8")
        file_lines = in_file.readlines()
        in_file.close()
    except FileNotFoundError:
        raise FileNotFoundError("Cannot read VID file " + vid_file)

    # Sanitize inputs
    file_lines = _strip_comments(file_lines)

    # Generate a list of lines which are split into a list, make a set of
    # vendors
    for line in file_lines:
        line = line.split('\t')
        try:
            vendor = line[1]
            _valid_vendors.add(vendor)
        except Exception:
            continue
        out_lines.append(line)

    return out_lines


def _get_processed_vid(in_line):
    """Returns a formated tupple with MAC info (prefix,bytes_needed,vendor,description)"""

    # Start with the items that don't need transforms
    vendor = in_line[1]
    try:
        description = in_line[2]
    except Exception:
        description = ""

    # prefix or raw VID bytes
    prefix = in_line[0].split('/')[0]
    suffix = ''
    # get the suffix. It is either going to be 36, 28 or none.
    try:
        suffix = in_line[0].split('/')[1]
    except Exception:
        suffix = None

    bytes_needed = _vid_table[suffix]

    # Generate the string returned
    out_vid = ''
    if suffix == None:
        out_vid = prefix
    else:
        # Cut down the trailing zeros so random data can be generated in that
        # space
        prefix_size = (12 - bytes_needed) // 2
        prefix = prefix.split(':')
        prefix = prefix[0:prefix_size]
        prefix = ":".join(prefix)
        out_vid = prefix

    return prefix, bytes_needed, vendor, description


def _gen_rand_bytes(bytes_needed):
    """Generate X amount of random bytes, seperated by a :"""
    out_bytes = []
    rand_byte = ""
    for i in range(bytes_needed):
        rand_byte = random.choice(_valid_char) + random.choice(_valid_char)
        out_bytes.append(rand_byte)
    out_bytes = ":".join(out_bytes)
    return out_bytes


def _is_byte(test_byte):
    """Tests if a string is a hexdecimal byte, returns True/False"""
    test_byte = test_byte.strip(":")

    # Bytes need to be two hexdecimal chars
    if len(test_byte) != 2:
        return False

    # If a byte does not convert from hex, its not a byte
    try:
        test_byte = int(test_byte, 16)
    except Exception:
        return False

    # If the value is out of range for a single byte, it is not
    if 0 < test_byte > 255:
        return False

    # If we get to the end, its a byte
    return True


def total_random():
    """Generates a completely random mac"""
    # An odd number in the first Digit is multi-cast and invalid for
    # assignment
    first_byte = random.choice(_valid_char) + random.choice(_valid_bcast_char)

    # the rest are random hexdecimal values
    five_bytes = _gen_rand_bytes(5)
    out_mac = first_byte + ":" + five_bytes
    return out_mac


def vid_file_random(vid_file):
    """Generates a MAC with random vendor bytes read from a the wireshark manuf file"""
    file_lines = _read_vid_file(vid_file)

    # Get a random line from the file
    rand_line = file_lines[random.randrange(len(file_lines))]
    # Get the MAC address from the line
    rand_line = _get_processed_vid(rand_line)
    vid_bytes = rand_line[0]

    # Now generate the random device bytes
    bytes_needed = rand_line[1] // 2
    dev_bytes = _gen_rand_bytes(bytes_needed)

    output = vid_bytes + ":" + dev_bytes
    return (output)


def vid_file_vendor(vid_file, vendor, desc=None):
    """Generates a random MAC from a specified vendor name. Takes three parameters. file name, vendor name,
    and description(optional). description can be a partial match """
    file_lines = _read_vid_file(vid_file)

    line_vendor = ""
    vid_bytes = ""
    file_desc = ""
    rand_line = ""
    # If the vendor is not in vendor list, throw an error, otherwise
    # function will hang if vendor not in
    # _valid_vendors: raise KeyError(vendor + " has no
    # associated VID byte in manuf file")

    search_lines = []
    for line in file_lines:
        line = _get_processed_vid(line)
        # split the line into named variables. for formating see above fuction _get_processed_vid()
        if len(line) == 4:
            vid_bytes, bytes_needed, line_vendor, file_desc = line
        elif len(line) == 3:
            vid_bytes, bytes_needed, line_vendor = line
        else:
            continue

        # Compile a list of matching lines into search_lines. use description if its present
        if desc == None and vendor.lower() == line_vendor.lower():
            search_lines.append(line)
        elif desc == None:
            continue
        elif desc.lower() in file_desc.lower() and vendor.lower() == line_vendor.lower():
            search_lines.append(line)
        else:
            continue

    # If there are no search_lines, there are no matches, raise error
    if len(search_lines) == 0:
        raise KeyError("No Match Vendor: " + vendor + " Desc: " + str(desc))
    rand_line = search_lines[random.randrange(len(search_lines))]
    vid_bytes, bytes_needed, line_vendor, file_desc = rand_line

    # Now generate the random device bytes
    bytes_needed = rand_line[1] // 2
    dev_bytes = _gen_rand_bytes(bytes_needed)

    output = vid_bytes + ":" + dev_bytes
    return output


def vid_provided(vid_bytes):
    """Generates only the Device bytes, given specified VID bytes"""
    test_vid = []
    rand_bytes = ""
    output = ""
    ## Start with error checking
    # remove any trailing :
    try:
        vid_bytes = vid_bytes.rstrip(":")
        test_vid = vid_bytes.split(":")
    except Exception:
        raise ValueError(str(vid_bytes) + ' are not valid VID bytes')
    # If there aren't precisely three bytes, its not a VID
    if len(test_vid) != 3:
        raise ValueError(vid_bytes + ' are not valid VID bytes')
    for byte in test_vid:
        if _is_byte(byte) == False:
            raise ValueError(str(vid_bytes) + ' are not valid VID bytes')

    # generate some new device bytes
    rand_bytes = _gen_rand_bytes(3)
    output = vid_bytes + ":" + rand_bytes
    return output


def list_vendors(vid_file):
    """Returns a list[] of valid ETH Vendors that can be used with vid_file_vendor()"""
    file_lines = _read_vid_file(vid_file)
    return _valid_vendors


def is_mac_address(mac_address):
    """Test if a given string is a valid Ethernet MAC address. return True or False"""
    # Check to make sure its 6 fields split with a colon - :
    try:
        mac_bytes = mac_address.split(":")
    except Exception:
        return False
    if len(mac_bytes) != 6:
        return False

    # Make sure all bytes are in fact bytes
    for byte in mac_bytes:
        if _is_byte(byte) == False:
            return False

    # First Octet needs to be odd.
    mac_byte_bcast = mac_bytes[0][1]
    mac_byte_bcast = mac_byte_bcast.upper()
    if mac_byte_bcast in _valid_bcast_char:
        return True
    else:
        return False


def get_vid_bytes(mac_address):
    """Return vendor bytes from a given MAC address as a string"""
    # check if this is a valid mac address
    if is_mac_address(mac_address) != True:
        raise ValueError(str(mac_address) + ' is not a valid MAC address')

    output = ""
    # Grab the first three bytes, this is the VID
    mac_bytes = mac_address.split(":")
    output = ":".join(mac_bytes[0:3])

    return output


def another_same_vid(mac_address):
    """Generate another MAC address from the same VID bytes"""
    output = ""

    vid_bytes = get_vid_bytes(mac_address)
    dev_bytes = _gen_rand_bytes(3)
    output = vid_bytes + ":" + dev_bytes
    output = output.upper()

    return output
