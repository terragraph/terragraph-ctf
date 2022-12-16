# CTF Client

CTF client is a Python-based API library that enables our users to build and run
tests that communicate with the CTF backend to reserve test setups, access test
devices, post results, and save logs; it also includes a local "serverless"
mode.

## Examples

Example tests can be found in the `samples` directory.

## Requirements

* Mac OS X or Linux
* Python 3.8.8

## How CTF Client works

### Credentials

CTF credentials must be provided in any of the following ways:

1. `~/.ctf_config` file:
```json
{
  "user": "<your email address>",
  "pwd": "<your CTF password>",
  "api_server_url": "https://openctf.io/",
  "file_server_url": "https://openctf.io/"
}
```

2. Environment variables, if no `~/.ctf_config` file is found:
```
CTF_USER
CTF_PASSWORD
CTF_API_SERVER_URL
CTF_FILE_SERVER_URL
```

### Example Test Run

In order to run the `sample_date_test.py` on your local machine:
```sh
# create a Python virtual environment
$ python3 -m venv ctf_client_env

# activate virtual env
$ source ./ctf_client_env/bin/activate

# install required packages (run this command from within the common and top level dir)
$ pip install -r requirements.txt

# run test
$ python3 sample_date_test.py
```

## Documentation

### Supported APIs

* `check_if_test_setup_is_free` - Function to check if given test setup is free or not.
  * PARAMETERS
    * (int) test_setup_id - test setup id which is to be checked whether is that free or busy.
  * FUNCTION RESPONSE
    * returns the response with true or false that whether the test setup is busy or not. If its true, then the given test setup is free else it's busy.
* `copy_files_from_remote` - Copy files device to server
  * PARAMETERS
    * (str) local_path -
    * (tuple) remote_files -
    * (bool) recursive -
  * FUNCTION RESPONSE
    * returns the response dictionary with "error" and "message"
* `copy_files_to_remote` - Copy files from server to device.
  * PARAMETERS
    * (tuple) local_files -
    * (str) remote_path -
  * FUNCTION RESPONSE
    * returns the response dictionary with "error" and "message"
* `create_test_run_result` - Function to create a test run result from terminal.
  * PARAMETERS
    * (str) name - name which is to be set for test run result.
    * (str) identifier - unique string or uuid to be set as identifier for test run result.
    * (str) description - description of the test run result.
    * (int) team_id - id of team to which the test result should be added
    * (int) test_setup - test setup number test is run on
  * FUNCTION RESPONSE
    * returns the response with error or success message that whether the test run result is successfully created or not.
* `get_test_setup_devices_and_connections` - Function to get the test setup devices and its connection details.
  * PARAMETERS
    * (int) test_setup_id - test setup id of which all the details of devices and its connection needs to be fetched.
  * FUNCTION RESPONSE
    * returns the objects of connections and list of all the devices used in the given test setup.
* `action_custom_command` - Function of a device object.
  * PARAMETERS
    * (str) cmd - command to be sent over the device's connection type.
    * (int) timeout (Optional default = 50s) - how long to wait before the command times out.
  * FUNCTION RESPONSE
    * returns the result dictionary with the following keys:
    * "error": 0 if the command is able to be sent and 1 if there was any SSH problems (ex: failed to connect to device)
    * "message": the response from the device (for an SSH connection this is the stdout of the ssh command).
* `set_test_setup_and_devices_busy` - Function to set the test setup status to busy.
  * PARAMETERS
    * (int) test_setup_id - test setup id which is to be marked as busy.
  * FUNCTION RESPONSE
    * returns the response with true or false that whether the test setup id marked as busy or not. If its true then the test setup is marked as busy else test setup if free or used by other test/user.
* `set_test_setup_and_devices_free` - Function to set the test setup status to free.
  * PARAMETERS
    * (int) test_setup_id - test setup id which is to be marked as free.
  * FUNCTION RESPONSE
    * returns the response with true or false that whether the test setup id marked as free or not. If its true then the test setup is marked as free else test setup if busy or used by other test/user.
* `save_test_action_result` - Function to save test action result.
  * PARAMETERS
    * (int) test_run_id - test run id for which the action results needs to be saved.
    * (str) description - description of the action.
    * (int) outcome - outcome value of the action that whether is action is passed or failed.
    * (str) logs - action result logs that are visible in the UI.
    * (str) data - [DEPRECATED] data of the action result. Historically used for values to be graphed later, but is deprecated please leave empty for now, will be deleted soon
    * (date_time) start_time - execution start time of the action.
    * (date_time) end_time - execution end time of the action.
  * FUNCTION RESPONSE
    * returns the response with error or success message that whether the action results are successfully saved or not.
* `save_log_file` - Function used to save log files from test run to be downloaded from UI on completion of test.
  * PARAMETERS
    * (int) test_exe_id - test run id for which the action results needs to be saved.
    * (str) source_file_path - absolute path of the file to upload to fileserver.
    * (str) constructive_path - path file will be located when downloaded relative to parent dir: test_run_<test_exe_id>/
  * FUNCTION RESPONSE
    * returns the response with error or success message that whether the file is successfully saved or not.
* `save_test_run_outcome` - Function used to save test run outcome.
  * PARAMETERS
    * (int) test_run_id - test run id for which test run outcome to be saved.
  * FUNCTION RESPONSE
    * returns the test run outcome result that whether the test is passed or failed.

### Suggested test flow
```
check_if_test_setup_is_free
if test setup is free:
    create_test_run_result
    get_test_setup_devices_and_connections
    for all steps in a test:
        execute step in test (ex: device.action_custom_command)
        save_test_action_result
    save_test_run_outcome
    save_log_file
    set_test_setup_and_devices_free
```

## Contributing

See the [CONTRIBUTING](CONTRIBUTING.md) file for how to help out.

## Terms of Use

<https://opensource.facebook.com/legal/terms>

## Privacy Policy

<https://opensource.facebook.com/legal/privacy>

## License

CTF Client is MIT licensed, as found in the LICENSE file.
