# WebHDF5

WASM compilation of a subset of libhdf5 C high- and low-level library functions.

## Building

This can only be done on Unix-like systems due to the use of GNU autotools. Maybe MinGW will work on Windows but YMMV. Also, I have not checked on a fresh system that these instructions work.

1. Clone the repository with [submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules):
```bash
git clone --recurse-submodules git@github.com:aertslab/webhdf5.git
```

2. Check that you have these tools installed:
  - Python
  - Autotools
  - Libtool
  - C compiler
  - [Emscripten](https://emscripten.org/docs/getting_started/downloads.html)

3. In the top-level directory run: `./build.py`. This does a native build of the library first (in order to get configuration programs: `H5detect` and `H5make_libsettings`), then re-compiles with Emscripten to produce a WASM binary and JS wrapper.

## Running

A HTML file is supplied called `libhdf5.html`. To run functions follow these steps:

1. Start a server with e.g. `python3 -m http.server`
2. Open a browser at `localhost:8000/libhdf5.html`. If the browser successfully loads the WASM then an alert will be displayed.
3. Open the dev console and run the library initialisation function:
```javascript
Module["_H5open"]()
```
