# Copyright (c) 2015, European Union
# All rights reserved.
# Authors: Simonetti Dario, Marelli Andrea


def printInColor(string, color):
    """ Print message to terminal using colors """
    color = color.upper()
    colors = {'GRAY': '\033[1;m',
              'GREY': '\033[1;m',
              'RED': '\033[1;31m',
              'GREEN': '\033[1;32m',
              'BLACK': '\033[1;30m',
              'PURPLE': '\033[1;35m',
              'YELLOW': '\033[1;33m',
              'WHITE': '\033[1;29m',
              'BLUE': '\033[1;34m'}
    # TODO: - colors to be verified
    return colors[color]+string+'\033[1;m'