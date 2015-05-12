# bottle-yang-extractor-validator

A web application that allows you to fetch, extract and validate YANG modules by RFC number, by IETF draft name, or by uploading YANG files. It is built on top of the [bottle](http://bottlepy.org/docs/dev/index.html) python micro-web framework using a combination of [xym](https://github.com/YangModels/yang/tree/master/tools/xym) to fetch and extract YANG modules from IETF specifications, and [pyang](https://github.com/mbj4668/pyang) to validate the extracted modules.

## Hardcoded prerequisites in `main.py`
- The pyang binary in `/usr/local/bin/`
- YANG modules commonly required for validation (e.g. the IETF modules for interface and ip configuration as well as the types) in `/opt/local/share/yang/`