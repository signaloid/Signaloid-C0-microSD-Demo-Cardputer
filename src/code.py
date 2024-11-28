# Copyright (c) 2024, Signaloid.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


import struct

import board
import busio
import sd_protocol as sd
from distributional import DistributionalValue
from interface import C0microSDSignaloidSoCInterface
from plot_histogram_dirac_deltas import PlotHistogramDiracDeltas


class APP_CONFIG:
    """Application configuration.

    This class contains the configuration for the application, including the
    pin assignments for the SPI interface and the SPI baudrate.
    """
    PIN_MOSI = board.SD_MOSI
    PIN_MISO = board.SD_MISO
    PIN_CLK = board.SD_SCK
    PIN_SD_CS = board.SD_CS
    SPI_BAUDRATE = 5000000
    SPI_PHASE = 0
    SPI_POLARITY = 0
    SD_REPEAT_TIMEOUT = 1000


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

        # Initialize SD
        self.sd = sd.SD(
            spi=self.spi,
            cs_pin=APP_CONFIG.PIN_SD_CS,
            timeout=APP_CONFIG.SD_REPEAT_TIMEOUT
        )


class C0microSDSignaloidSoCInterfaceSDSPI(C0microSDSignaloidSoCInterface):
    """Communication interface for C0-microSD over SPI.

    This class provides basic functionality for interfacing with the
    Signaloid C0-microSD through the SD SPI interface.
    """

    def __init__(self, sd: sd.SD, force_transactions: bool = False) -> None:
        super().__init__(force_transactions)

        self.sd = sd

    def _read(self, offset, bytes) -> bytes:
        """
        Reads data from the C0-microSD.

        :return: The read buffer
        """
        if bytes % 512 == 0:
            num_blocks = bytes // 512
        else:
            num_blocks = bytes // 512 + 1
        data = self.sd.read_blocks(offset, num_blocks)
        return data[0:bytes]

    def _write(self, offset, data) -> int:
        """
        Write data to the C0-microSD.

        :param buffer: The data buffer to write.
        :return: Number of bytes written.
        """
        # Pad the data to 512 bytes
        remaining_bytes = 512 - (len(data) % 512)
        data += bytes(remaining_bytes)

        return self.sd.write_blocks(offset, data)


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


def pack_doubles(doubles: list, size: int) -> bytes:
    """
    Pack a list of doubles to a zero-padded bytes buffer of length size.

    :param doubles: List of doubles to be packed
    :param size: Size of target buffer

    :return: The padded bytes buffer
    """
    buffer = struct.pack(f"{len(doubles)}d", *doubles)

    # Pad the buffer with zeros
    if len(buffer) < size:
        buffer += bytes(size - len(buffer))
    elif len(buffer) > size:
        raise ValueError(
            f"Buffer length exceeds {size} bytes after packing doubles."
        )
    return buffer


def unpack_doubles(byte_buffer: bytes, count: int) -> list[int]:
    """
    This function unpacks 'count' number of double-precision floating-point
    numbers from the given byte buffer. It checks if the buffer has enough
    data to unpack.

    Parameters:
        byte_buffer: A bytes object containing the binary data.
        count: The number of double-precision floats (doubles) to unpack.

    Returns:
        A list of unpacked double values.
    """

    # Each double (double-precision float) is 8 bytes
    double_size = 8

    # Check if the buffer has enough bytes to unpack the requested
    # number of doubles
    expected_size = double_size * count
    if len(byte_buffer) < expected_size:
        raise ValueError(
            f"Buffer too small: expected at least {expected_size} bytes, \
                got {len(byte_buffer)} bytes.")

    # Unpack the 'count' number of doubles ('d' format for double in struct)
    format_string = f'{count}d'
    doubles = struct.unpack(format_string, byte_buffer[:expected_size])

    return list(doubles)


def pack_unsigned_integers(uint: list, size: int) -> bytes:
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


def parse_tolerance_value(value_with_uncertainty: str) -> tuple:
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

    return min_value, max_value


def main():
    # Clear the screen
    print("\n"*10)

    # Initialize the device
    d = Device()

    # Initialize the C0-microSD interface
    C0_microSD = C0microSDSignaloidSoCInterfaceSDSPI(d.sd)

    # Get the default display root group (the terminal), so that we can
    # restore it later
    default_display_root_group = board.DISPLAY.root_group

    # Try to get the status of the C0-microSD, if it is not in SoC mode, then
    # raise an exception and exit the program
    try:
        C0_microSD.get_status()
        print(C0_microSD)

        if C0_microSD.configuration != "soc":
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
            data = pack_doubles(
                [arg_a_min, arg_a_max, arg_b_min, arg_b_max],
                C0_microSD.MOSI_BUFFER_SIZE_BYTES,
            )
            C0_microSD.write_signaloid_soc_MOSI_buffer(data)

            # Calculate result
            result_buffer = C0_microSD.calculate_command(
                calculation_commands[args_command])

            # Interpret and remove the first 4 bytes as an unsigned integer
            returned_bytes = struct.unpack("I", result_buffer[:4])[0]

            # Keep only needed bytes in buffer
            result_buffer = result_buffer[4:]
            result_buffer = result_buffer[:returned_bytes]

            print("Parsing distribution.")
            distribution = DistributionalValue.parse(result_buffer)

            print("Plotting distribution.")
            plt = PlotHistogramDiracDeltas()
            plt.plot_histogram_dirac_deltas(
                [distribution],
                plotting_resolution=16,
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
