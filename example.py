#! /usr/bin/env python

import sys
import time

import HPMA115

def main():
    if len(sys.argv) != 2:
        print("Usage: ./example.py /dev/ttyS0")
        return

    hpm = HPMA115.HPMA115C0(sys.argv[1])
    hpm.start_measurement()
    try:
        while True:
            sam = hpm.sample()
            print(sam)
            time.sleep(1)
    except:
        pass
    hpm.stop_measurement()


if __name__ == "__main__":
    main()
