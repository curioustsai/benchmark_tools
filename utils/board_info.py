import re

board_dict = {
    'model': re.compile(r'board.name=(?P<model>.*)\n'),
    'hwaddr': re.compile(r'board.hwaddr=(?P<hwaddr>.*)\n')
}

def parse_line(line, rx_dict):
    for key, rx in rx_dict.items():
        match = rx.search(line)

        if match:
            return key, match
    return None, None

def get_model_name(ssh):
    ssh.get_file("/etc/board.info", "./board.info")
    model = ""
    hwaddr = ""

    with open("./board.info") as f:
        for line in f.readlines():
            key, match = parse_line(line, board_dict)

            if key == 'model':
                model = match.group('model')
                model = model.replace(' ', '_')
            elif key == 'hwaddr':
                hwaddr = match.group('hwaddr')

    model = model + '-' + hwaddr
    return model
