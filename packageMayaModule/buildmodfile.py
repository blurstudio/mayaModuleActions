import os
import re
import shutil
from pathlib import Path, PurePosixPath

PLAT_DICT = {
    "Windows": "win64",
    "Linux": "linux",
    "macOS": "mac",
}


def main(outpath, artifactpath, modname, modver, modpath, modfolders, py_limited_api):
    outpath = Path(outpath).absolute()
    basepath = outpath.parent
    modpath = Path(modpath).absolute()
    modrel = modpath.relative_to(basepath)
    artifactpath = Path(artifactpath).absolute()

    plats = "|".join(PLAT_DICT.keys())
    plat_regex = rf"(?P<platform>{plats})"
    year_regex = r"(?P<year>\d+)"

    plugin_regex = f"{plat_regex}-{year_regex}-plugin"
    python_regex = f"{plat_regex}-{year_regex}-pyModule"
    if py_limited_api:
        python_regex = f"{plat_regex}-pyModule"

    include_top = False
    modfolders = [i for i in modfolders.split() if i]
    for mf in modfolders:
        mfp = Path.cwd() / mf
        if not mfp.is_dir():
            continue
        include_top = True
        shutil.copytree(mfp, modpath / mf, dirs_exist_ok=True)

    plugPaths = sorted(list(artifactpath.glob("**/*-plugin")))
    pyPaths = sorted(list(artifactpath.glob("**/*-pyModule")))

    pydict = {}
    for pp in pyPaths:
        match = re.search(python_regex, str(pp))
        if not match:
            continue
        plat = PLAT_DICT[match['platform']]
        if py_limited_api:
            key = plat
        else:
            key = f'{plat}-{match["year"]}'

        rel = Path(key) / "pyModules"
        tar = modpath / rel
        shutil.copytree(pp, tar, dirs_exist_ok=True)
        pydict[key] = PurePosixPath(rel)

    lines = []
    if include_top:
        lines.append(f"+ {modname} {modver} {modrel}")
        lines.append("")

    for pp in plugPaths:
        match = re.search(plugin_regex, str(pp))
        if not match:
            continue
        plat, year = PLAT_DICT[match["platform"]], match["year"]
        key = f"{plat}-{year}"
        rel = Path(key) / "plug-ins"
        tar = modpath / rel
        shutil.copytree(pp, tar, dirs_exist_ok=True)
        lines.append(
            f"+ PLATFORM:{plat} MAYAVERSION:{year} {modname}_{year} {modver} {modrel}"
        )
        lines.append(f"plug-ins: {PurePosixPath(rel)}")
        if pydict:
            key = plat if py_limited_api else key
            lines.append(f"PYTHONPATH +:= {pydict[key]}")

        lines.append("")

    with open(outpath, "w") as f:
        f.write("\n".join(lines))

    sep = "-" * 80
    print("Generated Mod File:")
    print(sep)
    print(sep)
    print("\n".join(lines))
    print(sep)
    print(sep)


if __name__ == "__main__":
    main(
        os.environ["OUTPATH"],
        os.environ["ARTIFACTPATH"],
        os.environ["MODNAME"],
        os.getenv("MODVERSION", "1.0.0"),
        os.environ["MODPATH"],
        os.environ["MODFOLDERS"],
        bool(os.getenv("LIMITED", False)),
    )
