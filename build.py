#!/usr/bin/python3

from __future__ import print_function

import os
import subprocess
import pprint
from pathlib import Path
import tempfile
from shutil import copy, rmtree

cleanup_dirs = []


def exported():
    with open("exported.txt") as f:
        return "EXPORTED_FUNCTIONS=" \
            + pprint.pformat([f"_{line.strip()}" for line in f]) \
                    .replace("\n", "") \
                    .replace("'", '\"')


def check_emscripten():
    try:
        path = Path(os.environ["EMSDK"])
        return [path.exists(),
                subprocess.run(["emcc", "--version"], text=True,
                               capture_output=True).stdout.split(' ')[4]]

    except KeyError:
        return [False, None]


def setup_build(prefix="build"):
    def gen_directories():
        cache = tempfile.mkdtemp(prefix="cache", dir=os.getcwd())
        cleanup_dirs.append(cache)

        while True:
            build = tempfile.mkdtemp(prefix=prefix, dir=os.getcwd())
            cleanup_dirs.append(build)
            yield [build, cache]

    if not hasattr(setup_build, "gen"):
        setup_build.gen = gen_directories()

    return setup_build.gen.__next__()


def configure():
    print("Checking for Emscripten...", end=' ')
    exists, version = check_emscripten()
    print(version, "Found")

    if not exists:
        exit(1)


def cleanup():
    for d in cleanup_dirs:
        rmtree(d)


def execute(command, in_dir):
    cwd = os.getcwd()
    os.chdir(in_dir)
    print(f"Running [{str(in_dir)}]...", " ".join(command))
    try:
        subprocess.run(command, stdout=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as err:
        print(err.__cause__)

    os.chdir(cwd)


def run_configure_script(build_dir, runner=["bash"]):
    configure_script = Path("..") / Path("libhdf5") / Path("configure")
    execute(runner + [str(configure_script), "--disable-tests",
                      "--enable-build-mode=production",
                      "--disable-tools", "--disable-shared",
                      "--disable-deprecated-symbols"],
            build_dir)


def run_make(build_dir, runner=[]):
    execute(runner + ["make", "-j8"], build_dir)


def finalise(build_dir, exported_functions):
    libs = [str(build_dir / Path("src") / Path(".libs") / Path("libhdf5.a")),
            str(build_dir / Path("hl") / Path("src") / Path(".libs")
                / Path("libhdf5_hl.a"))]

    execute(["emcc", "-O3"]
            + libs
            + ["-o", "webhdf5.js", "-s",
               "EXTRA_EXPORTED_RUNTIME_METHODS='[\"ccall\", \"cwrap\"]'",
               "-s", exported_functions],
            build_dir)
    return [build_dir / Path("webhdf5.wasm"), build_dir / Path("webhdf5.js")]


def native_build():
    build_dir, cache_dir = setup_build()
    libhdf5_dir = Path("libhdf5")
    autogen_script = Path("..") / Path("libhdf5") / Path("autogen.sh")

    execute([str(autogen_script)], libhdf5_dir)
    run_configure_script(build_dir)
    run_make(build_dir)
    copy(Path(build_dir) / Path("src") / Path("H5detect"), cache_dir)
    copy(Path(build_dir) / Path("src") / Path("H5make_libsettings"), cache_dir)


def wasm_build(exported_functions):
    build_dir, cache_dir = setup_build()
    src_dir = Path(build_dir) / Path("src")
    run_configure_script(build_dir, ["emconfigure"])
    run_make(build_dir, ["emmake"])

    copy(Path(cache_dir) / Path("H5detect"), src_dir)
    execute(["touch", "H5detect"], in_dir=src_dir)
    run_make(build_dir, ["emmake"])

    copy(Path(cache_dir) / Path("H5make_libsettings"), src_dir)
    execute(["touch", "H5make_libsettings"], in_dir=src_dir)
    run_make(build_dir, ["emmake"])

    wasm, js = finalise(Path(build_dir), exported_functions)
    copy(wasm, Path("webhdf5.wasm"))
    copy(js, Path("webhdf5.js"))

    execute(["brotli", "-9", "webhdf5.wasm"], Path())


if __name__ == "__main__":
    configure()
    try:
        native_build()
        wasm_build(exported())
    except BaseException as err:
        print(err)

    cleanup()
