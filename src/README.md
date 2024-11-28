# CircuitPython host application for the Cardputer

See top-level README file for instructions on how to use.

## Files in this folder:
- `code.py`: CircuitPython host application logic for the Cardputer.
- `distributional.py`: Library for parsing the Signaloid C0-microSD results into a distributional value object.
- `plot_histogram_dirac_deltas.py`: Library for preparing distributional values for plotting.
- `extended_ulab_numpy.py`: Extended version of the ulab's `numpy` library that adds support for the non-implemented functions used by the `distributional.py` and `plot_histogram_dirac_deltas.py` libraries.
- `plotting.py`: Library for rendering the plot image displayed on the CardPuter's screen.
- `interface.py`: Library for interfacing with the Signaloid C0-microSD on an application level.
- `sd_protocol.py`: Library for interfacing with the Signaloid C0-microSD over the SD SPI protocol.
- `settings.toml`: Configuration file for the CircuitPython application stack size.
