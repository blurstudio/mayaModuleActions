# Maya Module Actions

Two actions for streamlining the compiling and distribution of maya modules.

The first is `getMayaDevkit`, which will download and cache the maya devkit for all the years and updates you use in your matrix

The second is `packageMayaModule`, which will grab all the compiled artifacts, and build a .mod file for distributing your plugins.


## Get Maya Devkit

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


## Package Maya Module

Basic Usage:

```
- name: Package
  uses: blurstudio/mayaModuleActions/packageMayaModule@v1
  with: 
    module-name: TwistSpline
    folder-list: scripts icons
    version: v1.2.3
```

This will upload an artifact named TwistSpline-v1.2.3.zip.

### Requirements

All of your plugin artifacts must already have a folder structure matching this pattern

    <operatingSystem>-<mayaYear>/plug-ins/<pluginName>.mll


Any Python modules that go with your plugin are either similarly structured

    <operatingSystem>-<mayaYear>/pyModules/<pythonModule>.pyd

OR

The python modules may be compiled with the limited api, and can therefore be reused across all maya versions. If so, pass `py-limited-api: true`, and build the python modules without a year in their folder structure

    <operatingSystem>/pyModules/<pythonModule>.pyd

## Example

Here's an example of a full yaml that will build, package, and upload artifacts, and release them on a tag

```
name: build

on:
  push:
    branches: [ master ]
    tags:
      - v*
  pull_request:
    branches: [ master ]

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
        uses: blurstudio/mayaModuleActions/mayaMesonBuild@v1
        with:
          maya: ${{ matrix.maya }}
          update: ${{ matrix.update }}
          build-type: release
          devkit-path: ${{ steps.get-devkit.outputs.devkit-path }}

      - name: Repath Artifacts
        shell: bash
        run: |
          mkdir -p artifacts/plug-ins
          cp build/*.${{ steps.get-devkit.outputs.plugin-ext }} artifacts/plug-ins

      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ${{ runner.os }}-${{ matrix.maya }}
          path: artifacts/plug-ins/*.${{ steps.get-devkit.outputs.plugin-ext }}
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
