import os
import re
import argparse
from pathlib import Path, PurePosixPath


WIN = "Windows"
LIN = "Linux"
MAC = "macOS"


def main(outpath, modname, modver, modpath, py_limited_api, include_top):
    outpath = Path(outpath).absolute()

    basepath = outpath.parent
    modpath = Path(modpath).absolute()
    modrel = modpath.relative_to(basepath)

    plat_regex = rf"(?P<platform>{WIN}|{MAC}|{LIN})"
    year_regex = r"(?P<year>\d+)"

    plugin_regex = f"{plat_regex}-{year_regex}"
    python_regex = plugin_regex
    if py_limited_api:
        python_regex = plat_regex

    plugPaths = sorted(list(modpath.glob(str(Path("**") / "plug-ins"))))
    pyPaths = sorted(list(modpath.glob(str(Path("**") / "pyModules"))))

    pydict = {}
    for pp in pyPaths:
        rel = PurePosixPath(pp.relative_to(modpath))
        match = re.search(python_regex, str(rel))
        if not match:
            continue
        pydict[match.groups()] = rel

    lines = []
    if include_top:
        lines.append(f"+ {modname} {modver} {modrel}")
        lines.append("")

    for pp in plugPaths:
        rel = PurePosixPath(pp.relative_to(modpath))
        match = re.search(plugin_regex, str(rel))
        if not match:
            continue
        plat, year = match["platform"], match["year"]
        lines.append(
            f"+ PLATFORM:{plat} MAYAVERSION:{year} {modname}_{year} {modver} {modrel}"
        )
        lines.append(f"plug-ins: {rel}")
        if pydict:
            key = (plat,) if py_limited_api else (plat, year)
            lines.append(f"PYTHONPATH +:= {pydict[key]}")

        lines.append("")

    with open(outpath, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main(
        os.environ["OUTPATH"],
        os.environ["MODNAME"],
        bool(os.getenv("MODVERSION", "1.0.0")),
        os.environ["MODPATH"],
        bool(os.getenv("LIMITED", False)),
        bool(os.getenv("TOP", False)),
    )
