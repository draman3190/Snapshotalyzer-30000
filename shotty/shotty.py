import boto3
import botocore
import click

session = boto3.Session(profile_name = 'shotty')
ec2 = session.resource('ec2')

def filter_instances(project):
    instances = []

    if project:
        filters = [{'Name': 'tag:Project', 'Values': [project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances


@click.group() #pipenv run python shotty/shotty.py will give the standard
#display screen under this entire group
#@click.option("--profile", default=None,
                #help='Choose your profile')

def cli():
    """Shotty manages snapshots"""

#Had trouble on this, but ultimately I managed to enable the function to change users.
#Will only work if the credentials are recognized in the .aws folder. so shotty will work
#but something like kevin will not work because kevin is not a user recognized in our
#.aws folder. In order for it to work, you would need to create a new user and paste
#the information in the .aws folder which likely would only occur if the user who
#made this program allows for it as he would be the one with access to said folder.
#Possibly good for security? Not sure entirely...

#Alternatively, you could automate the creation of new users so that the addition of
#information in the .aws folder doesn't have to be manual
#but I think this is good enough for the goal of this project.
@cli.group('profiles')
def profiles():
    """Commands for profiles"""

@profiles.command('change_profile')
@click.option('--profile', default=None,
                help='Choose your profile')

def change_profile(profile):
    try:
        if profile:
            session = boto3.Session(profile_name = str(profile))
            ec2 = session.resource('ec2')
    except botocore.exceptions.ProfileNotFound:
        print("The profile name entered is not registered. Please add it to the AWS configuration folder \nalong with the proper credentials and try again.")




@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project', default=None,
              help="Only snapshots for project(tag Project:<name>)")
@click.option('--instance', prompt=False,
                help='Individually select a snapshot to list')
@click.option('--all', 'list_all', default=False, is_flag=True,
 help="List all snapshots for each volume, not just the most recent volume." )

def list_snapshots(project, list_all, instance):
    "List EC2 snapshots"
    instances = filter_instances(project)


    if instance:

        for i in instances:
            if i.id == instance:
                for v in i.volumes.all():
                    for s in v.snapshots.all():
                        print(', '.join((
                        s.id,
                        v.id,
                        i.id,
                        s.state,
                        s.progress,
                        s.start_time.strftime("%c")
                        )))

                        if s.state == 'completed' and not list_all:
                            break
    else:
        for i in instances:
            for v in i.volumes.all():
                for s in v.snapshots.all():
                    print(', '.join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
                    )))

                    if s.state == 'completed' and not list_all:
                        break


def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0].state == 'pending'

@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project', default=None,
              help="Only volumes for project(tag Project:<name>)")
@click.option('--instance', prompt=False,
                help='Individually lists a volume to the list')
def list_volumes(project, instance):
    "List EC2 volumes"
    instances = filter_instances(project)
    if instance:
        for i in instances:
            if i.id == instance:
                for v in i.volumes.all():
                    print(', '.join((
                    v.id,
                    i.id,
                    v.state,
                    str(v.size) + "GiB",
                    v.encrypted and "Encrypted" or "Not Encrypted"
                    )))
    else:
        for i in instances:
            for v in i.volumes.all():
                print(', '.join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and "Encrypted" or "Not Encrypted"
                )))


@cli.group('instances')#If called, will show all options for this group
#list,stop,start
def instances():
    """Commands for instances"""

@instances.command('reboot', help="Reboots instances")
@click.option('--project', default=False,
                help='Only instances for project(tag Project:<name>')
@click.option('--instance', prompt=False,
                help='Individually select an instance to reboot')

#--force must be represented in the function def as force argument.
#is_flag=True specifies the argument as always true so if --force is called, the code will read it as true.
#Thus the code will inititate.
#--project, default=False so basically when the command for reboot is initiated, project is set to false by default.
#So the if project or force: will return False and move to the else block and return an error statement.
@click.option('--force', is_flag=True,
                help="Forces command to initiate without specifying project labels.")
def reboot(project, force, instance):#Note that reboot and restart are not the same, hence you cannot reboot a stopped instance.
                #Made this on my own.

    instances = filter_instances(project)
    if project or force:

        for i in instances:
            if i.state['Name'] == "running":
                print("Rebooting the following instance: " + i.id)
                i.reboot()
            else:
                print("The instance " + i.id + " is currently stopped. Please make sure the instance is running before attempting to reboot.")

    elif instance:
        for i in instances:
            if i.id == instance:
                if i.state['Name'] == "running":
                    print("Rebooting the following instance: " + i.id)
                    i.reboot()
                else:
                    print("The instance " + i.id + " is currently stopped. Please make sure the instance is running before attempting to reboot.")

    else:
        print("Project must be specified. --force to continue without project labels.")





@instances.command('snapshot',
help="Create snapshots of all volumes")
@click.option('--instance', prompt=False,
                help='Individually select a snapshot to create.')
@click.option('--project', default=None,
              help="Only instances for project(tag Project:<name>)")
@click.option('--force', is_flag=True,
                help="Forces command to initiate without specifying project labels.")
def create_snapshots(project, force, instance):
    "Create snapshots for EC2 instances"

    instances = filter_instances(project)
    try:
        if project or force:

            for i in instances:
                print("Stopping... {0}".format(i.id))
                i.stop()
                i.wait_until_stopped()
                for v in i.volumes.all():
                    if has_pending_snapshot(v):
                        print("Skipping {0}, snapshot already in progress".format(v.id))
                        continue
                    print("Creating snapshots of {0}".format(v.id))
                    v.create_snapshot(Description="Created by our Snapshotalyzer30000")
                print("Starting... {0}".format(i.id))
                i.start()
                i.wait_until_running()

                print("Job's done!")


        elif instance:
            nameHolder = ""
            for i in instances:
                if i.id == instance:
                    print("Stopping... {0}".format(i.id))
                    i.stop()
                    i.wait_until_stopped()
                    for v in i.volumes.all():
                        if has_pending_snapshot(v):
                            print("Skipping {0}, snapshot already in progress".format(v.id))
                            continue
                        print("Creating snapshots of {0}".format(v.id))
                        v.create_snapshot(Description="Created by our Snapshotalyzer30000")
                    print("Starting... {0}".format(i.id))
                    i.start()
                    i.wait_until_running()
                    nameHolder = str(i.id)
                    print("Job's done!")

            if nameHolder != instance:
                print("Sorry, the instance ID is invalid, please try again.")

        else:
            print("Project not specified, --force to continue without project labels.")

    except botocore.exceptions.ClientError:
        print("AWS Service had some trouble, please try again.")



@instances.command('list')
@click.option('--instance', prompt=False,
                help='Individually select an instance to list')
#Basic Value Options on click documentation
@click.option('--project', default=None,
              help="Only instances for project(tag Project:<name>)")
def list_instances(project, instance):
    "List EC2 instances"



    instances = filter_instances(project)
    if instance:
        try:
            nameHolder = ""
            for i in instances:
                if i.id == instance:
                        tags = {t['Key']: t['Value'] for t in i.tags or []}
                        print(', '.join((
                        i.id,
                        i.instance_type,
                        i.placement['AvailabilityZone'],
                        i.state['Name'],
                        i.public_dns_name,
                        tags.get('Project', '<no project>')
                        )))
                        nameHolder = str(i.id)
            if nameHolder != instance:
                print("Sorry, the instance ID is invalid, please try again.")

        except botocore.exceptions.ClientError as e:
            print(" Could not stop {0}. ".format(i.id) + str(e))

    else:
        for i in instances:
            tags = {t['Key']: t['Value'] for t in i.tags or []}
            print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project', '<no project>')
            )))
        return




@instances.command('stop')
@click.option('--instance', prompt=False,
                help='Individually select an instance to stop')
@click.option('--project', default=None,
                help='Only instances for project')
@click.option('--force', is_flag=True,
                help="Forces command to initiate without specifying project labels.")
def stop_instances(project, force, instance):
    'Stop EC2 instances'

    instances = filter_instances(project)
    if project or force:

        for i in instances:
            print("Stopping {0}... ".format(i.id))
            try:
                i.stop()
            except botocore.exceptions.ClientError as e:
                print(" Could not stop {0}. ".format(i.id) + str(e))
                continue

#Selects indivudal instances to stop.
    elif instance:
        try:
            nameHolder = ""
            for i in instances:
                if i.id == instance:
                    print("Stopping {0}...".format(i.id))
                    i.stop()
                    i.wait_until_stopped()
                    nameHolder = str(i.id)
            if nameHolder != instance:
                print("Sorry, the instance ID is invalid, please try again.")

        except botocore.exceptions.ClientError as e:
            print(" Could not stop {0}. ".format(i.id) + str(e))


    else:
        print("Project not specified. --force to continue without project labels.")



@instances.command('start')
@click.option('--instance', prompt=False,
                help='Individually select an instance to start')
@click.option('--project', default=None,
                help='Only instances for project')
@click.option('--force', is_flag=True,
                help="Forces command to initiate without specifying project labels.")

def start_instances(project, force, instance):
    'Start EC2 instances'
    instances = filter_instances(project)
    if project or force:

        for i in instances:
            print("Starting {0}... ".format(i.id))
            try:
                i.start()
            except botocore.exceptions.ClientError as e:
                print(" Could not start {0}. ".format(i.id) + str(e))
                continue
    elif instance:
        try:
            nameHolder = ""
            for i in instances:
                if i.id == instance:
                    print("Starting {0}...".format(i.id))
                    i.start()
                    i.wait_until_running()
                    nameHolder = str(i.id)
            if nameHolder != instance:
                print("Sorry, the instance ID is invalid, please try again.")

        except botocore.exceptions.ClientError as e:
            print(" Could not start {0}. ".format(i.id) + str(e))

    else:
        print("Project not specified. --force to continue without project labels.")


if __name__ == '__main__':
    cli()
