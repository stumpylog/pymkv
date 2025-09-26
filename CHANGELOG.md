# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Breaking

- Internal file and function renaming ([#6](https://github.com/stumpylog/pymkv/pull/6))
  - Renamed all internal files so they are proper Python module names
  - Renamed internal ISO639 checking function

### Added

- This changelog
- Basic testing covering all the classes ([#2](https://github.com/stumpylog/pymkv/pull/2))
- pre-commit configuration and EditorConfig to standardize more items ([#4](https://github.com/stumpylog/pymkv/pull/4))

### Changed

- Updates packaging to use pyproject.toml and hatch/hatchling ([#1](https://github.com/stumpylog/pymkv/pull/1))
- Formatting and linting is now done with Ruff ([#4](https://github.com/stumpylog/pymkv/pull/4))
- Simplifies the Timestamp class using static methods and fewer members ([#5](https://github.com/stumpylog/pymkv/pull/5))
