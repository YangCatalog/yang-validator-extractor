# Bottle-based YANG Extractor and Validator

A web application that allows you to fetch, extract and validate YANG modules by RFC number, by IETF draft name, or by uploading YANG files. It is built on top of the [bottle](http://bottlepy.org/docs/dev/index.html) python micro-web framework using a combination of [xym](https://github.com/YangModels/yang/tree/master/tools/xym) to fetch and extract YANG modules from IETF specifications, and [pyang](https://github.com/mbj4668/pyang), [confdc](https://developer.cisco.com/site/confD/downloads/) and [yanglint](https://github.com/CESNET/libyang) YANG compilers to validate the extracted modules.

## Prerequisites
The following requirements will be installed by the pip installation script:
- The [bottle](https://bottlepy.org/) micro-framework
- The bottle application defaults to requiring the [cherrypy](http://www.cherrypy.org/) web framework
- The [pyang](https://github.com/mbj4668/pyang) tool
- The [xym](https://github.com/xym-tool/xym) tool

The following tools will need to be manually preinstalled:
- The [yanglint](https://github.com/CESNET/libyang) tool needs to be preinstalled
- The [confdc](https://developer.cisco.com/site/confD/downloads/) compiler needs to be preinstalled, use the `--confd-install-path` option to point to the ConfD install directory (i.e. `$CONFD_DIR`)
- YANG modules commonly required for validation (e.g. the IETF modules for interface and ip configuration as well as the types) are expected to be in `/var/tmp/yangmodules/extracted`
- The default port is 8080 to avoid requiring root privileges. Use the `--port=80` option with root privileges to listen to the default HTTP port.

## Preparing the YANG modules
The `sync.sh` script uses rsync to download all IETF RFCs and drafts to a temporary directory, and then extracts all found YANG modules using `xym`. Please *read and understand* the script before you run it.