"""
Copyright 2018 Goldman Sachs.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.

Chart Service will attempt to make public functions (not prefixed with _) from this module available. Such functions
should be fully documented: docstrings should describe parameters and the return value, and provide a 1-line
description. Type annotations should be provided for parameters.

Econometrics timeseries library is for standard economic and time series analytics operations, including returns,
diffs, lags, volatilities and other numerical operations which are generally finance-oriented
"""


import math
from .statistics import *
from ..errors import *

# Return types
_SIMPLE = "SIMPLE"
_LOG = "LOG"

# Annualization factors
_DAILY = 252
_WEEKLY = 52
_SEMI_MONTHLY = 26
_MONTHLY = 12
_QUARTERLY = 4
_ANNUALLY = 1


def _get_annualization_factor(series):

    prev_idx = series.index[0]
    prev_value = series[0]
    distances = []
    r = []  # returns
    for idx, value in series.iloc[1:].iteritems():
        d = (idx - prev_idx).days
        if d == 0:
            raise MqValueError('multiple data points on same date')
        distances.append(d)
        r.append(value / prev_value - 1)
        prev_idx = idx
        prev_value = value

    average = numpy.average(distances)
    if average < 2.1:
        factor = _DAILY
    elif average <= 6:
        factor = _WEEKLY + ((6 - average) * (_DAILY - _WEEKLY) / 3.9)
    elif average < 8:
        factor = _WEEKLY
    elif average <= 14:
        factor = _SEMI_MONTHLY + ((14 - average) * (_WEEKLY - _SEMI_MONTHLY) / 6)
    elif average < 17:
        factor = _SEMI_MONTHLY
    elif average <= 25:
        factor = _MONTHLY + ((25 - average) * (_SEMI_MONTHLY - _MONTHLY) / 8)
    elif average < 35:
        factor = _MONTHLY
    elif average <= 85:
        factor = _QUARTERLY + ((85 - average) * (_MONTHLY - _QUARTERLY) / 50)
    elif average < 97:
        factor = _QUARTERLY
    elif average <= 364:
        factor = _ANNUALLY + ((364 - average) * (_QUARTERLY - _ANNUALLY) / 279)
    elif average < 386:
        factor = _ANNUALLY
    else:
        raise MqValueError('data points are too far apart')
    return factor


def annualize(series):
    """
    Annualize series based on observation periods. Will attempt to determine the observation frequency automatically
    (e.g. daily, weekly), and then apply the corresponding annualization factor, e.g. sqrt(252), sqrt(52)
    :param series: time series of prices
    :return: date-based time series of annualized values
    """

    factor = _get_annualization_factor(series)
    return series * math.sqrt(factor)


def lag(series, observations=1):
    """
    Lag timeseries by a specified number of observations
    :param series: time series of prices
    :param observations: number of observations to lag series
    :return: date-based time series of return
    """

    # Determine how we want to handle observations prior to start date

    return series.shift(-observations)


lag.__annotations__ = {'series': pd.Series, 'observations': int, 'return': pd.Series}


def returns(series, ret_type=_SIMPLE, naiszero=1):
    """
    Calculate returns of a given price series
    :param series: time series of prices
    :param ret_type: returns type (simple, log)
    :param naiszero: returns zero rather than NaN for lagged dates
    :return: date-based time series of return
    """

    if series.size < 1:
        return series

    if ret_type is _SIMPLE:
        ret_series = series/series.shift(1) - 1
    elif ret_type is _LOG:
        log_s = series.apply(math.log)
        ret_series = log_s-log_s.shift(1)
    else:
        raise MqValueError('Unknown returns type (use simple / log)')

    # Ensures prod(1+returns(series)) == index(series
    if naiszero:
        ret_series[0] = 0

    return ret_series


returns.__annotations__ = {'series': pd.Series, 'type': str, 'naiszero': bool, 'return': pd.Series}


def prices(series, initial=1, ret_type=_SIMPLE):
    """
    Calculate price levels from a given returns series
    :param series: time series of prices
    :param initial: initial price level
    :param ret_type: returns type (simple, log)
    :return: date-based time series of return
    """

    if series.size < 1:
        return series

    if ret_type is _SIMPLE:
        return product(1+series) * initial
    elif ret_type is _LOG:
        return product(series.apply(math.exp)) * initial
    else:
        raise MqValueError('Unknown returns type (use simple / log)')


prices.__annotations__ = {'series': pd.Series, 'initial': int, 'type': str, 'return': pd.Series}


def diff(series, observations=1, naiszero=1):
    """
    Calculate differences of a given timeseries
    :param series: time series of prices
    :param observations: number of observations
    :param naiszero: returns zero rather than NaN for lagged dates
    :return: date-based time series of return
    """

    if series.size < 1:
        return series

    ret_series = series - series.shift(observations)

    # Ensures 1+sum(diff(s)) == s
    if naiszero:
        ret_series[0:observations] = 0

    return ret_series


diff.__annotations__ = {'series': pd.Series, 'observations': int, 'naiszero': bool, 'return': pd.Series}


def index(x):
    """
    Multiplicative series normalization. Divides every value in x by the initial value of x.
    :param x: time series
    :return: normalized time series
    """
    return x / x[0]


index.__annotations__ = {'x': pd.Series, 'return': pd.Series}


def volatility(series, window=0):
    """
    Calculate rolling annualized realized volatility of a given price series
    :param series: time series of prices
    :param window: number of observations
    :return: date-based time series of return
    """
    window = window or series.size

    if series.size < 1:
        return series

    return annualize(standard_deviation(returns(series), window))


volatility.__annotations__ = {'series': pd.Series, 'window': int, 'return': pd.Series}


def correlation(series1, series2, window=0):
    """
    Calculate rolling correlation of two price series
    :param series1: time series of prices
    :param series2: time series of prices
    :param window: number of observations
    :return: date-based time series of return
    """
    window = window or series1.size

    if series1.size < 1:
        return series1

    ret_1 = returns(series1)
    ret_2 = returns(series2)

    return ret_1.rolling(window, 0).corr(ret_2)


correlation.__annotations__ = {'series1': pd.Series, 'series2': pd.Series, 'window': int, 'return': pd.Series}