import os
import shlex
import subprocess


def main(build_path, maya_version, build_type, dk_path, setup_args):
    # fmt: off
    cmd = [
        "meson", "setup", build_path,
        f'-Dmaya:maya_version={maya_version}',
        f'-Dmaya:maya_devkit_base={dk_path}',
        "--buildtype", build_type,
        "--backend", "ninja",
    ]
    # fmt: on
    if os.name == "nt":
        cmd.append("--vsenv")

    setup_args = shlex.split(setup_args)
    if setup_args:
        cmd.extend(setup_args)
    subprocess.run(cmd)


if __name__ == "__main__":
    main(
        os.environ["BUILD_PATH"],
        os.environ["MAYA_VER"],
        os.environ["BUILD_TYPE"],
        os.environ["DK_PATH"],
        os.environ["SETUP_ARGS"],
    )
