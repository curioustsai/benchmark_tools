import os
import logging
import argparse

from utils.ssh_client import SSHClient

log = logging.getLogger('update_modules')
log.setLevel(logging.DEBUG)
fh = logging.FileHandler(filename='update_modules.txt')
fh.setLevel(logging.DEBUG)
log.addHandler(fh)


def update_streamer(ssh, platform="gen4c", build_type="MinSizeRel", lib_type="SHARED"):
    mw_path = "/home/richard/workspace/unifi-video-fw-middleware"
    module_name = "ubnt_streamer"

    # stop streamer
    cmd = 'sed -i "s@null::respawn:/bin/ubnt_streamer@#null::respawn:/bin/ubnt_streamer@" /etc/inittab && init -q; killall ubnt_streamer'
    log.info("exe cmd: {}".format(cmd))
    ssh.execmd_getmsg(cmd)

    # update streamer and lib
    module_path = os.path.join(mw_path, "builders/cmake/output/", platform, build_type, lib_type, "rootfs/usr/bin", module_name)
    log.info("update module: {}".format(module_path))
    ssh.put_file(module_path, "/tmp/")

    libubnt_encoder_path = os.path.join(mw_path, "builders/cmake/output/", platform, build_type, lib_type, "rootfs/usr/lib/libubnt_encoder.so")
    log.info("update lib: {}".format(libubnt_encoder_path))
    ssh.put_file(libubnt_encoder_path, "/tmp/")

    libubnt_audio_utils_path = os.path.join(mw_path, "builders/cmake/output/", platform, build_type, lib_type, "rootfs/usr/lib/libubnt_audio_utils.so")
    log.info("update lib: {}".format(libubnt_audio_utils_path))
    ssh.put_file(libubnt_audio_utils_path, "/tmp/")

    # run streamer
    cmd = "export LD_LIBRARY_PATH=/tmp:$LD_LIBRARY_PATH && /tmp/ubnt_streamer &"
    log.info("exe cmd: {}".format(cmd))
    ssh.execmd_getmsg(cmd)

    return 


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Update modules")
    parser.add_argument("--ip", type=str,
                        default="192.168.1.43",
                        help="camera ip")
    parser.add_argument("--username", type=str,
                        default="ubnt",
                        help="camera username")
    parser.add_argument("--password", type=str,
                        default="ubntubnt",
                        help="camera password")
    parser.add_argument("--platform", type=str,
                        default="gen4c",
                        help="platform")
    parser.add_argument("--build_type", type=str,
                        default="MinSizeRel",
                        help="build type")
    parser.add_argument("--lib_type", type=str,
                        default="SHARED",
                        help="library type")

    p = parser.parse_args()
    camera_ip = p.ip
    username = p.username
    password = p.password
    platform = p.platform
    build_type = p.build_type
    lib_type = p.lib_type

    try:
        ssh = SSHClient(host=camera_ip, port=22,
                        username=username,
                        password=password)

        log.info('ssh successfully')
    except Exception as e:
        log.info(e)
        msg = 'connect to "{}" failed...'.format(camera_ip)
        log.info(msg)
        log.info('username = {}'.format(username))
        log.info('password = {}'.format(password))
        raise Exception(msg)

    update_streamer(ssh, platform, build_type, lib_type)
