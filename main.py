import networktables as nt
import time
import threading

import os
import random
from typing import List
import pygame as pg
import json
import logging

GRAPHSIZE = (17.548, 8.062)
SCALE = 40
SCREENRECT = pg.Rect(0, 0, GRAPHSIZE[0]*SCALE+20, GRAPHSIZE[1]*SCALE+20)

BLUE = pg.Color(0,0,255)
GREEN = pg.Color(0,255,0)
RED = pg.Color(255,0,0)
YELLOW = pg.Color(255,255,0)

COLORS = [RED, GREEN, YELLOW, BLUE]
CIDX = 0
COLORREG = {}

def getColor(k):
    if k in COLORREG:
        return COLORREG[k]
    else:
        COLORREG[k] = COLORS.pop(0)
        return COLORREG[k]

class Data:
    def __init__(self, server, spit, restime=1):
        self.inst = nt.NetworkTablesInstance.getDefault()
        self.table = self.inst.getTable("SmartDashboard")
        self.inst.startClient("qdb")
        self.inst.setServer(server)
        self.restime = restime
        self.thread = threading.Thread(target=self.start)
        self.data = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.spit = spit
        self.running = True

    def run(self): 
        self.thread.start()

    def start(self):
        cflag = False
        while self.running:
            if not self.inst.isConnected():
                cflag = False
                logging.warning("NT not connected!")
            elif self.inst.isConnected() and not cflag:
                logging.info("NT connected")
                cflag = True

            time.sleep(self.restime)
            self.data = json.loads(self.table.getString("qdbpoints", "{}"))
            self.spit(self.data)
            

    def kill(self):
        self.running = False
        self.join()

    def join(self):
        self.thread.join()


class Graph:
    def __init__(self):
        self.thread = threading.Thread(target=self.start)
        self.running = True
        self.wait = False
        self.rawpointclouds = {}

    def start(self):
        pg.init()
        bestdepth = pg.display.mode_ok(SCREENRECT.size, 0, 32)
        screen = pg.display.set_mode(SCREENRECT.size, 0, bestdepth)

        pg.display.set_caption("qdb")
        pg.mouse.set_visible(0)

        background = pg.Surface(SCREENRECT.size)
        background.fill(pg.Color(0,0,0))

        screen.blit(background, (0, 0))
        pg.display.flip()

        all = pg.sprite.RenderUpdates()

        clock = pg.time.Clock()
        # pointclouds = [Pointcloud(all, points=pc['points'], color=pc['color']) for pc in self.rawpointclouds.values()]

        while self.running: 
            if self.wait:
                continue
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return
                if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    return

            # pg.draw.circle(screen, RED, (50,50), 5)
            # all.clear(screen, background)
            background.fill(pg.Color(0,0,0))

            for points in self.rawpointclouds.values():
                for point in points['points']:
                    pg.draw.circle(background, points['color'], (point[0]*SCALE+120, SCREENRECT.height - (point[1]*SCALE+120)), 5)

            screen.blit(background, (0, 0))
            pg.display.flip()

            clock.tick(60)
        pg.quit()

    def setd(self, data: dict):
        self.wait = True
        self.rawpointclouds = {}
        for k,v in data.items():
            self.rawpointclouds[k] = {'color': getColor(k), 'points': v}
        self.wait = False

    def run(self):
        self.thread.start()

    def kill(self):
        self.running = False
        self.join()

    def join(self):
        self.thread.join()



def main():
    graph = Graph()
    graph.run()

    dataprovider = Data("127.0.0.1", graph.setd, 0.05)
    dataprovider.run()
    graph.join()
    dataprovider.kill()

if __name__ == "__main__":
    main()

