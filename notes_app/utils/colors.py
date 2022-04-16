# https://qconv.com/en/color_names-rgba
class Color:
    def __init__(self, name, rgba_value):
        self.name = name
        self.rgba_value = rgba_value


AVAILABLE_COLORS = [
    Color("black", (0, 0, 0, 1)),
    Color("navy", (0, 0, 0.5, 1)),
    Color("blue", (0, 0, 1, 1)),
    Color("green", (0, 0.5, 0, 1)),
    Color("teal", (0, 0.5, 0.5, 1)),
    Color("lime", (0, 1, 0, 1)),
    Color("aqua", (0, 1, 1, 1)),
    Color("maroon", (0.5, 0, 0, 1)),
    Color("purple", (0.5, 0, 0.5, 1)),
    Color("olive", (0.5, 0.5, 0, 1)),
    Color("gray", (0.5, 0.5, 0.5, 1)),
    Color("silver", (0.75, 0.75, 0.75, 1)),
    Color("red", (1, 0, 0, 1)),
    Color("fuchsia", (1, 0, 1, 1)),
    Color("yellow", (1, 1, 0, 1)),
    Color("white", (1, 1, 1, 1))
]


def get_color_by_name(color_name):
    for color in AVAILABLE_COLORS:
        if color.name == color_name:
            return color


def get_next_color_by_rgba(rgba_value):
    iterable_available_colors = iter(AVAILABLE_COLORS)

    for color in iterable_available_colors:
        if color.rgba_value == tuple(rgba_value):
            return next(
                iterable_available_colors,
                next(iter(AVAILABLE_COLORS))
            )
