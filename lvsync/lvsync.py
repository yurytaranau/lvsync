#!/usr/bin/env python
# coding: utf8

from optparse import OptionParser
from struct import pack,unpack
import subprocess
import sys
import os
import io


class Helper(object):

    def __htonq(self, value):
        #
        # convert little-endian to big-endian
        #
        if sys.byteorder == 'big':
            # convert to big-endian (network)
            return unpack('>Q', pack('Q', value))
        elif sys.byteorder == 'little':
            return value
        else:
            print 'I don\'t know what must I do with this order - %s' % sys.byteorder
            sys.exit(1)

    def __ntohq(self, value):
        return __htonq(value)

    def find_dm_path(self, path, NEED_COW=False, NEED_ORIGIN=False):
        #
        # Return device-mapper path for block device
        #        
        sub = subprocess.Popen(
            ['lvs', '--noheadings', '%s' % path],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=open(os.devnull, 'w'),
        )
        output = sub.stdout.readline().split()
        lv_name = output[0]
        vg_name = output[1]
        if NEED_ORIGIN:
            lv_name = output[4]
        sub.wait()
        if sub.returncode != 0:
            print 'Couldn\'t find volume %s' % path
            sys.exit(1)
        # generate dm-path
        dm_path = '/dev/mapper/%(vg_name)s-%(origin_name)s' % {
            'vg_name': vg_name,
            'origin_name': lv_name.replace('-', '--')
        }
        if NEED_COW:
            dm_path += '-cow'
        return dm_path

    def find_diff_map(self, snapshot):
        #
        # Find different chunks between current device and snapshot
        #
        diff_map = []
        with open(snapshot, 'r') as cow:
            # read header (first 16 bytes)
            magic, valid, version, chunk_size = unpack('IIII', cow.read(16))
            if magic != 0x70416e53: 
                # incorrent snap magic
                print 'Invalid snapshot path: %s' % snapshot
                sys.exit(1)
            if valid != 1: 
                # invalid snapshot
                print 'Snapshot marked as invalid: %s' % snapshot
                sys.exit(1)
            if version != 1:
                print 'Unsupported snapshot version: %s' % version
                sys.exit(1)

            # chunk size in bytes
            chunk_size = chunk_size * 512
            # skip all header chunk from begin
            cow.seek(chunk_size, 0)
            # check each chunk
            progress = True
            while progress:
                for i in range(0, chunk_size/16):
                    origin_offset, snap_offset = unpack('QQ', cow.read(16))
                    origin_offset = self.__htonq(origin_offset)
                    snap_offset = self.__htonq(snap_offset)
                    #print 'origin offset: %s \t | snapshot offset: %s' % (origin_offset, snap_offset)
                    if snap_offset == 0:
                        progress = False
                        break
                    diff_map.append(origin_offset)
                cow.seek(chunk_size * chunk_size/16, 1)

        # need convert this block map to byte-range or no??
        cow.close()
        return diff_map, chunk_size

    def send_diff(self, origin_volume, destination, diff_map, chunk_size):
        #
        # Send chunk changes to remote volume
        #
        if len(diff_map) == 0: # diff_map empty
            print "no difference between original volume and snapshot. Exiting."
            sys.exit(0)

        # establish connection with remote host
        # destination = (remote_host, remote_volume)
        dst = io.os.popen('ssh %s lvsync -s -d %s' % destination, 'w')

        # find data from origin
        with open(origin_volume, 'r') as origin:
            for offset in diff_map:
                origin.seek(offset * chunk_size, 0)
                data = origin.read(chunk_size)
                header = pack('QI', self.__htonq(offset), chunk_size)
                dst.write(header)
                dst.write(data)
                dst.flush()
        print "Successfully sended %s chunks. Done" % len(diff_map)


class MainHandler(object):

    def __init__(self):
        self.helper = Helper()

    def client(self):
        #
        # Run lvsync
        #
        src_volume = sys.argv[1]
        dst_server, dst_volume = sys.argv[2].split(':')

        # find origin and snapshot-cow device-mapper path
        origin = self.helper.find_dm_path(src_volume, NEED_ORIGIN=True)
        snapshot = self.helper.find_dm_path(src_volume, NEED_COW=True)
        print "origin: %s, snapshot: %s" % (origin, snapshot)
        sync_command = '''dd if=%(source)s bs=1M | pv -ptrb | ssh %(server)s dd of=%(remote)s bs=1M''' % {
            'source': src_volume,
            'server': dst_server,
            'remote': dst_volume
        }
        # if need send snapshot to remote server (vm can be running)
        SEND_SNAPSHOT = raw_input('''
            First need to send created snapshot to remote server.
            Type 'no' if you has already sent volume manually).
            Command: \033[1;32m%s\033[1;m
            Run sync? [yes/no]: ''' % sync_command)

        if SEND_SNAPSHOT == 'yes':
            # run sync command
            os.system(sync_command)

        # get diff map (changed chunk addresses)
        diff_map, chunk_size = self.helper.find_diff_map(snapshot)
        SEND_DIFF = raw_input('''
            Found %s changed chunks.
            Send chunks to remote volume? [yes/no]: ''' % len(diff_map))
        
        if SEND_DIFF == 'yes':
            # send changed chuncks to remote server
            self.helper.send_diff(origin, (dst_server, dst_volume), diff_map, chunk_size)

    def server(self, destination):
        #
        # Server mode. Accept and apply data from stdin
        #
        dst_remote = self.helper.find_dm_path(destination) # open remote device
        with open(dst_remote, 'w+') as remote:
            progress = True
            while progress:
                header = sys.stdin.read(12)
                if len(header) != 12: # end of data
                    progress = False
                    break
                # unpack header
                offset, chunk_size = unpack('QI', header)
                #offset = self.helper.__ntohq(offset)
                data = sys.stdin.read(chunk_size)
                # move to chunk
                remote.seek(offset * chunk_size, 0)
                remote.write(data)
        remote.close()


if __name__ == '__main__':
    parser = OptionParser(usage='%prog [options]')
    parser.add_option('-s', '--server', dest='server', action='store_true', help='Server mode', default='False')
    parser.add_option('-d', '--destination', dest='destination', help='Remote logical volume')
    (options, args) = parser.parse_args()

    main = MainHandler()
    if options.server == True:
        # run lvsync in server mode
        main.server(options.destination)
    else:
        if len(sys.argv) < 3:
            print 'Usage: lvsync /dev/<vg>/<snap-name> root@<server>:/dev/<vg>/<lv-name>'
            sys.exit(1)
        # client mode
        main.client()