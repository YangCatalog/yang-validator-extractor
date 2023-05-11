# Django-based YANG Extractor and Validator

[![codecov](https://codecov.io/gh/YangCatalog/yang-validator-extractor/branch/master/graph/badge.svg?token=xFDIybuCiU)](https://codecov.io/gh/YangCatalog/yang-validator-extractor)

---

A web application that allows you to fetch, extract and validate YANG modules by RFC number, by IETF draft name, or by uploading YANG files. 
It is built on top of the [Django](https://www.djangoproject.com/) Python web framework. [xym](https://github.com/xym-tool/xym) tool is used to fetch and extract YANG modules from IETF specifications. Combination of the following YANG compilators/validators are used on the extracted modules:
- [pyang](https://github.com/mbj4668/pyang)
- [confdc](https://developer.cisco.com/site/confD/downloads/)
- [yanglint](https://github.com/CESNET/libyang)

## Prerequisites
The following requirements will be installed by the pip installation script:
- The [Django](https://www.djangoproject.com/) web framework
- The [pyang](https://github.com/mbj4668/pyang) tool
- The [xym](https://github.com/xym-tool/xym) tool

The following tools will need to be manually preinstalled:
- The [yanglint](https://github.com/CESNET/libyang) tool needs to be preinstalled
- The [confdc](https://developer.cisco.com/site/confD/downloads/) compiler needs to be preinstalled, use the `--confd-install-path` option to point to the ConfD install directory (i.e. `$CONFD_DIR`)
- The default port is 8080 to avoid requiring root privileges. Use the `--port=80` option with root privileges to listen to the default HTTP port.

## Documentation
Information about the YANG Validator API can be found here:
- https://yangcatalog.org/yangvalidator/v2/
- https://yangcatalog.org/yangvalidator/api

## Building and Deploying Docker Image

The NSO configuration is set up to listen to port 8080 to avoid requiring root to run it, so remember to use port mapping when you start the container:

```console
docker run -p 0.0.0.0:80:8080
```

## Running the Validator in AWS

The current [yangvalidator.com](https://yangvalidator.com/) instance is running on Docker on an AWS EC2 `t2.micro` instance. 
The docker image is pushed to a repository in [Amazon ECS](https://aws.amazon.com/ecs/) and then pulled from the EC2 instance.

Remember to set up the appropriate Security Group definition for the EC2 instance if you expect to reach the web server from the outside.
