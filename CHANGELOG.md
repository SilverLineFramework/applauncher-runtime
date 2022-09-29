x# Changelog
## [1.1.2](https://github.com/SilverLineFramework/sideload-runtime/compare/v1.1.1...v1.1.2) (2022-09-29)


### Bug Fixes

* add daemon start mode flag ([59f5731](https://github.com/SilverLineFramework/sideload-runtime/commit/59f573103dddc17440b09c1517d90ac5fcb5f6b8))

## [1.1.1](https://github.com/SilverLineFramework/sideload-runtime/compare/v1.1.0...v1.1.1) (2022-09-28)


### Bug Fixes

* add wait for it script ([45207c9](https://github.com/SilverLineFramework/sideload-runtime/commit/45207c986d1031056b1017eba832006ca7da0284))
* add wait for it script ([418f9cf](https://github.com/SilverLineFramework/sideload-runtime/commit/418f9cf877bacff08430bcbc96931144ff97b654))
* add wait for it script ([c6a66ca](https://github.com/SilverLineFramework/sideload-runtime/commit/c6a66caa217bbec386603e8156b3268b58686fa3))

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
