## YANG Validator Release Notes

* ##### vm.m.p - 2022-MM-DD

* ##### v5.6.1 - 2022-10-10

  * Loading xym tool version from .env file [deployment #161](https://github.com/YangCatalog/deployment/issues/161)
  * Autocomplete functionality for IETF draft names [#107](https://github.com/YangCatalog/yang-validator-extractor/issues/107)

* ##### v5.6.0 - 2022-09-30

  * No changes - released with other [deployment submodules](https://github.com/YangCatalog/deployment)

* ##### v5.5.0 - 2022-08-16

  * Docker base image changed to python:3.9
  * Django package version bumped [#102](https://github.com/YangCatalog/yang-validator-extractor/issues/102)
  * Tracking API access using Matomo [deployment #151](https://github.com/YangCatalog/deployment/issues/151)

* ##### v5.4.0 - 2022-07-08

  * lxml package version bumped

* ##### v5.3.0 - 2022-06-06

  * Yanglint version passed as argument into Docker image build [deployment #137](https://github.com/YangCatalog/deployment/issues/137)
  * Various code adjustments after config file update [deployment #135](https://github.com/YangCatalog/deployment/issues/135)
  * yanglint update to version v2.0.194 [deployment #127](https://github.com/YangCatalog/deployment/issues/127)

* ##### v5.2.0 - 2022-05-03

  * Pyang update to version 2.5.3 [deployment #124](https://github.com/YangCatalog/deployment/issues/124)
  * Type checking fixes with pyright [deployment #126](https://github.com/YangCatalog/deployment/issues/126)

* ##### v5.1.0 - 2022-03-28

  * No changes - released with other [deployment submodules](https://github.com/YangCatalog/deployment)

* ##### v5.0.0 - 2022-02-02
  
  * Remove absolute paths from validators outputs [#89](https://github.com/YangCatalog/yang-validator-extractor/issues/89)
  * Bugfix: Problem with emitting dependencies [#84](https://github.com/YangCatalog/yang-validator-extractor/issues/84)
  * Swagger documentation created [#81](https://github.com/YangCatalog/yang-validator-extractor/issues/81)
  * Run application under 'yang' user/group [#80](https://github.com/YangCatalog/yang-validator-extractor/issues/80)
  * Pyang update to version 2.5.2 [deployment #113](https://github.com/YangCatalog/deployment/issues/113)
  * Repository renamed to yang-validator-extractor [#75](https://github.com/YangCatalog/yang-validator-extractor/issues/75)
  * lxml package version bumped
  * Send empty string instead of newline if empty validation output

* ##### v4.3.0 - 2021-12-03

  * /ping endpoint moved from v1 to v2 API

* ##### v4.2.1 - 2021-10-06

  * ConfD update to version 7.6 [deployment #99](https://github.com/YangCatalog/deployment/issues/99)
  * Dockerfile reorganized - image build speed up [#77](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/77)
  * "bottle" string removed from paths and user names [#75](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/75)
  * v2/versions endpoint added [#72](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/72)
  * Unit tests for v2 API endpoints added [#69](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/69)
  * Unit tests for modelChecker.py added [#69](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/69)

* ##### v4.2.0 - 2021-09-09

  * Removed unneeded sync.sh from Docker image build [#66](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/66)
  * Using cached rfc/draft documents if available [#29](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/29)
  * Config loading simplified [deployment #96](https://github.com/YangCatalog/deployment/issues/96)

* ##### v4.1.0 - 2021-08-10

  * No changes - released with other [deployment submodules](https://github.com/YangCatalog/deployment)

* ##### v4.0.0 - 2021-07-09

  * Pyang update to version 2.5.0 [deployment #85](https://github.com/YangCatalog/deployment/issues/85)
  * YumaPro validator updated to version 20.10-9 [deployment #84](https://github.com/YangCatalog/deployment/issues/84)
  * Make it possible to create request to validate modules outside of webpage [#39](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/39)
  * Give options to choose which file to use as a dependency [#9](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/9)
  * Create new endpoints to validate modules fo new UI [#48](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/48)
  * Upgrade django file structure
  * Updated libyang build requirements

* ##### v3.2.1 - 2021-05-04

  * No changes - released with other [deployment submodules](https://github.com/YangCatalog/deployment)

* ##### v3.2.0 - 2021-04-15

  * YumaPro validator updated to version 20.10-6 [deployment #53](https://github.com/YangCatalog/deployment/issues/53)
  * lxml, urllib3 packages versions bumped

* ##### v3.1.0 - 2021-03-18

  * xym tool update to version 0.5 [deployment #50](https://github.com/YangCatalog/deployment/issues/50)

* ##### v3.0.1 - 2021-02-26

  * rsyslog and systemd added to Docker image build [deployment #48](https://github.com/YangCatalog/deployment/issues/48)

* ##### v3.0.0 - 2021-02-10

  * Fixed /api/versions endpoint [#45](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/45)
  * ConfD update [deployment #34](https://github.com/YangCatalog/deployment/issues/34)
  * Pyang validator update [deployment #36](https://github.com/YangCatalog/deployment/issues/36)
  * YumaPro validator update
  * Fixed validation of a module/s in a .zip file [#40](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/40)
  * Update of xym tool
  * Moved to Gunicorn from Uwsgi [deployment #39](https://github.com/YangCatalog/deployment/issues/39)
  * Recursion problem fix [#32](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/32)
  * Update Dockerfile
  * Various major/minor bug fixes and improvements

* ##### v2.0.0 - 2020-08-14

  * Add health-check endpoint
  * Update of xym tool
  * Parameters loaded from config file
  * Various major/minor bug fixes and improvements

* ##### v1.1.0 - 2020-07-16

  * Fix yang failure [#30](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/30)
  * Update Pyang version
  * Update Dockerfile
  * Fix yang validator times out bug [#28](https://github.com/YangCatalog/bottle-yang-extractor-validator/issues/28)
  * Various major/minor bug fixes and improvements

* ##### v1.0.1 - 2020-07-03

  * Various major/minor bug fixes and improvements

* ##### v1.0.0 - 2020-06-23

  * Initial submitted version
