# Signaloid C0-microSD CardPuter CircuitPython Demo
This is a demo [CircuitPython](https://circuitpython.org/) host application on the [M5Stack CardPuter](https://docs.m5stack.com/en/core/CardPuter) for the [Signaloid C0-microSD Calculator Demo](https://github.com/signaloid/Signaloid-C0-microSD-Demo-Calculator).

https://github.com/user-attachments/assets/15ec10e5-6ba8-48a0-8c9f-bce33e0dc572

This demo application supports the following arithmetic operations of two uniform distributions:
- Addition
- Subtraction
- Multiplication
- Division

Folder `src` contains the CircuitPython source code that runs on the CardPuter. The CardPuter acts as the host that communicates with a Signaloid C0-microSD through its integrated microSD card slot.

Folder `submodules/C0-microSD-utilities/` contains the `interface.py` library, which is symlinked to the `src` folder, that defines the interface between the host and the Signaloid C0-microSD.

Folder `submodules/signaloid-python/` contains the `distributional.py` and `plot_histogram_dirac_deltas.py` libraries, which are symlinked to the `src` folder, that define the parsing and plotting of the distributional information from the Signaloid C0-microSD results.

## Cloning this repository
The correct way to clone this repository is:
```sh
git clone --recursive https://github.com/signaloid/Signaloid-C0-microSD-CardPuter-Demo
```

If you forgot to clone with `--recursive`, and end up with empty submodule directories, you can remedy this with
```sh
git submodule update --init --recursive
```

## How to use:

### Build & Flash the C0-microSD application
To build and flash the C0-microSD application, follow the instructions in the [Signaloid C0-microSD Calculator Demo](https://github.com/signaloid/Signaloid-C0-microSD-Demo-Calculator). This is **mandatory** before running the host application, so that the Signaloid C0-microSD is initialized with the correct firmware, and able to communicate with the host.

### Prepare the CardPuter for the CircuitPython application
To prepare the CardPuter for the CircuitPython application, you have to flash it with the CircuitPython firmware following the instructions in the [CircuitPython M5Stack CardPuter documentation](https://circuitpython.org/board/m5stack_cardputer/).

### Run the CircuitPython based host application
To run the Python host application you first need to bundle all library dependencies. To do that run this command from the `root` folder:
```sh
make
```

This command will do the following:
1. Initialize & update all submodules.
2. Apply the necessary patches to the Signaloid Python library, so that it can be used with the CardPuter using CircuitPython.
3. Create the `CircuitPythonLibs/` folder, where the [Adafruit CircuitPython bundle](https://github.com/adafruit/Adafruit_CircuitPython_Bundle) and the [Community CircuitPython bundle](https://github.com/adafruit/CircuitPython_Community_Bundle) libraries are downloaded and extracted.
4. Create the `src/lib/` folder, where the CircuitPython libraries are symlinked to.

### Copy the CircuitPython application to the CardPuter
To copy the CircuitPython application to the CardPuter, run this command from the `root` folder:
```sh
make sync
```
This command will hard copy all the files and folders from the `src` folder to the CardPuter. Make sure that you have mounted your CardPuter to your computer, and that the mount path is correctly specified at the `DEVICE` variable in the `Makefile` (default is `/run/media/<user>/CIRCUITPY`).

### Live sync the CircuitPython application to the CardPuter
To live sync the CircuitPython application to the CardPuter, while you are developing or making changes, run this command from the `root` folder:
```sh
make live-sync
```
This command will first sync all the files and folders from the `src` folder to the CardPuter, then watch for any changes in the `src` folder, and live sync them to the CardPuter. Make sure that you have mounted your CardPuter to your computer, and that the mount path is correctly specified at the `DEVICE` variable in the `Makefile` (default is `/run/media/<user>/CIRCUITPY`).

### Clean project
To clean the project, run this command from the `root` folder:
```sh
make clean
```
This command will delete the `CircuitPythonLibs/`, and the `src/lib/` folders.

### Clean the CardPuter
To clean the CardPuter, run this command from the `root` folder:
```sh
make clean-device
```
This command will delete all files and folders from the CardPuter, and will create a new "Hello World" `code.py` file. Make sure that you have mounted your CardPuter to your computer and that the mount path is correctly specified at the `DEVICE` variable in the `Makefile` (default is `/run/media/<user>/CIRCUITPY`).

## Host application
The host application is designed to parse two input arguments. Each argument specifies a uniform distribution, represented in the the [concise form of uncertainty
notation](https://physics.nist.gov/cgi-bin/cuu/Info/Constants/definitions.html#:~:text=A%20more%20concise%20form%20of,digits%20of%20the%20quoted%20result.&text=See%20Uncertainty%20of%20Measurement%20Results), i.e., `X.Y(Z)`. The application supports addition, subtraction, multiplication, and division of the input arguments.
```
usage: {add,sub,mul,div} uniform_distribution1 uniform_distribution2

Host application for C0-microSD calculator application

positional arguments:
  {add,sub,mul,div}
                        Commands
    add                 Add two uniformly distributed random variables
    sub                 Subtract two uniformly distributed random variables
    mul                 Multiply two uniformly distributed random variables
    div                 Divide two uniformly distributed random variables

    uniform_distribution1 uniform_distribution2
                        Two uniform distributions
```

For example, you can multiply the value `2.0` with a tolerance of `+- 0.5` and the value `5.0` with a tolerance of `+- 0.3` by running:

```sh
mul 2.0(5) 5.0(3)
```
