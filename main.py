#!/usr/bin/env python
import argparse
import bz2
import datetime
import os
import toml
from log import logger

from client import RemoteClient

CONFIG_FILENAME = os.path.expanduser("~/.1and1db.toml")
BACKUP_FOLDER = os.path.expanduser("~/backup")
LOG_FOLDER = "./logs"


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", dest="config",
                        metavar="NAME", default=CONFIG_FILENAME,
                        help="Specify a configuration file")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Do not print status messages")

    args = parser.parse_args()

    config = toml.load(os.path.expanduser(args.config))
    time_stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")

    if not os.path.exists(LOG_FOLDER):
        os.mkdir(LOG_FOLDER)

    if not os.path.exists(BACKUP_FOLDER):
        os.mkdir(BACKUP_FOLDER)

    if not args.quiet:
        logger.info(f"Connecting to {config['ssh']['host']}...")

    remote = RemoteClient(config['ssh']['host'], config['ssh']['user'], config['ssh']['key'], None)
    for site_name in config['databases']:
        site_cfg = config['databases'][site_name]
        if not args.quiet:
            logger.info(f"Backing up {site_name}...")

        try:
            dump_cmd = f"mysqldump --host={site_cfg['host_name']} --user={site_cfg['user_name']} --password={site_cfg['password']} --lock-tables --databases {site_cfg['db_name']}"
            # zip_cmd = f"bzip2 -c > ~/backup/{site_name}-{time_stamp}.sql.bz2"
            result = remote.execute_single_command(dump_cmd)
            b_result = "\n".join(result).encode('utf8')
            fn_out = os.path.join(BACKUP_FOLDER, f"{site_name}-{time_stamp}.sql.bz2")
            with open(fn_out, 'wb') as fd:
                fd.write(bz2.compress(b_result))
        except TypeError:
            logger.warning(f'Backup failed for {site_name}')


if __name__ == "__main__":
    main()
