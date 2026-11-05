# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-11-04

### Added

- `--samples` separates sampling noise from wording sensitivity
- On-disk reply cache: resume interrupted runs and re-analyze without new API calls
- `--llm-paraphrases` adds model-written rewordings
- Contributor docs, issue templates, linting and coverage in CI, release workflow

## [0.1.0] - 2026-11-04

### Added

- Rule-based meaning-preserving rewordings, answer normalizers, flip rate and stability AUROC
- OpenAI-compatible, Anthropic and shell-command backends; HTML report
