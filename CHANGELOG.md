# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2024-04-19

### Fixed

- Fix ruff command to use the now mandatory `check` command for fixing

### Added

## [1.0.0] - 2024-02-13

### Added

- Add versioning to the convention
- Mention the adherence to Python convention in README.md

### Changed

- Move wiki doc to repo for proper review / versioning
- Disable pyright bytes type promotions

## [0.2.0] - 2024-02-05

### Changed

- Adopt hatch-openzim for metadata computation
- Upgrade dependencies
- Upgrade to Python 3.11 + 3.12 (instead of 3.10 + 3.11)
- Fix ruff configuration in pyproject.toml to fix depreciation warning in 0.2
- Fix Pyright ignore rules to adapt to breaking changes in 1.1.348

## [0.1.10] - 2023-12-12

### Fixed

- Add package location to adapt to hatchling 1.19.0

## [0.1.9] - 2023-09-19

### Changed

- Split Docker build for efficiency

## [0.1.8] - 2023-08-17

### Added

- Add sample Docker test configuration for daemon processes
- Add support for coverage HTML report

### Fixed

- Fix few invoke task arguments and help


## [0.1.7] - 2023-08-04

### Changed

- Update dependencies

## [0.1.6] - 2023-07-26

### Changed

- Enhance CI to do more tests regarding Docker and Python build and publish dev image

## [0.1.5] - 2023-07-24

### Changed

- Source Python version from pyproject.toml
- Build Docker image in CI `Publish.yaml`

### Fixed

- Adjust Ruff rules ignored by default
- Use `no-cache-dir` for package install

## [0.1.4] - 2023-07-17

### Added

- Added debugpy

## [0.1.3] - 2023-07-14

### Added

- Added a `check` feature in hatch
- Added pyright wrapper to this feature
- Installed this feature in `dev` environment
- Used `check-pyright` task in QA workflow

### Changed

- Use major versions for workflows actions
- Enable `dev` in default hatch environment

## [0.1.2] - 2023-07-13

### Fixed

- Fix version to comply with SemVer

## [0.1.1] - 2023-07-11

### Added

- Add the scripts to lint's features, otherwise we can use the hatch run lint:*


## [0.1.0] - 2023-06-22

### Added

- Initial version
