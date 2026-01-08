#   Copyright (c) 2024, Signaloid.
#
#   Permission is hereby granted, free of charge, to any person obtaining a
#   copy of this software and associated documentation files (the "Software"),
#   to deal in the Software without restriction, including without limitation
#   the rights to use, copy, modify, merge, publish, distribute, sublicense,
#   and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.


import struct

import board
import busio
from microcontroller import Pin

from c0microsd.interface import C0microSDSignaloidSoCInterfaceSDSPI
from signaloid.circuitpython.plot_wrapper import plot
from signaloid.distributional.distributional import DistributionalValue
from signaloid.distributional_information_plotting.plot_histogram_dirac_deltas import \
    PlotData


class APP_CONFIG:
    """Application configuration.

    This class contains the configuration for the application, including the
    pin assignments for the SPI interface and the SPI baudrate.
    """
    PIN_MOSI: Pin = board.SD_MOSI
    PIN_MISO: Pin = board.SD_MISO
    PIN_CLK: Pin = board.SD_SCK
    PIN_SD_CS: Pin = board.SD_CS
    SPI_BAUDRATE: int = 5000000
    SPI_PHASE: int = 0
    SPI_POLARITY: int = 0
    SD_REPEAT_TIMEOUT: int = 1000
    DOUBLE_PRECISION: bool = False
    PLOTTING_RESOLUTION: int = 32


class Device:
    def __init__(self):
        # Initialize SPI
        self.spi = busio.SPI(
            clock=APP_CONFIG.PIN_CLK,
            MOSI=APP_CONFIG.PIN_MOSI,
            MISO=APP_CONFIG.PIN_MISO,
        )
        while not self.spi.try_lock():
            pass
        self.spi.configure(
            baudrate=APP_CONFIG.SPI_BAUDRATE,
            phase=APP_CONFIG.SPI_PHASE,
            polarity=APP_CONFIG.SPI_POLARITY
        )
        self.spi.unlock()

        # Initialize the C0-microSD interface
        self.C0_microSD: C0microSDSignaloidSoCInterfaceSDSPI = C0microSDSignaloidSoCInterfaceSDSPI(
            spi=self.spi,
            cs_pin=APP_CONFIG.PIN_SD_CS,
            timeout=APP_CONFIG.SD_REPEAT_TIMEOUT
        )


kCalculateNoCommand = 0
kCalculateAddition = 1
kCalculateSubtraction = 2
kCalculateMultiplication = 3
kCalculateDivision = 4

calculation_commands = {
    "add": kCalculateAddition,
    "sub": kCalculateSubtraction,
    "mul": kCalculateMultiplication,
    "div": kCalculateDivision,
}


def pack_floats(floats: list[float], size: int, double_precision: bool = True) -> bytes:
    """
    Pack a list of floats to a zero-padded bytes buffer of length size

    :param floats: List of floats to be packed
    :param size: Size of target buffer
    :param double_precision: If the floats are in double precision representation

    :return: The padded bytes buffer
    """
    format_str = f"{len(floats)}{'d' if double_precision else 'f'}"
    buffer = struct.pack(format_str, *floats)

    # Pad the buffer with zeros
    if len(buffer) < size:
        buffer += bytes(size - len(buffer))
    elif len(buffer) > size:
        raise ValueError(
            f"Buffer length exceeds {size} bytes after packing floats."
        )
    return buffer


def unpack_floats(byte_buffer: bytes, count: int, double_precision: bool = True) -> list[int]:
    """
    This function unpacks 'count' number of single or double precision
    floating-point numbers from the given byte buffer. It checks if the
    buffer has enough data to unpack.

    :param byte_buffer: A bytes object containing the binary data.
    :param count: The number of floats to unpack.
    :param double_precision: If the floats are in double precision representation

    :return A list of unpacked floating-point values.
    """

    # 4 bytes for each single-precision float
    # 8 bytes for each double-precision float
    float_size = 8 if double_precision else 4

    # Check if the buffer has enough bytes to unpack the requested
    # number of floats
    expected_size = float_size * count
    if len(byte_buffer) < expected_size:
        raise ValueError(
            f"Buffer too small: expected at least {expected_size} bytes, \
                got {len(byte_buffer)} bytes.")

    # Unpack the 'count' number of floats
    format_string = f"{count}{'d' if double_precision else 'f'}"
    floats = struct.unpack(format_string, byte_buffer[:expected_size])

    return list(floats)


def pack_unsigned_integers(uint: list[int], size: int) -> bytes:
    """
    Pack a list of unsigned integers to a zero-padded bytes.
    buffer of length size

    :param uint: List of unsigned integers to be packed
    :param size: Size of target buffer

    :return: The padded bytes buffer
    """
    buffer = struct.pack(f"<{len(uint)}I", *uint)

    # Pad the buffer with zeros
    if len(buffer) < size:
        buffer += bytes(size - len(buffer))
    elif len(buffer) > size:
        raise ValueError(
            f"Buffer length exceeds {size} bytes after packing doubles."
        )
    return buffer


def parse_tolerance_value(value_with_uncertainty: str) -> tuple[float, float]:
    """
    This function parses a string following the concise form of uncertainty
    notation 'X.Y(Z)' to create a uniform distribution, whose minimum and
    maximum values are returned as a tuple.

    For more information on the concise form of uncertainty notation, see:
    https://physics.nist.gov/cgi-bin/cuu/Info/Constants/definitions.html#:~:text=A%20more%20concise%20form%20of,digits%20of%20the%20quoted%20result.&text=See%20Uncertainty%20of%20Measurement%20Results

    :param  value_with_uncertainty: the string to parse

    :raises ValueError: when the input string is not in the correct format

    :return: minimum and maximum values of the uniform distribution
    """

    # Split the value and the uncertainty part
    if '(' not in value_with_uncertainty or ')' not in value_with_uncertainty:
        raise ValueError(
            "Invalid format. Please provide value in the format 'X.Y(Z)'")

    # Extract the main value and the uncertainty
    value_str, uncertainty_str = value_with_uncertainty.split('(')
    uncertainty_str = uncertainty_str.strip(')')

    # Find smallest order
    if "." in value_str:
        # Split at the decimal point
        _, decimal_part = value_str.split(".")
        order = -(len(decimal_part))
    else:
        order = 0

    # Convert to appropriate types
    value = float(value_str)
    uncertainty = int(uncertainty_str)

    # Calculate minimum and maximum values
    min_value = value - (uncertainty * (10 ** order))
    max_value = value + (uncertainty * (10 ** order))

    return (min_value, max_value)


def main():
    # Clear the screen
    print("\n"*10)

    # Initialize the device
    d = Device()

    # Get the default display root group (the terminal), so that we can
    # restore it later
    default_display_root_group = board.DISPLAY.root_group

    # Try to get the status of the C0-microSD, if it is not in SoC mode, then
    # raise an exception and exit the program
    try:
        d.C0_microSD.get_status()
        print(d.C0_microSD)

        if d.C0_microSD.configuration != "soc":
            raise RuntimeError(
                "Error: The C0-microSD is not in SoC mode. "
                "Switch to SoC mode and try again."
            )
    except Exception as e:
        print(e)
        return

    # Main loop: Continue to ask for commands until the user enters 'q'
    while True:
        try:
            print("\n"*2)

            # Ask the user for a command
            command = input("Give me a command...\n")
            args_command, args_argument_a, args_argument_b = command.split(" ")

            # Parse inputs
            arg_a_min, arg_a_max = parse_tolerance_value(args_argument_a)
            arg_b_min, arg_b_max = parse_tolerance_value(args_argument_b)

            print("Sending parameters to C0-microSD...")
            data = pack_floats(
                [arg_a_min, arg_a_max, arg_b_min, arg_b_max],
                d.C0_microSD.MOSI_BUFFER_SIZE_BYTES,
                double_precision=APP_CONFIG.DOUBLE_PRECISION
            )
            d.C0_microSD.write_signaloid_soc_MOSI_buffer(data)

            # Calculate result
            result_buffer = d.C0_microSD.calculate_command(
                calculation_commands[args_command])

            # Interpret and remove the first 4 bytes as an unsigned integer
            returned_bytes = struct.unpack("I", result_buffer[:4])[0]

            # Keep only needed bytes in buffer
            result_buffer = result_buffer[4:]
            result_buffer = result_buffer[:returned_bytes]

            print("Parsing distribution.")
            distribution = DistributionalValue.parse(
                result_buffer,
                double_precision=APP_CONFIG.DOUBLE_PRECISION
            )

            if distribution is None:
                print("Cannot parse resulting Ux bytes.")
                return

            print(distribution)

            print(f"Plotting {command}")
            plot(
                plot_data=PlotData(
                    distribution,
                    plotting_resolution=APP_CONFIG.PLOTTING_RESOLUTION,
                ),
                plot_name=command
            )
        except Exception as e:
            print(
                f"An error occurred while calculating: \n{e} \nAborting.",
            )

        # Ask the user to press Enter to continue, or 'q' to exit
        res = input("Press Enter to continue, or q to exit...")

        # Restore the default display root group (the terminal)
        board.DISPLAY.root_group = default_display_root_group

        if res == 'q':
            return


if __name__ == "__main__":
    main()
