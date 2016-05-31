# -*- coding: utf-8 -*-
"""
Class to hold random utilities of use throughout this code
"""
from __future__ import print_function

import collections
import datetime
import os
import re
import sys

import dateutil.rrule  # do this long so where it is from is remembered

from . import Version


def dateForPrinting(dt=None, microseconds=False, brackets='[]'):
    """
    Return a string of the date format for printing on the screen, if dt is None return now.

    Parameters
    ----------
    dt : datetime.datetime, optional
        The datetime object to format, defaults to now()
    microseconds : bool, optional
        Should the microseconds be included, default False
    brackets : str, optional
        Which brackets to encase the time in, default ('[', ']')

    Returns
    -------
    str
       Iso formatted string

    Examples
    --------
    >>> from dbprocessing.Utils import dateForPrinting
    >>> print("{0} Something occurred".format(dateForPrinting()))
    [2016-03-22T10:51:45]  Something occurred
    """
    if dt is None:
        dt = datetime.datetime.now()
    if not microseconds:
        dt = dt.replace(microsecond=0)
    return brackets[0] + dt.isoformat() + brackets[1]


def progressbar(count, blocksize, totalsize, text='Download Progress'):
    """
    print a progress bar with urllib.urlretrieve reporthook functionality, taken from spacepy

    Parameters
    ----------
    count : float
        The current count of the progressbar
    blocksize : float
        The size of each block (mostly useful for file downloads)
    totalsize : float
        The total size of the job, progress is count*blocksize*100/totalsize
    text : str, optional
        The text to print in the progressbar

    Returns
    -------
    None
        No return, but things are printed to the screen

    Examples
    --------
    >>> import spacepy.toolbox as tb
    >>> import urllib
    >>> urllib.urlretrieve(config['psddata_url'], PSDdata_fname, reporthook=tb.progressbar)
    """
    percent = int(count * blocksize * 100 / totalsize)
    sys.stdout.write("\r" + text + " " + "...%d%%" % percent)
    if percent == 100: print('\n')
    sys.stdout.flush()


# from http://stackoverflow.com/questions/434287/what-is-the-most-pythonic-way-to-iterate-over-a-list-in-chunks
def chunker(seq, size):
    """
    Return a long iterable in a tuple of shorter lists. Taken from from http://stackoverflow.com/questions/434287/what-is-the-most-pythonic-way-to-iterate-over-a-list-in-chunks

    Parameters
    ----------
    seq : iterable
        Iterable to split up
    size : int
        Size of each split in the output, last one has the remaining elements of `seq`

    Returns
    -------
    tuple
        A tuple of lists of the iterable `seq` split into len(seq)/`size` segments

    """
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))


def unique(seq):
    """
    Take a list and return only yhr unique elements in the same order

    Parameters
    ----------
    seq : list
        List to return the unique elements of

    Returns
    -------
    list
        List with only the unique elements

    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if x not in seen and not seen_add(x)]


def expandDates(start_time, stop_time):
    """
    Given a start and a stop date make all the dates in between, inclusive on the ends

    Parameters
    ----------
    start_time : datetime.datetime
        Date to start the list
    stop_time : datetime.datetime
        Date to end the list, inclusive

    Returns
    -------
    list
        All the dates between `start_time` and `stop_time`

    """
    return dateutil.rrule.rrule(dateutil.rrule.DAILY, dtstart=start_time, until=stop_time)


def daterange_to_dates(daterange):
    """
    given a daterange return the dat objects for all days in the range

    Parameters
    ----------
    seq : iterable of datetime.datetime
        Start and stop dates

    Returns
    -------
    list
        All the dates between `daterange`[0] and `daterange`[1]

    """
    return [daterange[0] + datetime.timedelta(days=val) for val in
            xrange((daterange[1] - daterange[0]).days + 1)]


def parseDate(inval):
    """
    given a date of the for yyyy-mm-dd parse to a datetime
    If the format is wrong ValueError is raised. This is just
    a wrapper around datetime.datetime.strptime

    Parameters
    ----------
    inval : str
        String date representation of the form YYYY-MM-DD

    Returns
    -------
    datetime.datetime
        datetime object parsed from the string

    """
    return datetime.datetime.strptime(inval, '%Y-%m-%d')


def parseVersion(inval):
    """
    given a format of the form x.y.z parse to a Version, this is a wrapper
    around Version.Version.fromString()

    Parameters
    ----------
    inval : str
        String Version representation of the form xx.yy.zz

    Returns
    -------
    Version.Version
        Version object parsed form the string

    """
    return Version.Version.fromString(inval)


def flatten(l):
    """
    flatten an irregularly nested list of lists
    thanks SO: http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python
    """
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el


def toBool(value):
    if value in ['True', 'true', True, 1, 'Yes', 'yes']:
        return True
    else:
        return False


def toNone(value):
    if value in ['', 'None', 'none', 'NONE']:
        return None
    else:
        return value


def strargs_to_args(strargs):
    """
    read in the arguments string from the db and change to a dict
    """
    if strargs is None:
        return None
    kwargs = {}
    if isinstance(strargs, (list, tuple)):  # we have multiple to deal with
        # TODO why was this needed?
        if len(strargs) == 1:
            kwargs = strargs_to_args(strargs[0])
            return kwargs
        for val in strargs:
            tmp = strargs_to_args(val)
            for key in tmp:
                kwargs[key] = tmp[key]
        return kwargs
    try:
        for val in strargs.split():
            tmp = val.split('=')
            kwargs[tmp[0]] = tmp[1]
    except (AttributeError, KeyError, IndexError):  # it was None
        pass
    return kwargs


def dirSubs(path, filename, utc_file_date, utc_start_time, version, dbu=None):
    """
    do any substitutions that are needed to put ting in the right place
    # Honored database substitutions used as {Y}{MILLI}{PRODUCT}
    #	Y: 4 digit year
    #	m: 2 digit month
    #	b: 3 character month (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)
    #	d: 2 digit day
    #	y: 2 digit year
    #	j: 3 digit day of year
    #	H: 2 digit hour (24-hour time)
    #	M: 2 digit minute
    #	S: 2 digit second
    #	VERSION: version string, interface.quality.revision
    #	DATE: the UTC date from a file, same as Ymd
    #   MISSION: the mission name from the db
    #   SPACECRAFT: the spacecraft name from the db
    #   PRODUCT: the product name from the db
    @param dbu:
    """
    if '{INSTRUMENT}' in path or '{SATELLITE}' in path or '{SPACECRAFT}' in path or '{MISSION}' in path or '{PRODUCT}' in path:
        ftb = dbu.getTraceback('File', filename)
        if '{INSTRUMENT}' in path:  # need to replace with the instrument name
            path = path.replace('{INSTRUMENT}', ftb['instrument'].instrument_name)
        if '{SATELLITE}' in path:  # need to replace with the instrument name
            path = path.replace('{SATELLITE}', ftb['satellite'].satellite_name)
        if '{SPACECRAFT}' in path:  # need to replace with the instrument name
            path = path.replace('{SPACECRAFT}', ftb['satellite'].satellite_name)
        if '{MISSION}' in path:
            path = path.replace('{MISSION}', ftb['mission'].mission_name)
        if '{PRODUCT}' in path:
            path = path.replace('{PRODUCT}', ftb['product'].product_name)

    if '{Y}' in path:
        path = path.replace('{Y}', utc_file_date.strftime('%Y'))
    if '{m}' in path:
        path = path.replace('{m}', utc_file_date.strftime('%m'))
    if '{d}' in path:
        path = path.replace('{d}', utc_file_date.strftime('%d'))
    if '{b}' in path:
        months = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct',
                  11: 'Nov', 12: 'Dec'}
        path = path.replace('{b}', months[utc_file_date.month])
    if '{y}' in path:
        path = path.replace('{y}', utc_file_date.strftime('%y'))
    if '{j}' in path:
        path = path.replace('{j}', utc_file_date.strftime('%j'))
    if '{H}' in path:
        path = path.replace('{H}', utc_start_time.strftime('%H'))
    if '{M}' in path:
        path = path.replace('{M}', utc_start_time.strftime('%M'))
    if '{S}' in path:
        path = path.replace('{S}', utc_start_time.strftime('%S'))
    if '{VERSION}' in path:
        if isinstance(version, (unicode, str)):
            version = Version.Version.fromString(version)
        path = path.replace('{VERSION}', '{0}'.format(str(version)))
    if '{DATE}' in path:
        path = path.replace('{DATE}', utc_file_date.strftime('%Y%m%d'))
    return path


def split_code_args(args):
    """
    split a string with a bunch of command line arguments into a list
    as needed by Popen

    This is different thatn just split() since we have to keep options
    together with the flags
    e.g. "code -n hello outfile" -> [code, -n hello, outfile]
    """
    # just do the spit
    ans = args.split()
    # loop through and see if an index has just a -x (any letter)
    for ii, v in enumerate(ans):
        if re.match(r'\-\S', v):  # found a single letter option
            ans[ii] = ans[ii] + " " + ans[ii+1]
            del ans[ii+1]

    return ans


def processRunning(pid):
    """
    given a PID see if it is currently running

    @param pid: a pid
    @type pid: long

    @return: True if pid is running, False otherwise
    @rtype: bool

    @author: Brandon Craig Rhodes
    @organization: Stackoverflow
    http://stackoverflow.com/questions/568271/check-if-pid-is-not-in-use-in-python

    @version: V1: 02-Dec-2010 (BAL)
    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True
