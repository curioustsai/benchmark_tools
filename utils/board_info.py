import re
import os

project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
tmp_dir =os.path.join(project_dir, 'tmp')

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
    if not os.path.exists(tmp_dir ):
        os.makedirs(tmp_dir )

    board_file = os.path.join(tmp_dir , "board.info")
    ssh.get_file("/etc/board.info", board_file)
    model = ""
    hwaddr = ""

    with open(board_file) as f:
        for line in f.readlines():
            key, match = parse_line(line, board_dict)

            if key == 'model' and match is not None:
                model = match.group('model')
                model = model.replace(' ', '_')
            elif key == 'hwaddr' and match is not None:
                hwaddr = match.group('hwaddr')

    model = model + '-' + hwaddr
    return model
