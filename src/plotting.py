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


import board
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_imageload
from circuitpython_uplot.plot import Plot
from circuitpython_uplot.cartesian import Cartesian
from circuitpython_uplot.scatter import Scatter, Pointer

import extended_ulab_numpy as np


def rgba2rgb(bg, fg):
    """
    This function converts a background color and a foreground color with alpha
    to a RGB color.

    :param bg: The background color in the format '#RRGGBB'.
    :param fg: The foreground color in the format '#RRGGBBAA'.

    :return: The RGB color in the format '#RRGGBB'.
    """

    alpha = int(fg[6:8], 16) / 256

    bg_red = int(bg[:2], 16)
    bg_green = int(bg[2:4], 16)
    bg_blue = int(bg[4:6], 16)

    fg_red = int(fg[:2], 16)
    fg_green = int(fg[2:4], 16)
    fg_blue = int(fg[4:6], 16)

    red = int(fg_red * alpha + bg_red * (1 - alpha))
    green = int(fg_green * alpha + bg_green * (1 - alpha))
    blue = int(fg_blue * alpha + bg_blue * (1 - alpha))

    color = red << 16 | green << 8 | blue
    return color


def rgbStr2hex(color):
    """
    This function converts a color in the format '#RRGGBB' to a color in the
    format '0xRRGGBB'.

    :param color: The color in the format '#RRGGBB'.

    :return: The color in the format '0xRRGGBB'.
    """

    color = color.replace("#", "")
    return int(color, 16)


# The background color of the plot
BG_COLOR = 0xFFFFFF
BG_COLOR_STR = f"{BG_COLOR:06x}"

# The text color of the plot
TEXT_COLOR = 0x000000

# The number of decimal places to show in the ticks
MIN_TICK_DECIMAL_POINTS = 1
MAX_TICK_DECIMAL_POINTS = 3

# The size of the ticks (font characters) in pixels
TICK_SIZE = 8

# The size of the Signaloid logo in pixels
SIGNALOID_LOGO_SIZE = 24
SIGNALOID_LOGO_MARGIN = 2


# The Dirac Delta arrow characteristics
DELTA_WIDTH = 0.012
DELTA_COLOR = 0xff00ff
DELTA_ARROW_HEAD_SHIFT = -0.025
DELTA_X_RANGE = 0.5
DELTA_Y_RANGE = 1.5


def gen_xy_origin(position, width, height, align="center"):
    """
    Generates the x and y coordinates to plot a rectangle at the given
    position.

    :param position: The position of the rectangle.
    :param width: The width of the rectangle.
    :param height: The height of the rectangle.
    :param align: The alignment of the rectangle. Can be "center" or "edge".
                    If "center", the rectangle will be centered at the
                    given position.
                    If "edge", the rectangle will be aligned to the left
                    edge of the given position.

    :return: A tuple containing the x and y coordinates.
    """

    if align == "center":
        start = position - width / 2
        end = position + width / 2
    elif align == "edge":
        start = position
        end = position + width

    x = [start, start, end, end]
    y = [0, height, height, 0]

    return x, y


def bar(
    boundary_positions,
    bin_heights,
    width,
    align,
    edgecolor,
    facecolor,
    hatch="\\",
    title="",
    particle_value=None,
):
    """
    This function plots a Signaloid histogram style bar chart.

    :param boundary_positions: The positions of the bin boundaries.
    :param bin_heights: The heights of the bins.
    :param width: The width of each bin.
    :param align: The alignment of the bars. Possible values are 'edge' and
                  'center'.
    :param edgecolor: The color of the bars.
    :param facecolor: The color of particle value.
    :param hatch: The hatch pattern of the bars. This is not used, but it is
                  included for compatibility with the existing code.
    :param title: The title of the chart.
    :param particle_value: The value of the particle.
    """

    # Calculate the maximum length of the integer part of the bin heights
    # and use it to calculate the shift on the x-axis so everything fits in the
    # screen
    MAX_BIN_HEIGHT_INT_LEN = len(str(int(max(bin_heights))))
    X_SHIFT = (MAX_BIN_HEIGHT_INT_LEN + 1 + 2) * TICK_SIZE
    TICK_DECIMAL_POINTS = max(
        MIN_TICK_DECIMAL_POINTS,
        MAX_TICK_DECIMAL_POINTS - len(str(int(boundary_positions[-1]))) + 1
    )

    # Convert the edge color to a simple 3-byte RGB hex
    edgecolor = rgbStr2hex(edgecolor)

    # Convert the face color to a simple 3-byte RGB hex
    facecolor = facecolor.replace("#", "")
    if len(facecolor) > 6:
        facecolor = rgba2rgb(BG_COLOR_STR, facecolor)
    else:
        facecolor = rgbStr2hex(facecolor)

    # Create a displayio Group to hold the plot
    g = displayio.Group()

    # Create the background and append it to the group.
    # We have to create a background plot separately because the main plot is
    # smaller than the screen, and leaves empty/black space, so the background
    # one acts as a filler.
    bg_plot = Plot(
        x=0,
        y=0,
        width=board.DISPLAY.width,
        height=board.DISPLAY.height,
        show_box=False,
        background_color=BG_COLOR,
        box_color=TEXT_COLOR,
        scale=1,
    )
    g.append(bg_plot)

    # Create the main plot and append it to the group
    plot = Plot(
        x=X_SHIFT,
        y=0,
        width=board.DISPLAY.width - X_SHIFT + 2 * TICK_SIZE,
        height=board.DISPLAY.height - TICK_SIZE,
        show_box=True,
        background_color=BG_COLOR,
        box_color=TEXT_COLOR,
        scale=1,
    )
    g.append(plot)

    # Set the axes type to 'line' and set the tick parameters
    plot.axs_params(axstype="line")
    plot.tick_params(
        show_ticks=True,
        tickx_height=TICK_SIZE,
        ticky_height=TICK_SIZE,
        tickcolor=TEXT_COLOR,
        tickgrid=True,
        showtext=True,
        decimal_points=TICK_DECIMAL_POINTS,
    )

    # Show the title text
    plot.show_text(
        text=title,
        x=(board.DISPLAY.width - X_SHIFT + 2 * TICK_SIZE) // 2,
        y=TICK_SIZE,
        anchorpoint=(0.5, 0.0),
        text_color=0x00000,
        free_text=False,
    )

    # Generate the x and y coordinates for the rectangles
    x = []
    y = []
    for p, w, h in zip(boundary_positions, width, bin_heights):
        x_tmp, y_tmp = gen_xy_origin(p, w, h, align=align)
        x += x_tmp
        y += y_tmp

    # Set the plot range
    rangex = [min(x), max(x)]
    rangey = [0, max(y)]

    # Draw the histogram bars using a Cartesian plot and the generated x and y
    # coordinates
    Cartesian(
        plot=plot,
        x=x,
        y=y,
        rangex=rangex,
        rangey=rangey,
        line_color=edgecolor,
        fill=True,
        nudge=False,
        logging=False,
    )

    # Show the x-axis label
    plot.show_text(
        text="Distribution Support",
        x=(board.DISPLAY.width - X_SHIFT + 2 * TICK_SIZE) // 2,
        y=board.DISPLAY.height - 2 * TICK_SIZE,
        anchorpoint=(0.5, 0.0),
        text_color=0x00000,
        free_text=False,
    )

    # Show the y-axis label
    text_area = label.Label(
        font=terminalio.FONT,
        text="Probability Density",
        color=TEXT_COLOR,
        background_color=BG_COLOR,
        line_spacing=0.8,
        anchor_point=(0.0, 0.5),
        anchored_position=(0, board.DISPLAY.height // 2),
        label_direction="UPR",
    )
    g.append(text_area)

    # Show the particle value
    if particle_value is not None:
        # To draw the particle value, we need to create a rectangle, the same
        # way we create the histogram bars

        # Calculate the width of the particle value rectangle so that it is
        # easily visible compared to the other histogram bars
        particle_width = np.average(width) / 4

        # Use the maximum height of the histogram bars to span over the entire
        # height of the plot
        height = max(bin_heights)

        # Generate the x and y coordinates for the particle value rectangle
        x, y = gen_xy_origin(particle_value, particle_width, height, align="center")

        # Draw the particle value rectangle using a Cartesian plot
        c = Cartesian(
            plot=plot,
            x=x,
            y=y,
            rangex=rangex,
            rangey=rangey,
            line_color=facecolor,
            fill=True,
            nudge=False,
            logging=False,
        )

        # Add the "E(X)" label to the plot to indicate the particle value
        text_area = label.Label(
            font=terminalio.FONT,
            text="E(X)",
            color=TEXT_COLOR,
            line_spacing=0.8,
            anchor_point=(0.0, 0.0),
            anchored_position=(c.points[3][0] + X_SHIFT, c.points[3][1]),
            label_direction="UPR",
        )
        g.append(text_area)

    # Add the Signaloid logo to the top right corner of the screen
    sprite_sheet, palette = adafruit_imageload.load(
        "assets/signaloid_logo_24x24.bmp",
        bitmap=displayio.Bitmap,
        palette=displayio.Palette,
    )
    sprite = displayio.TileGrid(
        sprite_sheet,
        pixel_shader=palette,
        width=1,
        height=1,
    )
    sprite.x = board.DISPLAY.width - SIGNALOID_LOGO_SIZE - SIGNALOID_LOGO_MARGIN
    sprite.y = SIGNALOID_LOGO_MARGIN
    g.append(sprite)

    # Show the whole group to the screen
    board.DISPLAY.root_group = g


def annotate(
    title,
    xy=(0, 0),
    xytext=(0, 0),
    arrowprops="",
):
    """
    This function plots an annotation with a Dirac Delta arrow head.

    :param title: The title of the annotation.
    :param xy: The position of the Dirac Delta arrow head.
    :param xytext: The position of the text label. This is not used, but kept
                    for compatibility with the existing code.
    :param arrowprops: The properties of the Dirac Delta arrow head. This is
                       not used, but kept for compatibility with the existing
                       code.
    """

    position = xy[0]
    height = xy[1]

    # Calculate the maximum length of the integer part of the bin heights
    # and use it to calculate the shift on the x-axis so everything fits in the
    # screen
    MAX_BIN_HEIGHT_INT_LEN = len(str(int(height)))
    X_SHIFT = (MAX_BIN_HEIGHT_INT_LEN + 1 + 2) * TICK_SIZE

    TICK_DECIMAL_POINTS = max(
        MIN_TICK_DECIMAL_POINTS,
        MAX_TICK_DECIMAL_POINTS - len(str(int(position))) + 1
    )

    # Create a displayio Group to hold the plot
    g = displayio.Group()

    # Create the background and append it to the group.
    # We have to create a background plot separately because the main plot is
    # smaller than the screen, and leaves empty/black space, so the background
    # one acts as a filler.
    bg_plot = Plot(
        x=0,
        y=0,
        width=board.DISPLAY.width,
        height=board.DISPLAY.height,
        show_box=False,
        background_color=BG_COLOR,
        box_color=TEXT_COLOR,
        scale=1,
    )
    g.append(bg_plot)

    # Create the main plot and append it to the group
    plot = Plot(
        x=X_SHIFT,
        y=0,
        width=board.DISPLAY.width - X_SHIFT + 2 * TICK_SIZE,
        height=board.DISPLAY.height - TICK_SIZE,
        show_box=True,
        background_color=BG_COLOR,
        box_color=TEXT_COLOR,
        scale=1,
    )
    g.append(plot)

    # Set the axes type to 'line' and set the tick parameters
    plot.axs_params(axstype="line")
    plot.tick_params(
        show_ticks=True,
        tickx_height=TICK_SIZE,
        ticky_height=TICK_SIZE,
        tickcolor=TEXT_COLOR,
        tickgrid=True,
        showtext=True,
        decimal_points=TICK_DECIMAL_POINTS
    )

    # Show the title text
    plot.show_text(
        text=title,
        x=(board.DISPLAY.width - X_SHIFT + 2 * TICK_SIZE) // 2,
        y=TICK_SIZE,
        anchorpoint=(0.5, 0.0),
        text_color=0x00000,
        free_text=False,
    )

    # Generate the x and y coordinates for the rectangles
    x, y = gen_xy_origin(position, DELTA_WIDTH, height, align='center')

    # Add dummy points to the x and y coordinates to make the plot scaling
    # work correctly
    x = [position - DELTA_X_RANGE] + x + [position + DELTA_X_RANGE, position + DELTA_X_RANGE]
    y = [0] + y + [0, height * DELTA_Y_RANGE]

    # Set the plot range
    rangex = [min(x), max(x)]
    rangey = [0, max(y)]

    # Draw the Dirac Delta using a Cartesian plot and the generated x and y
    # coordinates
    c = Cartesian(
        plot=plot,
        x=x,
        y=y,
        rangex=rangex,
        rangey=rangey,
        line_color=DELTA_COLOR,
        fill=True,
        nudge=False,
        logging=False,
    )

    # Draw the Dirac Delta arrow head with a triangle
    Scatter(
        plot,
        [position + DELTA_ARROW_HEAD_SHIFT],
        [height],
        rangex=rangex,
        rangey=rangey,
        pointer=Pointer.TRIANGLE,
        pointer_color=DELTA_COLOR,
        nudge=False,
    )

    # Show the x-axis label
    plot.show_text(
        text="Distribution Support",
        x=(board.DISPLAY.width - X_SHIFT + 2 * TICK_SIZE) // 2,
        y=board.DISPLAY.height - 2 * TICK_SIZE,
        anchorpoint=(0.5, 0.0),
        text_color=0x00000,
        free_text=False,
    )

    # Show the y-axis label
    text_area = label.Label(
        font=terminalio.FONT,
        text="Probability Density",
        color=TEXT_COLOR,
        background_color=BG_COLOR,
        line_spacing=0.8,
        anchor_point=(0.0, 0.5),
        anchored_position=(0, board.DISPLAY.height // 2),
        label_direction="UPR",
    )
    g.append(text_area)

    # Add the "E(X)" label to the plot to indicate the particle value
    text_area = label.Label(
        font=terminalio.FONT,
        text="E(X)",
        color=TEXT_COLOR,
        line_spacing=0.8,
        anchor_point=(0.0, 0.0),
        anchored_position=(c.points[3][0] + X_SHIFT, c.points[3][1]),
        label_direction="UPR",
    )
    g.append(text_area)

    # Add the Signaloid logo to the top right corner of the screen
    sprite_sheet, palette = adafruit_imageload.load(
        "assets/signaloid_logo_24x24.bmp",
        bitmap=displayio.Bitmap,
        palette=displayio.Palette,
    )
    sprite = displayio.TileGrid(
        sprite_sheet,
        pixel_shader=palette,
        width=1,
        height=1,
    )
    sprite.x = board.DISPLAY.width - SIGNALOID_LOGO_SIZE - SIGNALOID_LOGO_MARGIN
    sprite.y = SIGNALOID_LOGO_MARGIN
    g.append(sprite)

    # Show the whole group to the screen
    board.DISPLAY.root_group = g
