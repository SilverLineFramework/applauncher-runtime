x# Changelog
## [1.1.0](https://github.com/SilverLineFramework/sideload-runtime/compare/v1.0.2...v1.1.0) (2022-09-25)


### Features

* dockerfile ([9cfaab4](https://github.com/SilverLineFramework/sideload-runtime/commit/9cfaab4d262f84615f6c04a944573f57a81d4bce))

## [1.0.2](https://github.com/SilverLineFramework/sideload-runtime/compare/v1.0.1...v1.0.2) (2022-09-25)


### Bug Fixes

* release-please workflow ([d6891b1](https://github.com/SilverLineFramework/sideload-runtime/commit/d6891b10931bd3269b32cbf69a6581b755bc7901))

## [1.0.1](https://github.com/SilverLineFramework/sideload-runtime/compare/v1.0.0...v1.0.1) (2022-09-25)


### Bug Fixes

* edit changelog to reflect first release ([443ddaf](https://github.com/SilverLineFramework/sideload-runtime/commit/443ddaf05adda0c8d1a1058b30f2ebc424f4d8b9))

## 1.0.0 (2022-09-25)

* Initial release of fully working runtime.

### Features

* fully working Silverline runtime: register runtime; manage the lifetime of modules; send keepalives with stats
* logzero logs (configurable level, messages, etc)
* framework for different application stores where to get module files
* framework for different launchers (module start implementations)