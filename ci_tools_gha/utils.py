import os
import platform
import re

from conans.client import conan_api
from cpt.packager import ConanMultiPackager
from cpt.remotes import RemotesManager
from cpt.tools import split_colon_env
from cpt.printer import Printer

printer = Printer()


def get_recipe_path(cwd=None):
    conanfile = os.getenv("CONAN_CONANFILE", "conanfile.py")
    if cwd is None:
        return conanfile
    else:
        return os.path.join(cwd, conanfile)


_recipe_path = os.path.dirname(get_recipe_path())


def _file_contains(file, word):
    """ Read file and search for word
    :param file: File path to be read
    :param word: word to be found
    :return: True if found. Otherwise, False
    """
    if os.path.isfile(file):
        with open(file) as ifd:
            content = ifd.read()
            if word in content:
                return True
    return False


def recipe_contains(word):
    return _file_contains(get_recipe_path(), word)


def recipe_has_option(option_name):
    options = inspect_value_from_recipe(attribute="options", recipe_path=get_recipe_path())
    if options and option_name in options:
        return True

    return False


def recipe_has_setting(setting_name):
    settings = inspect_value_from_recipe(attribute="settings", recipe_path=get_recipe_path())
    if settings and setting_name in settings:
        return True

    return False


def is_custom_build_py_existing() -> (bool, str):
    custom_build_path = os.path.join(_recipe_path, "build.py")
    if os.path.isfile(custom_build_path):
        return True, custom_build_path

    return False, None


def is_pure_c():
    if recipe_contains("del self.settings.compiler.libcxx") and recipe_contains("del self.settings.compiler.cppstd"):
        return True

    return False


def get_bool_from_env(var_name, default="1"):
    val = os.getenv(var_name, default)
    return str(val).lower() in ("1", "true", "yes", "y")


def get_value_from_recipe(search_string, recipe=None):
    if recipe is None:
        recipe = get_recipe_path()
    with open(recipe, "r") as conanfile:
        contents = conanfile.read()
        result = re.search(search_string, contents)
    return result


def inspect_value_from_recipe(attribute, recipe_path):
    try:
        conan_instance, _, _ = conan_api.Conan.factory()
        inspect_result = conan_instance.inspect(path=recipe_path, attributes=[attribute])
        return inspect_result.get(attribute)
    except:
        pass
    return None


def get_name_from_recipe(recipe=None):
    name = inspect_value_from_recipe(attribute="name", recipe_path=get_recipe_path())
    return name or get_value_from_recipe(r'''name\s*=\s*["'](\S*)["']''', recipe=recipe).groups()[0]


def get_version_from_recipe(recipe=None):
    version = inspect_value_from_recipe(attribute="version", recipe_path=get_recipe_path())
    return version or get_value_from_recipe(r'''version\s*=\s*["'](\S*)["']''', recipe=recipe).groups()[0]


def is_shared(recipe=None):
    options = inspect_value_from_recipe(attribute="options", recipe_path=get_recipe_path())
    if options:
        return "shared" in options

    match = get_value_from_recipe(r'''options.*=([\s\S]*?)(?=}|$)''', recipe=recipe)
    if match is None:
        return False
    return "shared" in match.groups()[0]


def get_version(recipe=None):
    return get_version_from_recipe(recipe=recipe)


def get_conan_vars(configuration, recipe=None, kwargs={}):
    username = kwargs.get("username", os.getenv("CONAN_USERNAME", configuration["USERNAME"]))
    kwargs["channel"] = kwargs.get("channel", os.getenv("CONAN_CHANNEL", configuration["channel"]))
    version = os.getenv("CONAN_VERSION", get_version(recipe=recipe))
    kwargs["login_username"] = kwargs.get("login_username", os.getenv("CONAN_LOGIN_USERNAME"))
    kwargs["username"] = username

    return username, version, kwargs


def get_conan_upload(configuration, username):
    upload = os.getenv("CONAN_UPLOAD")
    if upload:
        return upload.split('@') if '@' in upload else upload

    return configuration["upload_remote"]


def get_conan_upload_param(configuration, username, kwargs):
    if "upload" not in kwargs or (configuration["upload"] ):
        kwargs["upload"] = get_conan_upload(configuration, username)
    return kwargs


def get_conan_remotes(configuration, username, kwargs):
    remotes = None
    if "remotes" not in kwargs:
        remotes = []
        remotes_env = os.getenv("CONAN_REMOTES")
        if remotes_env:
            remotes_env = remotes_env.split(',')
            for remote in reversed(remotes_env):
                if '@' in remote:
                    remotes.append(RemotesManager._get_remote_from_str(remote, var_name=remote))

        remotes.append(configuration["upload_remote"])
        for i in configuration["remotes"]:
            remotes.append(i)

    kwargs["remotes"] = remotes
    return kwargs


def get_upload_when_stable(kwargs):
    upload_when_stable = kwargs.get('upload_only_when_stable')
    if upload_when_stable is None:
        kwargs['upload_only_when_stable'] = get_bool_from_env("CONAN_UPLOAD_ONLY_WHEN_STABLE")
    return kwargs


def get_os():
    return platform.system().replace("Darwin", "Macos")


def get_archs(kwargs):
    if "archs" not in kwargs:
        archs = os.getenv("CONAN_ARCHS", None)
        if archs is None:
            # Per default only build 64-bit artifacts
            kwargs["archs"] = ["x86_64"]
        else:
            kwargs["archs"] = split_colon_env("CONAN_ARCHS") if archs else None
    return kwargs


def get_stable_branch_pattern(kwargs):
    if "stable_branch_pattern" not in kwargs:
        kwargs["stable_branch_pattern"] = os.getenv("CONAN_STABLE_BRANCH_PATTERN", "stable/*")
    return kwargs


def get_reference(name, version, kwargs):
    if "reference" not in kwargs:
        kwargs["reference"] = "{0}/{1}".format(name, version)
    return kwargs


def get_builder(configuration, build_policy=None, cwd=None, **kwargs):
    recipe = get_recipe_path(cwd)
    name = get_name_from_recipe(recipe=recipe)
    username, version, kwargs = get_conan_vars(configuration, recipe=recipe, kwargs=kwargs)
    kwargs = get_reference(name, version, kwargs)
    kwargs = get_conan_upload_param(configuration, username, kwargs)
    kwargs = get_conan_remotes(configuration, username, kwargs)
    kwargs = get_upload_when_stable(kwargs)
    kwargs = get_stable_branch_pattern(kwargs)
    kwargs = get_archs(kwargs)
    build_policy = os.getenv('CONAN_BUILD_POLICY', build_policy)
    builder = ConanMultiPackager(
        build_policy=build_policy,
        cwd=cwd,
        **kwargs)
    return builder


def get_builder_default(
        configuration,
        shared_option_name=None,
        pure_c=True,
        dll_with_static_runtime=False,
        build_policy=None,
        cwd=None,
        reference=None,
        **kwargs):
    recipe = get_recipe_path(cwd)
    builder = get_builder(configuration, build_policy, cwd=cwd, **kwargs)
    if shared_option_name is None and is_shared(recipe):
        shared_option_name = "%s:shared" % get_name_from_recipe(recipe)

    builder.add_common_builds(
        shared_option_name=shared_option_name,
        pure_c=pure_c,
        dll_with_static_runtime=dll_with_static_runtime,
        reference=reference)

    return builder
