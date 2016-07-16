# bottle-yang-extractor-validator

A web application that allows you to fetch, extract and validate YANG modules by RFC number, by IETF draft name, or by uploading YANG files. It is built on top of the [bottle](http://bottlepy.org/docs/dev/index.html) python micro-web framework using a combination of [xym](https://github.com/YangModels/yang/tree/master/tools/xym) to fetch and extract YANG modules from IETF specifications, and [pyang](https://github.com/mbj4668/pyang) and the [confdc](https://developer.cisco.com/site/confD/downloads/) YANG compiler to validate the extracted modules.

## Hardcoded prerequisites in `main.py`
- The bottle application defaults to using the [cherrypy](http://www.cherrypy.org/) web framework, so this needs to be preinstalled.
- The [pyang](https://github.com/mbj4668/pyang) tool needs to be preinstalled
- The [xym](https://github.com/xym-tool/xym) tool needs to be preinstalled
- The [confdc](https://developer.cisco.com/site/confD/downloads/) compiler needs to be preinstalled, use the `--confd-install-path` option to point to the ConfD install directory (i.e. `$CONFD_DIR`)
- YANG modules commonly required for validation (e.g. the IETF modules for interface and ip configuration as well as the types) are expected to be in `/opt/local/share/yang/`
- The default port is 8080 to avoid requiring root privileges. Use the `--port=80` option with root privileges to listen to the default HTTP port.