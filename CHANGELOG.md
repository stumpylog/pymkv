# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Breaking

- Internal file and function renaming ([#6](https://github.com/stumpylog/pymkv/pull/6))
  - Renamed all internal files so they are proper Python module names
  - Renamed internal ISO639 checking function
- All functions and methods are now strongly typed
- Construction of an `MKVFile`, `MKVTrack` or `MKVAttachment` should now be done through one of the static factory methods
- Removed the track moving and swapping from `MKVFile` for now
- Splitting functionality now takes strongly typed classes for the complicated methods, such as frame splits
- Provided file paths are now assumed to be Maktroska or supported containers. If not supported an `UnsupportedContainerError` will be raised
- In the event of an `mkvmerge` subprocess failure, the stderr and stdout will be logged
- Files are no longer verified to be Maktroska files. This incurred multiple subprocess invocations

### Added

- This changelog
- Basic testing covering all the classes ([#2](https://github.com/stumpylog/pymkv/pull/2))
- pre-commit configuration and EditorConfig to standardize more items ([#4](https://github.com/stumpylog/pymkv/pull/4))
- The library now integrates with standard logging

### Changed

- Updates packaging to use pyproject.toml and hatch/hatchling ([#1](https://github.com/stumpylog/pymkv/pull/1))
- Formatting and linting is now done with Ruff ([#4](https://github.com/stumpylog/pymkv/pull/4))
- Simplifies the Timestamp class using static methods and fewer members ([#5](https://github.com/stumpylog/pymkv/pull/5))
