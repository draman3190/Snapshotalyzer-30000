# Snapshotalyzer-30000
Demo project to manage and automate AWS EC2 instance snapshots.


## About

This project is a demo, and uses boto3 to manage
AWS EC2 instance snapshots.

## Configuring

shotty uses the configuration file created by the
AWS cli. e.g.

'aws configure --profile shotty'

## Running

'pipenv run python shotty/shotty.py <command> <subcommand>
<--project=PROJECT>''

*command* is instances, volumes, or snapshots
*subcommand* depends on command, generally is list, stop, and start or reboot.
*project* still optional but --force option added in hopes to be more organized and allow for more project label usage.
