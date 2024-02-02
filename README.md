# DASIA-IoT project
This repository is part of the DASIA-IoT project, focused on detecting attacks against IoT devices through power usage reads and Machine Learning.

The following papers have been published for this project:

- _Intrusion detection for IoT environments through side-channel and Machine Learning techniques_ (2024) (awaiting publication, a link to the paper will be made available here in the future)

The following repositories are included in this project:

- [IOT](https://github.com/CenitS-COMPUTAEX/IOT): Contains scripts used to train and test one or more Machine Learning models, as well as scripts used to test and run them. Models can be run offline (with an existing dataset) or online (reading real-time data from a buffer).
- IOT_pi (this repository): Contains scripts that run on the devices to launch attacks and read power usage.

Physically, the code in these repositories is meant to work with a setup consisting on a main device that manages several end devices, launching attacks against them and reading their power usage.

# Table of contents
* [Project structure](#project-structure)
* [Attacks](#attacks)
  * [Attack requirements](#attack-requirements)
* [Common operations](#common-operations)
  * [Read power usage using the main device](#read-power-usage-using-the-main-device)
  * [Read power usage using the main device + Launch attacks in random intervals](#read-power-usage-using-the-main-device--launch-attacks-in-random-intervals)
  * [Manually start and stop attacks](#manually-start-and-stop-attacks)
  * [Make one of the end devices generate fake power reads and save them to a buffer file](#make-one-of-the-end-devices-generate-fake-power-reads-and-save-them-to-a-buffer-file)
* [Other questions and answers](#other-questions-and-answers)
  * [How do I specify connection details for my end devices?](#how-do-i-specify-connection-details-for-my-end-devices)
  * [How can new attacks be added?](#how-can-new-attacks-be-added)
  * [I have a separate script that launches an attack. How do I use it alongside the code in this repository?](#i-have-a-separate-script-that-launches-an-attack-how-do-i-use-it-alongside-the-code-in-this-repository)
  * [Some of the scripts in this repository need to run for a long time. How can I launch them as background processes?](#some-of-the-scripts-in-this-repository-need-to-run-for-a-long-time-how-can-i-launch-them-as-background-processes)

# Project structure
- [code](code): Scripts
	- [attacks](code/attacks): Scripts related to launching attacks on the devices
		- [files](code/attacks/files): Attack scripts sent to remote devices to run attacks
		- [scripts](code/attacks/scripts): Scripts that implement the actual attacks or attack launchers
	- [data](code/data): Scripts used to create and write the output files
	- [defs](code/defs): Common definitions used in multiple places
	- [lib](code/lib): External libraries imported as code files. **The license under which this repository is made available does not cover the files in this folder.**
- [crypt](crypt): Source code of the encryption attack (C++)
- [example_files](example_files): Contains some example files that can be used to recreate our experiment setup
- [Config.xml](Config.xml): Configuration file for the project. Includes a description for each parameter. It might be necessary to modify some of them before running the project on a new environment.
- [LICENSE](LICENSE): Contains the license that applies to the code files contained in this repository.
- [requirements.txt](requirements.txt): List of packages that must be installed to run the scripts in this reprository.
- [requirements-exact.txt](requirements-exact.txt): List of packages that must be installed to run the scripts in this reprository, incluing the exact version of all the dependencies used by us.

Scripts meant to be directly run can are located directly in the [code](code) folder. These scripts show information about the arguments and flags that can be passed to them when they are run without arguments or with the `--help` flag. That information should be enough to know how to run them. They also contain a comment at the start of the file explaining their purpose.

The script [attack_interface.py](code/attack_interface.py) works a bit differently than the rest: It's meant to be called by external programs that launch an attack to ensure that the start and end time of the attack is correctly flagged. This allows implementing new attacks using external scripts without having to manually register the start and end times.

**Important**: These scripts should be run from the root of the repository (e.g. `python code/main_run_model.py`), not from the [code](code) folder.

# Attacks
The following attacks are implemented in this repository:

- Mining: The main device sends a mining program to the target device. The program uses all available cores on the device, greatly increasing its CPU usage.
- Login: A program run from the main device tries to guess the password of the target device through brute force to gain unauthorized access. The attack launches multiple concurrent SSH connections, which also forces the target device to handle all the requests at once.
- Encryption: An encryption program is sent to the target device and executed. The program encrypts some of the files on the target device, simulating the behavior of a ransomware virus.
- Password: The remote device is forced to run a script that tries to crack a password hash through brute force by computing SHA-256 hashes. The program sleeps at random intervals to avoid being detected.
- Lite Mining: Similar to the Mining attack, but it only uses 2 threads instead of 4. This reduces its power usage, making it harder to detect.

## Attack requirements
In order to run the different attacks on the target devices, both the main and end devices must follow certain requirements. Since attacks are implemented as python scripts, the **main** device must have Python installed. The Python version used in our tests is Python 3.9.2, other versions (specially older ones) might not work. The specific requirements for each type of attack are listed below:

- All attacks
	- Connection data (IP address, username and password) must be specified for each end device in `Config > Devices`
		- (`Config > Devices` refers to the `<Devices>` XML element in the config file, [Config.xml](Config.xml))
- Mining attack
	- The **main** device must have the executable of the [cpuminer](https://github.com/tpruvot/cpuminer-multi) mining program located at `Config > Attacks > Mining > FileToSend`.
		- If you need to send a different executable to each device (because they have different architectures and a single binary wouldn't be compatible with all of them), you instead need to specify the list of executable files to send at `Config > Attacks > Mining > FilesToSend`.
	- The executable of the mining program must be able to run on the **end** device.
	- The **end** device should have at least 2 processors, since otherwise the power usage of this attack will be very similar to that of other attacks.
- Login attack
	- The **main** device must have [hydra](https://github.com/vanhauser-thc/thc-hydra) installed, with the SSH module enabled.
- Encryption attack
	- The **main** device must have the executable of the encryption program located at `Config > Attacks > Encryption > FileToSend`.
		- If you need to send a different executable to each device (because they have different architectures and a single binary wouldn't be compatible with all of them), you instead need to specify the list of executable files to send at `Config > Attacks > Encryption > FilesToSend`.
	- The **end** device must have a folder with files to encrypt located at `Config > Attacks > Encryption > FolderToEncrypt`. The duration of an iteration depends on the total size of the files contained in this folder. This is important since the attack won't end until the current iteration finishes. Ideally, an iteration should take at most 5-6 seconds. This means the files in this folder might need to be adjusted depending on the processing power of the end device.
		- Some example files are provided under [example_files/files_to_encrypt](example_files/files_to_encrypt).
	- The executable of the encryption program must be able to run on the **end** device.
		- To ensure this, compile the encryption program on the end device using the source code, which can be found in the [crypt](crypt) folder.
			- To enable debug output, compile the code with the g++ `-D DEBUG` flag. This will print the time taken to encrypt the files when the program is run directly, which can be used to determine if the time taken is too long.
- Password attack
	- The **end** device must have Python installed.
- Lite mining attack
	- All the requirements of the mining attack.
	- The **end** device must have at least 3 processors, since otherwise this attack will be the same as the standard mining attack.
- Test attack
	- The **main** device must have the test script located at `test_attack.FILE_TO_SEND`.
		- (`test_attack.FILE_TO_SEND` refers to the value of the constant `FILE_TO_SEND` declared at [code/attacks/scripts/test_attack.py](code/attacks/scripts/test_attack.py))
	- The **end** device must have Python installed.

# Common operations
This section lists some operations that can be performed with the scripts in this repository, as well as the device they should be performed on. This section assumes that all the repositories from the project are contained in the same folder and that the scripts are being run from the root folder of this repository.

To get more information about the parameters and flags, check the help messages provided by the scripts.

**Important**: The commands must be run on a system or Python virtual environment that has all the required packages installed. The commands also assume that python is run with the `python` command, although some devices might use `python3` instead.

## Read power usage using the main device
This command will make the main device read the power usage of all the configured devices, saving them to separate csv files.

- Device: Main
- Command: `python code/main_loop.py`
  - Add the `-b` flag to store the data in a cyclic buffer file instead
  - By default, a column listing the active attacks will be included in the output file. Add the `-na` flag to exclude it. There aren't any situations where this is really necessary, but it might be helpful if no attacks are going to be launched using the tools in this repository.

## Read power usage using the main device + Launch attacks in random intervals
This command will make the main device read the power usage of all the configured devices, while also launching attacks against them depending on the exact parameters specified.

- Device: Main
- Command: `python code/main_loop.py -a -l <rest of arguments>`
  - The rest of the arguments specify how the attacks will be launched (list of devices to attack, which attacks to launch, duration of the attacks, delay between them, etc.). Check the help info of [main_loop.py](code/main_loop.py) for the list of possible arguments.

## Manually start and stop attacks
This command launches the tool that allows the user to manually start and stop attacks against the devices.

- Device: Main
- Command: `python code/main_attack_tool.py -r`

## Make one of the end devices generate fake power reads and save them to a buffer file
End devices don't have a way to read their own power usage. In order to allow testing of the models deployed on the devices themselves, this script will generate fake power reads in the same format as real reads so they can be passed to the models.

- Device: End
- Command: `python code/end_device_loop.py data/buffer.csv <buffer size>`
  - The minimum buffer size depends on the model that will be run. It must be at least _group_amount_ * _num_groups_ entries.

# Other questions and answers
Since the repository has a somewhat complex structure, this section lists how to perform some less common operations, as well as how to properly modify some parts of the project.

## How do I specify connection details for my end devices?
This programs connects to end devices using SSH to launch attacks to them, so it needs to know the IP address, login username and password of those devices to make the connection. All that data must be supplied through the configuration file ([Config.xml](Config.xml)).

Power usage is read through the _INA_3221_ library, which does not use IP addresses, so changes are not needed there as long as the devices are correctly connected physically.

## How can new attacks be added?
In order to implement a new attack, follow these steps:

1. The list of attacks is defined in the `AttackType` enum, in [attacks/attack_type.py](code/attacks/attack_type.py). A new entry must be added, including a string that identifies it in the `from_str()` method.
2. Create a new class under [attacks/scripts](code/attacks/scripts). The class must extend `BaseAttack`, implementing the required methods.
3. Modify `AttackFactory`, in [attacks/attack_factory.py](code/attacks/attack_factory.py), to allow instantiating the new type of attack based on the `AttackType` values.
4. Update the help text in [main_loop.py](code/main_loop.py) and [main_attack_tool.py](code/main_attack_tool.py) to list the new attacks.
5. Modify the method `_get_attack_letters()` in IOT/defs/utils.py to include the abbreviated representation of the new attack, which should be composed of 1 or 2 uppercase letters.

Consider if it's necessary to add a new line to the `INCOMPATIBLE_ATTACKS` constant (in [defs/constants.py](code/defs/constants.py)). This is only necessary if the new attack can't be active at the same time as some other existing attack(s).

## I have a separate script that launches an attack. How do I use it alongside the code in this repository?
The preferred solution would be implementing an attack in this repository that simply calls your external script when started. That would allow starting it through [main_loop.py](code/main_loop.py) and [main_attack_tool.py](code/main_attack_tool.py).

If that's not an option, follow steps 1 and 5 listed in [How can new attacks be added?](#how-can-new-attacks-be-added), Then make sure that your script calls [attack_interface.py](code/attack_interface.py) when starting and ending the attack so the system can properly log the start and end times (this is required to automatically label the resulting dataset).

## Some of the scripts in this repository need to run for a long time. How can I launch them as background processes?
It's not recommended to run the scripts as synchronous processes on a terminal window, specially if they are being run on other devices through an SSH connection, since closing the terminal (and sometimes other things like suspending the device) can kill the script.

In order to avoid this problem, we recommend using the `nohup` UNIX utility to launch the scripts:

First, the old log file should be deleted if it still exists (`rm nohup.out`). Then the script can be launched with `nohup python -u <script name>.py <arguments> &`. The command shows the ID of the background process that was just created. This process can be manually killed early with `kill -15 <PID>`.

The output is saved to the file _nohup.out_. It's possible to check how it updates in real time by running `tail -f nohup.out`.

As an example, the following command was used to generate the dataset for scenario 1: `nohup python -u code/main_loop.py -a -l --devices 1,2,3 --duration 360 --delay 30,10 --min-delay 60 --attacks 0,1,2 --attack-duration 3,1 --min-attack-duration 10 --multi-chance 20 --short-chance 20 --short-duration 20 &`

## The tool is logging a nonzero value on the "Attacks" column even though there's no active attacks. Why?
This can happen if any of the scripts that can launch attacks crashes unexpectedly, or if the system is shut down while they're running. To fix it, run `python code/main_attack_tool.py`, then type `clean` to remove leftover files.

## I'm trying to start an attack using main_attack_tool, but it says the attack is already active (started by another script). What does that mean?
Attacks can't be started from multiple scripts at the same time. Check that you don't have another script that is currently running an attack. To forcefully mark the attacks as ended, run `python code/main_attack_tool.py`, then type `clean`.