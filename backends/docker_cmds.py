# encoding: utf-8

import os

from .. import ROOTDIR, utils


def docker_version():
    return utils.extract_column(utils.filter_column(utils.Command('docker version').stdout, 0, eq='Version:'), 1)[0]


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


def container_stop(*container, **kwargs):
    image = kwargs.get('image')
    ret = True
    for cont in get_containers(image=image) if image else container:
        ret &= not utils.command('docker stop ' + cont)
    return ret


def container_delete(*container, **kwargs):
    image = kwargs.get('image')
    ret = container_stop(image=image, *container)
    for cont in get_containers(image=image, all=True) if image else container:
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
    container_stop(image=image)
    container_delete(image=image)
    return image_delete(image)


def docker_pull(image):
    return not utils.command('docker pull {}'.format(image))


def docker_build(image, tag=None):
    """ Wrapper around docker build command
    see https://docs.docker.com/engine/reference/commandline/build/
    :param image: name of the image. Can be an absolute path to a Dockerfile or an URL
           Can be an inline Dockerfile (contains \n).
    :param tag: target name of the image
    :return: True if successfull
    """
    if '\n' in image:
        if not tag:
            raise RuntimeError("Inline build requires a tag")
        cmd = 'docker build -t {} -'.format(tag)
        return not utils.command_input(cmd, image)
    else:
        if os.path.isabs(image):
            path = image
        else:
            path = os.path.join(ROOTDIR, 'images', image)
        cmd = 'docker build -t {} {}'.format(tag or image, path)
        print(utils.yellow(cmd))
        return not utils.Command(cmd, show='Build: ').returncode


def docker_run(image, container=None, parameters=None, cmd=None):
    docker_cmd = 'docker run -d'
    if container:
        docker_cmd += ' --name {0}  -h {0}'.format(container)
    if parameters:
        docker_cmd += ' ' + parameters
    docker_cmd += ' ' + image
    if cmd:
        docker_cmd += ' ' + cmd
    print(utils.yellow(docker_cmd))
    return not utils.command(docker_cmd)


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


def path_exists(path, container):
    return docker_exec('test -e {}'.format(path), container, status_only=True)


def get_data(source, container):
    return docker_exec('cat {}'.format(source), container, raises=True)


def put_file(source, dest, container):
    docker_cmd = 'docker cp {} {}:{}'.format(source, container, dest)
    return not utils.command(docker_cmd, raises=True)


def put_data(data, dest, container, append=False):
    """ Copy data to a file with optional append.
    :param data: string of data or object with read() method
    :param dest: file path on target container. The directory must exist
    :param container: container name
    :param append: if True, the data is appended to the file, otherwise, the file is created or overwritten
    """
    if append and not path_exists(dest, container):
        docker_exec('touch {}'.format(dest), container)
    docker_cmd = 'docker exec -i {} /bin/sh -c "cat {} {}"'.format(container, '>>' if append else '>', dest)
    return not utils.command_input(docker_cmd, data.read() if hasattr(data, 'read') else data, raises=True)


def put_directory(source, dest, container):
    docker_exec('mkdir -p {}'.format(dest), container, raises=True)
    with utils.cd(source):
        ret = utils.command('tar zc * | docker exec -i {} tar zx -C {}'.format(container, dest))
        if ret:
            raise RuntimeError("Error while copying {} to {}:{}".format(source, container, dest))

