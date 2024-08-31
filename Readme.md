# Maya Module Actions

Three actions for streamlining the compiling and distribution of maya modules: `getMayaDevkit`, `mesonBuild`, `packageMayaModule`


## Get Maya Devkit

Downloads (and caches) the maya devkit for all the versions and updates you use in your matrix

Basic Usage:

```
- name: Get Maya Devkit
  id: get-devkit
  uses: blurstudio/mayaModuleActions/getMayaDevkit@v1
  with:
    maya: 2023
    update: 3
    cache: true
```

This action also outputs the devkit path, which can be accessed like so (assuming the `id` is set to `get-devkit`)

```
${{ steps.get-devkit.outputs.devkit-path }}
```

And, just for convenience, it also outputs the maya plugin extension for the current operating system

```
${{ steps.get-devkit.outputs.plugin-ext }}
```


## Meson Build

This is just a conveneince wrapper for setting up and building with Meson (vs CMake)

Basic Usage: 

```
- name: Build
  uses: blurstudio/mayaModuleActions/mesonBuild@v1
  with:
    setup-args: >
      -Dmaya:maya_version=${{ matrix.maya }}
      -Dmaya:maya_devkit_base=${{ steps.get-devkit.outputs.devkit-path }}
      --buildtype release
      --backend ninja
```

This is not maya specific, so you can re-use this elsewhere if you like.
And it automatically detects a Windows build, and sets up the visual studio environment for compiling.
You could invoke meson directly, But dealing with the different shells required is a pain, and this action handles that part cleanly.


## Package Maya Module

Grabs all the compiled artifacts, and builds a .mod file for distributing your plugins.

Basic Usage:

```
- name: Package
  uses: blurstudio/mayaModuleActions/packageMayaModule@v1
  with: 
    module-name: TwistSpline
    folder-list: scripts icons
    version: v1.2.3
```

This would upload an artifact named TwistSpline-v1.2.3.zip.

### Requirements

All of your plugin artifacts must be named like this

    <operatingSystem>-<mayaYear>-plugin/<pluginName>.mll


Any Python modules that go with your plugin must be named like this

    <operatingSystem>-<mayaYear>-pyModule/<pythonModule>.pyd

OR

The python modules may be compiled with the limited api, and can therefore be reused across all maya versions. If so, pass `py-limited-api: true`, and build the python modules without a year in their folder structure

    <operatingSystem>-pyModule/<pythonModule>.pyd

## Full Example

Here's an example of a full yaml that will build, package, and upload artifacts, and release them when properly tagged.

```
name: build

on:
  push:
    branches: [ master ]
    tags:
      - v*
  pull_request:
    branches: [ master ]

# A minimal test matrix 
# matrix:
#   maya: [2024]
#   os: [macos-latest, ubuntu-latest, windows-latest]
#   include: 
#     - maya: 2024
#       update: 2

jobs:
  compile_plugin:
    strategy:
      matrix:
        maya: [2022, 2023, 2024, 2025]
        os: [macos-13, macos-latest, ubuntu-latest, windows-latest]
        include: 
          # Add the maya update versions here
          - maya: 2022
            update: 5
          - maya: 2023
            update: 3
          - maya: 2024
            update: 2
          - maya: 2025
            update: 1

        # cross-compiling is annoying so just fall back to macos-13
        exclude: 
          - os: macos-latest
            maya: 2022
          - os: macos-latest
            maya: 2023
          - os: macos-13
            maya: 2024
          - os: macos-13
            maya: 2025

      fail-fast: false

    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - name: Get Maya Devkit
        id: get-devkit
        uses: blurstudio/mayaModuleActions/getMayaDevkit@v1
        with:
          maya: ${{ matrix.maya }}
          update: ${{ matrix.update }}

      - name: Build
        uses: blurstudio/mayaModuleActions/mesonBuild@v1
        with:
          setup-args: >
            -Dmaya:maya_version=${{ matrix.maya }}
            -Dmaya:maya_devkit_base=${{ steps.get-devkit.outputs.devkit-path }}
            --buildtype release
            --backend ninja

      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ${{ runner.os }}-${{ matrix.maya }}-plugin
          path: build/*.${{ steps.get-devkit.outputs.plugin-ext }}
          if-no-files-found: error

  upload_release:
    name: Upload release
    needs: compile_plugin
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: git fetch --tags origin
      - name: 'Get Previous tag'
        id: previoustag
        uses: "WyriHaximus/github-action-get-previous-tag@v1"
        with:
          fallback: 0.0.1

      - name: Package
        uses: blurstudio/mayaModuleActions/packageMayaModule@v1
        with: 
          module-name: TwistSpline
          folder-list: scripts icons
          version: ${{ steps.previoustag.outputs.tag }}

      - name: Upload distribution
        if: ${{ startsWith(github.ref, 'refs/tags/v') }}
        uses: softprops/action-gh-release@v1
        with:
          token: "${{ secrets.GITHUB_TOKEN }}"
          prerelease: false
          files: |
            *.zip
```
