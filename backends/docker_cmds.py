# encoding: utf-8

import os
import time

from .. import ROOTDIR, utils


def get_images(filter=None):
    """ Get images names, with optional filter on name.
    :param filter: if string, get images names containing it, if python container, get images in this set.
    :return: a list of images names
    """
    images = utils.Command('docker images').stdout_column(0, 1)
    if filter:
        if isinstance(filter, basestring):
            return [x for x in images if filter in x]
        else:
            return [x for x in images if x in filter]
    return images


def get_containers(filter=None, image=None, all=True):
    """ Get containers names, with optional filter on name.
    :param filter: if string, get containers names containing it, if python container (list, set, ...),
           get containers in this set.
    :param image: if string, get containers from this image (ignore filter).
    :param all: if False, get only running containers, else get all containers.
    :return: a list of containers names
    """
    docker_cmd = 'docker ps -a' if all else 'docker ps'
    if image:
        return utils.extract_column(utils.filter_column(utils.Command(docker_cmd).stdout, 1, eq=image), -1)
    else:
        containers = utils.Command(docker_cmd).stdout_column(-1, 1)
        if filter:
            if isinstance(filter, basestring):
                return [x for x in containers if filter in x]
            else:
                return [x for x in containers if x in filter]
        return containers


def get_networks(filter=None, driver=None):
    docker_cmd = 'docker network ls'
    if driver:
        networks = utils.extract_column(utils.filter_column(utils.Command(docker_cmd).stdout, 2, 1, eq=driver), 1)
    else:
        networks = utils.Command(docker_cmd).stdout_column(1, 1)
    if filter:
        if isinstance(filter, basestring):
            return [x for x in networks if filter in x]
        else:
            return [x for x in networks if x in filter]
    return networks


def container_stop(*container):
    ret = True
    for cont in container:
        ret &= not utils.command('docker stop ' + cont)
    return ret


def container_delete(*container):
    ret = True
    for cont in container:
        ret &= not utils.command('docker rm ' + cont)
    return ret


def image_delete(*image):
    ret = True
    for im in image:
        ret &= not utils.command('docker rmi ' + im)
    return ret


def image_delete_and_containers(image):
    """ WARNING: This will remove an image and all its dependant containers
    """
    for container in get_containers(image=image):
        container_stop(container)
    for container in get_containers(image=image, all=True):
        container_delete(container)
    return image_delete(image)


def docker_build(image, tag, path=None, input=False):
    """ Wrapper around docker build command
    see https://docs.docker.com/engine/reference/commandline/build/
    :param image: the context (path to Dockerfile and other resources), can be an URL
    :param tag: target name of the image
    :param input: if True, path contains dockerfile data
    :return: True if successfull
    """
    if input:
        cmd = 'docker build -t {} -'.format(tag)
        return not utils.command_input(cmd, image)
    else:
        if os.path.isabs(image):
            path = image
        elif path:
            path = path
        else:
            path = os.path.join(ROOTDIR, 'images', image)
        cmd = 'docker build -t {} {}'.format(tag, path)
        print(utils.yellow(cmd))
        return not utils.Command(cmd, show='Build: ').returncode


def docker_run(image, container, host=None, parameters=None):
    cmd = 'docker run -d '
    cmd += '--name {} '.format(container)
    cmd += '-h {} '.format(host or container)
    if parameters:
        cmd += parameters + ' '
    cmd += image
    print(utils.yellow(cmd))
    return not utils.command(cmd)


def docker_start(container):
    return utils.command('docker start {}'.format(container))


def docker_commit(container, image):
    return not utils.command('docker commit {} {}'.format(container, image))


def get_container_ip(container, raises=False):
    docker_cmd = utils.Command("docker inspect --format '{{ .NetworkSettings.IPAddress }}' %s" % container)
    if raises and docker_cmd.stderr:
        raise RuntimeError("Container {} is not running".format(container))
    return docker_cmd.stdout.strip()


def docker_exec(cmd, container, user=None, raises=False, status_only=False, stdout_only=True):
    """ Executes a command on a running container via 'docker exec'
    :param cmd: the command to execute
    :param container: the target container
    :param user: an optional user (defaults to root)
    :param raises: if True, will raise a RuntimeError exception if command fails (return code != 0)
    :param status_only: If True, will return True if command succeeds, False if it fails
    :param stdout_only: If True, will return stdout as a string (default=True)
    :return: a subprocess.Popen object, or a string if stdout_only=True, or a boolean if status_only=True
    """
    docker_cmd = 'docker exec -i {} {} {}'.format('-u {}'.format(user) if user else '', container, cmd)
    dock = utils.Command(docker_cmd)
    if raises and dock.returncode:
        raise RuntimeError(
            "Error while executing <{}> on {}: [{}]".
                format(docker_cmd, container, dock.stderr.strip() or dock.returncode))
    if status_only:
        return not dock.returncode
    if stdout_only:
        return dock.stdout
    return dock


def docker_network(name, cmd='create', raises=True):
    allowed = ('create', 'remove')
    if cmd not in allowed:
        raise RuntimeError("Network command must be in {}, found {}".format(allowed, cmd))
    ret = utils.command('docker network {} {}'.format(cmd, name))
    if ret and raises:
        raise RuntimeError("Could not {} network {}".format(cmd, name))


def network_connect(network, container):
    if utils.command('docker network connect {} {}'.format(network, container)):
        raise RuntimeError("Could not connect {} to network {}".format(container, network))


def path_exists(path, container):
    return docker_exec('test -e {}'.format(path), container, status_only=True)


def get_data(source, container):
    return docker_exec('cat {}'.format(source), container, raises=True)


def put_file(source, dest, container):
    docker_cmd = 'docker cp {} {}:{}'.format(source, container, dest)
    utils.command(docker_cmd, raises=True)


def put_data(data, dest, container, append=False):
    """ Copy data to a file with optional append and user/perms settings.
    :param data: byte string of data
    :param dest: file path on target container. The directory must exist
    :param container: container name
    :param append: if True, the data is appended to the file, otherwise, the file is created or overwritten
    """
    if append and not path_exists(dest, container):
        docker_exec('touch {}'.format(dest), container)
    docker_cmd = 'docker exec -i {} /bin/bash -c "cat {} {}"'.format(container, '>>' if append else '>', dest)
    utils.command_input(docker_cmd, data, raises=True)


def put_directory(source, dest, container):
    docker_exec('mkdir -p {}'.format(dest), container, raises=True)
    with utils.cd(source):
        ret = utils.command('tar zc * | docker exec -i {} tar zx -C {}'.format(container, dest))
        if ret:
            raise RuntimeError("Error while copying {} to {}:{}".format(source, container, dest))

