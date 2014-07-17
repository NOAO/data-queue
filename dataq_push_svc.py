#! /usr/bin/env python
'''\ 
Read data records from socket and push to queue. 

The checksum provided for each data record is used as an ID.  If the
checksum of two records is the same, we assume the data is. So we can
throw one of them away.

TODO:
- setup as daemon
- trap for everything bad and do something good
'''

import os, sys, string, argparse, logging
import random
import redis
import SocketServer
from dbvars import *

class DataRecordTCPHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        r = self.server.r
        if r.get(readP) == 'off':
            return False

        self.data = self.rfile.readline().strip()
        (fname,checksum,size) = self.data.split() #! specific to our APP

        if r.sismember(rids,checksum) == 1:
            logging.warning(': Record for %s is already in queue.' 
                            +' Ignoring duplicate.', checksum)
        else:
            rec = dict(list(zip(['filename','size'],[fname,int(size)])))
            # add to DB
            r.lpush(aq,checksum)
            r.hmset(checksum,rec)
            r.sadd(rids,checksum) 
            r.save()    
            self.wfile.write(self.data.upper())

##############################################################################
def main():
    #! print('EXECUTING: %s\n\n' % (string.join(sys.argv)))
    parser = argparse.ArgumentParser(
        version='1.0.3',
        description='Read data from socket and push to Data Queue',
        epilog='EXAMPLE: %(prog)s --host localhost --port 9988'
        )

    parser.add_argument('--host',  help='Host to bind to',
                        default='localhost')
    parser.add_argument('--port',  help='Port to bind to',
                        type=int, default=9988)


    parser.add_argument('--loglevel',      help='Kind of diagnostic output',
                        choices = ['CRTICAL','ERROR','WARNING','INFO','DEBUG'],
                        default='WARNING',
                        )
    args = parser.parse_args()

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel) 
    logging.basicConfig(level = log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M'
                        )
    logging.debug('Debug output is enabled!!')
    ######################################################################

    server = SocketServer.TCPServer((args.host, args.port),
                                    DataRecordTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.r = redis.StrictRedis()
    server.serve_forever()

if __name__ == '__main__':
    main()
