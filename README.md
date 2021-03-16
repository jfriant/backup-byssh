# Backup-BySSH

This was written to backup and download SQL databases hosted by Ionos.com.  The databases can only be accessed from the web host, so a SSH connection is required before running the mysqldump command.  The result is downloaded and compressed with BZ2.

## Configuration

The script can be configured to backup multiple databases for a given host.  The file is in TOML format and should based on the example-config.toml file.

## Credits

The SSH client code was taken from https://github.com/hackersandslackers/paramiko-tutorial
