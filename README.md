# Terragraph CTF

<p align="center">
  <img src="./docs/media/logo/terragraph-logo-full-RGB.svg" width="320" />
</p>

Terragraph is a gigabit wireless technology designed to meet the growing demand
for reliable high-speed internet access. Documentation for the project can be
found at [terragraph.com](https://terragraph.com).

This repository contains a comprehensive automated test suite for Terragraph,
consisting of test implementations and a test runner application for the
Connectivity Testing Framework (CTF) developed by Meta. Test plan documentation
can be found [here](http://terragraph.github.io/terragraph-ctf).

## Building

### Dependencies

* Python 3.8
* [requests](https://pypi.org/project/requests/) - Used in test implementations
* [later](https://github.com/facebookincubator/later) - Used for unit tests
* [pandas](https://pypi.org/project/pandas/) - Used in SIT routing tests to analyze data by columns

### Installation

```sh
# Init venv
$ python3 -m venv venv
$ source ./venv/bin/activate

# Install dependencies
$ pip install --upgrade pip
$ cd ./ctf/ctf_client/ ; pip install -r requirements.txt ; cd -
$ cd ./ctf/common/     ; pip install -r requirements.txt ; cd -
$ pip install requests later pandas

# Run CTF
$ export EXTERNAL_DEPLOYMENT=True
$ python3 tg_ctf_runner.py --help

# Run unit tests
$ python3 -m unittest terragraph/ctf/unittests_lib.py
```

## Usage

### Commands

* `run <TestName>` - Run a CTF test (or test suite)
* `describe <TestName>` - Show test description and parameters
* `list-tests` - List all tests (and test suites)
* `list-setups` - List all setups registered in CTF
* `force-free <id>` - Forcefully free a test setup

### Credentials

CTF credentials must be provided in any of the following ways:

1. `~/.ctf_config` file:
```json
{
  "user": "user@fb.com",
  "pwd": "<your CTF password>",
  "api_server_url": "https://openctf.io/",
  "file_server_url": "https://openctf.io/"
}
```

2. Environment variables:
```
CTF_USER
CTF_PASSWORD
CTF_API_SERVER_URL
CTF_FILE_SERVER_URL
```

### Serverless Mode

The CTF client includes a "serverless" feature which allows running tests
locally without a CTF server instance. The test results are stored on the local
machine. To enable this mode, pass `--serverless=true` to the "run" command,
for example:
```
python3 tg_ctf_runner.py run TestTgCtfTest --test-setup-id 1 --serverless=true
```

This requires additional configuration files as listed below:

1. Create `~/.ctf_serverless_config` with the following contents:
```json
{
  "test_setups_dir": "/path/to/test_setups_dir",
  "test_results_dir": "/path/to/test_results_dir",
  "ctf_client_app_data": "/path/to/ctf_client_app_data"
}
```

2. Create the test setup files, which will hold all the devices and their
   connection details. The files must be named `<setup_id>.json` within the
   "test_results_dir" directory, for example `1.json` with the contents below:
```json
{
  "id": 1,
  "name": "CTF-Setup-1",
  "description": "2 node Puma setup",
  "report_data": "{}",
  "device_mapping_details": [
    {
      "device_type_id": 107,
      "node_number": 1
    },
    {
      "device_type_id": 107,
      "node_number": 2
    }
  ],
  "devices": [
    {
      "name": "puma-1",
      "serial_number": "aa:11:00:00:00:01",
      "firmware_version": "",
      "device_type": 107,
      "device_sub_type": null,
      "description": "",
      "latitude": 0,
      "longitude": 0,
      "height": 0,
      "connections": [
        {
          "id": 1,
          "is_active": true,
          "connection_type": 100,
          "device": 1,
          "jump_host": null,
          "jump_host_name": "",
          "ip_address": "2001::1",
          "port": 22,
          "username": "root",
          "password": "facebook",
          "timeout": 60,
          "prompt": "#",
          "custom_channel_processing": false,
          "key": null,
          "key_name": null,
          "shell_family": {
            "id": 1,
            "name": "BOURNE"
          },
          "shell_family_name": "BOURNE"
        }
      ],
      "device_type_data": {
        "device_type": 107,
        "device_sub_type": null,
        "device_ptr": 1,
        "is_gps_connected": true,
        "device_type_name": "Terragraph",
        "device_class_name": "TerragraphInterface"
      },
      "terragraph_slots": [
        {
          "wireless_mac_addr": "aa:00:00:00:00:01",
          "slot": "1",
          "slot_identifier": 0,
          "display_name": "slot_1"
        }
      ],
      "node_number": 1
    },
    {
      "name": "puma-2",
      "serial_number": "aa:11:00:00:00:02",
      "firmware_version": "",
      "device_type": 107,
      "device_sub_type": null,
      "description": "",
      "latitude": 0,
      "longitude": 0,
      "height": 0,
      "connections": [
        {
          "id": 2,
          "is_active": true,
          "connection_type": 100,
          "device": 2,
          "jump_host": null,
          "jump_host_name": "",
          "ip_address": "2001::2",
          "port": 22,
          "username": "root",
          "password": "facebook",
          "timeout": 60,
          "prompt": "#",
          "custom_channel_processing": false,
          "key": null,
          "key_name": null,
          "shell_family": {
            "id": 1,
            "name": "BOURNE"
          },
          "shell_family_name": "BOURNE"
        }
      ],
      "device_type_data": {
        "device_type": 107,
        "device_sub_type": null,
        "device_ptr": 2,
        "is_gps_connected": true,
        "device_type_name": "Terragraph",
        "device_class_name": "TerragraphInterface"
      },
      "terragraph_slots": [
        {
          "wireless_mac_addr": "bb:00:00:00:00:01",
          "slot": "1",
          "slot_identifier": 0,
          "display_name": "slot_1"
        }
      ],
      "node_number": 2
    }
  ]
}
```

## File Structure

```
tests/                 # Test implementations (Python)

sample_data/           # Sample test configuration files (JSON)
  nodes_data/          # - Setup-specific test data
  tests/               # - Test-specific test data

                       # Application modules
tg_ctf_runner.py       # - Test runner main class
tg_ctf_tests.py        # - Test class and test suite declarations/imports

                       # Test base classes
lib.py                 # - CTF framework/API library
tg.py                  # - Terragraph-specific methods
puma.py                # - Puma hardware-specific methods
x86_tg.py              # - x86 Terragraph host methods
x86_traffic_gen.py     # - x86 traffic generator methods
sit.py                 # - System Integration Testing (SIT) test methods

                       # Other Python modules
consts.py              # - Application/test constants
exceptions.py          # - CTF exception classes

                       # Unit tests
unittests_lib.py       # - Unit test library
unittests_fixtures.py  # - Unit test fixtures

docs/                  # Test plan documentation
docusaurus/            # Website
```

## Community
Please review our [Code of Conduct](CODE_OF_CONDUCT.md) and
[Contributing Guidelines](CONTRIBUTING.md).

General discussions are held on our
[Discord server](https://discord.gg/HQaxCevzus).

![](https://discordapp.com/api/guilds/982440743765409822/widget.png?style=banner2)

## License
Terragraph CTF has an MIT-style license as can be seen in the [LICENSE](LICENSE)
file.
