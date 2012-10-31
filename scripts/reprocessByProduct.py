#!/usr/bin/env python2.6


"""
go through the DB and add all the files that are a certain product and put then onto the
processqueue so that the next ProcessQueue -p will run them
"""




from optparse import OptionParser

from dateutil import parser as dup

import dbprocessing.DBlogging as DBlogging
import dbprocessing.dbprocessing as dbprocessing


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-s", "--startDate", dest="startDate", type="string",
                      help="Date to start reprocessing (e.g. 2012-10-02)", default=None)
    parser.add_option("-e", "--endDate", dest="endDate", type="string",
                      help="Date to end reprocessing (e.g. 2012-10-25)", default=None)
    parser.add_option("", "--force", dest="force", type="int",
                      help="Force the reprocessing, speicify which version number {0},{1},{2}", default=None)

    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")

    if options.startDate is not None:
        startDate = dup.parse(options.startDate)
    else:
        startDate = None
    if options.endDate is not None:
        endDate = dup.parse(options.endDate)
    else:
        endDate = None

    db = dbprocessing.ProcessQueue('~ectsoc/RBSP_processing.sqlite')

    if options.force is not None:
        if options.force not in [0,1,2]:
            parser.error("invalid force option [0,1,2]")
        num = db.reprocessByProduct(args[0], startDate=startDate, endDate=endDate, incVersion=options.force)
    else:
        num = db.reprocessByProduct(args[0], startDate=startDate, endDate=endDate)

    print('Added {0} files to be reprocessed for product {1}'.format(num, args[0]))
    DBlogging.dblogger.info('Added {0} files to be reprocessed for product {1}'.format(num, args[0]))


