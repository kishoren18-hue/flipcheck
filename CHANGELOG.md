# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-11-05

### Added

- `Gemini` backend (`--backend gemini`) using the Gemini API; works with free Google AI Studio keys
- `from_spec("gemini:<model>")` to build a backend from a provider-prefixed name
- Web app: models from different providers on one leaderboard; the leaderboard Action caches replies between runs

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
