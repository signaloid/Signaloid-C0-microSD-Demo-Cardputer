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


#   ulab's numpy implementation only supports a subset of numpy's functions.
#   So this file contains functions that are not supported by ulab's numpy, but
#   are needed for the calculations of this project.
#
#   ulab's numpy supported functions are:
#   ['all', 'any', 'bool', 'sort', 'sum', 'acos', 'acosh', 'arange', 'arctan2',
#   'argmax', 'argmin', 'argsort', 'around', 'array', 'asarray', 'asin', 'asinh',
#   'atan', 'atanh', 'bitwise_and', 'bitwise_or', 'bitwise_xor', 'ceil', 'clip',
#   'compress', 'concatenate', 'convolve', 'cos', 'cosh', 'cross', 'degrees',
#   'delete', 'diag', 'diff', 'dot', 'e', 'empty', 'equal', 'exp', 'expm1',
#   'eye', 'fft', 'flip', 'float', 'floor', 'frombuffer', 'full',
#   'get_printoptions', 'inf', 'int16', 'int8', 'interp', 'isfinite', 'isinf',
#   'left_shift', 'linalg', 'linspace', 'load', 'loadtxt', 'log', 'log10',
#   'log2', 'logspace', 'max', 'maximum', 'mean', 'median', 'min', 'minimum',
#   'nan', 'ndarray', 'ndinfo', 'nonzero', 'not_equal', 'ones', 'pi', 'polyfit',
#   'polyval', 'radians', 'right_shift', 'roll', 'save', 'savetxt',
#   'set_printoptions', 'sin', 'sinc', 'sinh', 'size', 'sqrt', 'std', 'tan',
#   'tanh', 'trace', 'trapz', 'uint16', 'uint8', 'vectorize', 'where', 'zeros']


import math

from ulab.numpy import *

# Alias for numpy.float
from ulab.numpy import float as np_float
float_ = np_float


def isnan(arr):
    """
    This function checks if an array or value contains any NaN values.

    :param arr: Can be an array or a single value.

    :return: If the input is an array, returns a list of booleans indicating
             whether each element is NaN.
             If the input is a single value, returns a boolean indicating
             whether the value is NaN.
    """

    if isinstance(arr, (list, ndarray)):
        return list(map(lambda x: math.isnan(x), arr))

    return math.isnan(arr)


def add(arr1, arr2):
    """
    This function adds two arrays or adds an array and a single value.

    :param arr1: The first array to add.
    :param arr2: The second array or value to add.

    :return: If the input is two arrays, returns a new array containing the
             sum of the two arrays, element-wise.
             If the input is an array and a single value, returns a new array
             containing the sum of the array and the single value.
    """

    if isinstance(arr2, (list, ndarray)):
        return list(map(lambda x1, x2: x1 + x2, arr1, arr2))

    return list(map(lambda x1: x1 + arr2, arr1))


def subtract(arr1, arr2):
    """
    This function subtracts two arrays or subtracts an array and a single value.

    :param arr1: The first array to subtract.
    :param arr2: The second array or value to subtract.

    :return: If the input is two arrays, returns a new array containing the
             subtraction of the two arrays, element-wise.
             If the input is an array and a single value, returns a new array
             containing the subtraction of the array and the single value.
    """

    if isinstance(arr2, (list, ndarray)):
        return list(map(lambda x1, x2: x1 - x2, arr1, arr2))

    return list(map(lambda x1: x1 - arr2, arr1))


def multiply(arr1, arr2):
    """
    This function multiplies two arrays or multiplies an array and a single value.

    :param arr1: The first array to multiply.
    :param arr2: The second array or value to multiply.

    :return: If the input is two arrays, returns a new array containing the
             multiplication of the two arrays, element-wise.
             If the input is an array and a single value, returns a new array
             containing the multiplication of the array and the single value.
    """

    if isinstance(arr2, (list, ndarray)):
        return list(map(lambda x1, x2: x1 * x2, arr1, arr2))

    return list(map(lambda x1: x1 * arr2, arr1))


def divide(arr1, arr2):
    """
    This function divides two arrays or divides an array and a single value.

    :param arr1: The first array to divide.
    :param arr2: The second array or value to divide.

    :return: If the input is two arrays, returns a new array containing the
             division of the two arrays, element-wise.
             If the input is an array and a single value, returns a new array
             containing the division of the array and the single value.
    """

    if isinstance(arr2, (list, ndarray)):
        return list(map(lambda x1, x2: x1 / x2, arr1, arr2))

    return list(map(lambda x1: x1 / arr2, arr1))


def power(arr, power):
    """
    This function raises an array to a power.

    :param arr: The array to raise to the power.
    :param power: The power to raise the array to.

    :return: A new array containing the result of raising the input array to
             the given power, element-wise.
    """

    return list(map(lambda x: x**power, arr))


def average(arr, weights=None):
    """
    This function calculates the average of an array.

    If weights is not None, it calculates the weighted average of the array.
    If weights is None, it calculates the unweighted average of the array.

    :param arr: The array to calculate the average of.
    :param weights: The weights to use for the weighted average.

    :return: The average of the array.
    """

    if weights is None:
        return sum(arr) / len(arr)

    arr = multiply(arr, weights)
    return sum(arr) / sum(weights)


def append(arr1, arr2):
    """
    This function appends an array to another array.

    :param arr1: The array to append to.
    :param arr2: The array to append.

    :return: A new array containing the concatenation of the two input arrays.
    """

    arr1 = list(arr1)
    arr2 = [arr2]
    return array(arr1 + arr2)


def insert(arr1, index, arr2):
    """
    This function inserts an array or a single value into another array at
    a given index.

    :param arr1: The array to insert into.
    :param index: The index to insert the array at.
    :param arr2: The array to insert. It can also be a single value.

    :return: A new array containing the concatenation of the two input arrays.
    """

    first_part = arr1[:index]
    first_part = list(first_part)

    second_part = arr2
    if not isinstance(second_part, (list, ndarray)):
        second_part = [second_part]

    third_part = arr1[index:]
    third_part = list(third_part)

    res = first_part + second_part + third_part
    res = array(res)

    return res


def printArr(text="", arr=[]):
    """
    This function prints an array to the console.

    :param text: The text to print before the array.
    :param arr: The array to print.
    """

    print()
    title_str = f"{text}[{len(arr)}]"
    title_str += "-" * (80 - len(title_str))
    print(title_str)
    for i, el in enumerate(arr):
        print(f"{i}: {el}")
