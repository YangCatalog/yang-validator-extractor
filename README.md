# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/YangCatalog/yang-validator-extractor/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                   |    Stmts |     Miss |   Cover |   Missing |
|--------------------------------------- | -------: | -------: | ------: | --------: |
| manage.py                              |       13 |        2 |     85% |     29-30 |
| tests/\_\_init\_\_.py                  |        0 |        0 |    100% |           |
| tests/resources/\_\_init\_\_.py        |        0 |        0 |    100% |           |
| tests/resources/settings.py            |       28 |        0 |    100% |           |
| tests/test\_modelsChecker.py           |       35 |        0 |    100% |           |
| tests/test\_views.py                   |      306 |        0 |    100% |           |
| yangvalidator/\_\_init\_\_.py          |        4 |        0 |    100% |           |
| yangvalidator/apps.py                  |        7 |        0 |    100% |           |
| yangvalidator/create\_config.py        |        6 |        0 |    100% |           |
| yangvalidator/default\_statements.py   |       20 |        0 |    100% |           |
| yangvalidator/urls.py                  |        7 |        0 |    100% |           |
| yangvalidator/v1/\_\_init\_\_.py       |        0 |        0 |    100% |           |
| yangvalidator/v1/urls.py               |        9 |        0 |    100% |           |
| yangvalidator/v1/views.py              |      420 |      348 |     17% |64-65, 93-95, 99-165, 169-179, 183-199, 203-411, 415-432, 436-477, 481-485, 489-495, 499-509, 513-525, 529-530, 534-538, 542-548, 552-555, 559-564, 568, 572 |
| yangvalidator/v2/\_\_init\_\_.py       |        0 |        0 |    100% |           |
| yangvalidator/v2/confdParser.py        |       51 |       33 |     35% |40-49, 52-80 |
| yangvalidator/v2/illegalMethodError.py |       10 |        0 |    100% |           |
| yangvalidator/v2/modelsChecker.py      |       58 |        6 |     90% |39-45, 95, 103-104 |
| yangvalidator/v2/pyangParser.py        |      104 |       46 |     56% |59-69, 77, 95-128, 134-140 |
| yangvalidator/v2/urls.py               |        9 |        0 |    100% |           |
| yangvalidator/v2/views.py              |      293 |       21 |     93% |55-65, 175, 203-204, 309-310, 353, 438, 444, 457, 461, 492 |
| yangvalidator/v2/xymParser.py          |       35 |        0 |    100% |           |
| yangvalidator/v2/yangdumpProParser.py  |       54 |       35 |     35% |42-57, 60-88 |
| yangvalidator/v2/yanglintParser.py     |       50 |        6 |     88% |35-36, 46, 60-62, 66 |
| yangvalidator/yangParser.py            |       83 |       22 |     73% |91-99, 165-166, 170-173, 197-213 |
|                              **TOTAL** | **1602** |  **519** | **68%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/YangCatalog/yang-validator-extractor/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/YangCatalog/yang-validator-extractor/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/YangCatalog/yang-validator-extractor/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/YangCatalog/yang-validator-extractor/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FYangCatalog%2Fyang-validator-extractor%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/YangCatalog/yang-validator-extractor/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.