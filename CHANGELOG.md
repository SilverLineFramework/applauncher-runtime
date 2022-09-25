x# Changelog
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
