# -*- coding: utf-8 -*-

from __future__ import division

import Image
import ImageDraw
import cStringIO
import math
import operator
import urllib

from module.plugins.captcha.OCR import OCR


class ImageSequence:

    def __init__(self, im):
        self.im = im

    def __getitem__(self, ix):
        try:
            if ix:
                self.im.seek(ix)
            return self.im
        except EOFError:
            raise IndexError # end of sequence


class CircleCaptcha(OCR):
    __name__    = "CircleCaptcha"
    __type__    = "ocr"
    __version__ = "1.00"

    __description__ = """Circle captcha ocr plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Sasch", "gsasch@gmail.com")]


    _DEBUG = False
    pointsofcirclefound = []

    BACKGROUND = 250
    BLACKCOLOR = 5


    def cleanImage(self, im, pix):
        cleandeep = 1

        imageheight = range(1,int(im.size[1]))
        imagewidth = range(1,int(im.size[0]))
        howmany = 0
        curcolor = self.BACKGROUND

        for y in imageheight:
            jump = True
            howmany = 0
            for x in imagewidth:
                curpix = pix[x,y]

                if curpix > self.BACKGROUND:
                    if howmany <= cleandeep and howmany > 0:
                        # clean pixel
                        for ic in range(1,cleandeep+1):
                            if x -ic > 0:
                                pix[x-ic,y] = self.BACKGROUND
                    jump = False
                    howmany = 0
                    curcolor = curpix
                    # print (x, y), jump,2
                else:
                    if howmany == 0:
                        # found pixel
                        jump = True
                        howmany = howmany + 1
                        curcolor = curpix
                        # print (x, y), jump,2
                    else:
                        howmany = howmany + 1
            if howmany == 1:
                # clean pixel
                pix[x-1,y] = self.BACKGROUND

        curcolor = self.BACKGROUND
        for x in imagewidth:
            jump = True
            howmany = 0
            for y in imageheight:
                curpix = pix[x,y]
                # if jump == True:
                if curpix > self.BACKGROUND:
                    if howmany <= cleandeep and howmany > 0:
                        # clean pixel
                        for ic in range(1,cleandeep+1):
                            # raw_input('2'+str(ic))
                            if y-ic > 0:
                                pix[x,y-ic] = self.BACKGROUND
                    jump = False
                    howmany = 0
                    curcolor = curpix
                    # print (x, y), jump
                else:
                    if howmany == 0:
                        # found pixel
                        jump = True
                        howmany = howmany + 1
                        curcolor = curpix
                        # print (x, y), jump
                    else:
                        howmany = howmany + 1
            if howmany == 1:
                # clean pixel
                pix[x-1,y] = self.BACKGROUND

        # return -1


    def findFirstPixelX(self, im, pix, curx, cury, color = -1, ExitWithBlack = False):
        imageheight = range(1,int(im.size[1]))
        imagewidth = range(curx+1,int(im.size[0]))
        jump = True
        newx = (-1,-1)
        blackfound = 0
        for x in imagewidth:
            curpix = pix[x,cury]

            if curpix < self.BLACKCOLOR:
                blackfound = blackfound + 1
                if ExitWithBlack == True and blackfound >= 3:
                    break;    #exit if found black
                else:
                    continue;

            if curpix >= self.BACKGROUND:
                # found first pixel white
                jump = False
                continue;

            if (curpix < self.BACKGROUND and color == -1) or (curpix == color and color > -1):
                if jump == False:
                    # found pixel
                    curcolor = curpix
                    newx = x, curcolor
                    break;

        return newx


    def findLastPixelX(self, im, pix, curx, cury, color = -1, ExitWithBlack = False):
        imageheight = range(1,int(im.size[1]))
        imagewidth = range(curx+1,int(im.size[0]))
        newx = (-1,-1)
        blackfound = 0
        for x in imagewidth:
            curpix = pix[x,cury]

            if curpix < self.BLACKCOLOR:
                blackfound = blackfound + 1
                if ExitWithBlack == True and blackfound >= 3:
                    break;    #exit if found black
                else:
                    continue;

            if curpix >= self.BACKGROUND:
                if newx != (-1,-1):
                    # found last pixel and the first white
                    break;

            if (curpix < self.BACKGROUND and color == -1) or (curpix == color and color > -1):
                # found pixel
                curcolor = curpix
                newx = x, curcolor

        return newx


    def findLastPixelY(self, im, pix, curx, cury, DownToUp, color = -1, ExitWithBlack = False):
        if DownToUp == False:
            imageheight = range(int(cury)+1,int(im.size[1])-1)
        else:
            imageheight = range(int(cury)-1,1,-1)
        imagewidth = range(int(curx),int(im.size[0]))
        newy = (-1,-1)
        blackfound = 0
        for y in imageheight:
            curpix = pix[curx,y]

            if curpix < self.BLACKCOLOR:
                blackfound = blackfound + 1
                if ExitWithBlack == True and blackfound >= 3:
                    break;    #exit if found black
                else:
                    continue;

            if curpix >= self.BACKGROUND:
                if newy != (-1,-1):
                    # found last pixel and the first white
                    break;

            if (curpix < self.BACKGROUND and color == -1) or (curpix == color and color > -1):
                # found pixel
                curcolor = curpix
                newy = y, color

        return newy


    def findCircle(self, pix, x1, y1, x2, y2, x3, y3):
        # trasposizione coordinate
        # A(0,0) B(x2-x1,y2-y1) C(x3-x1,y3-y1)
        # x**2+y**2+ax+bx+c=0
        p1 = (0,0)
        p2 = (x2-x1,y2-y1)
        p3 = (x3-x1,y3-y1)

        # 1
        c=0
        # 2
        # p2[0]**2+a*p2[0]+c=0
        # a*p2[0]=-1*(p2[0]**2-c)
        # a=(-1*(p2[0]**2-c))/p2[0]
        a=(-1*(p2[0]**2-c))/p2[0]
        # 3
        # p3[0]**2+p3[1]**2+a*p3[0]+b*p3[1]+c=0
        # b*p3[1]=-(p3[0]**2+p3[1]**2+a*p3[0]+c)
        # b=(-1 * (p3[0]**2+p3[1]**2+a*p3[0]+c)) / p3[1]
        b=(-1 * (p3[0]**2+p3[1]**2+a*p3[0]+c)) / p3[1]

        r=math.floor(math.sqrt((-1*(a/2))**2+(-1*(b/2))**2))
        cx=math.floor((-1*(a/2))+x1)
        cy=math.floor((-1*(b/2))+y1)

        return cx,cy,r


    def verifyCircleNew(self, im, pix, c):
        """
            This is the MAIN function to recognize the circle
            returns:
                1 -> Found closed circle
                0 -> Found open circle
                -1 -> Not found circle
                -2 -> Found black position then leave position
        """

        imageheight = range(int(c[1]-c[2]),int(c[1]+c[2]))
        imagewidth = range(int(c[0]-c[2]),int(c[0]+c[2]))

        min_ray = 15
        max_ray = 30
        exactfind = False

        howmany = 0
        missing = 0
        missingconsecutive = 0
        missinglist = []
        minX = 0; maxX = 0; minY = 0; maxY = 0
        pointsofcircle = []

        if (c[2] < min_ray) or (c[2] > max_ray):
            return -1

        # check cardinal points (at least 3) (if found i have to leave this position)
        if pix[c[0] + c[2],c[1]] < self.BLACKCOLOR:
            return -2;
        if pix[c[0] - c[2],c[1]] < self.BLACKCOLOR:
            return -2;
        if pix[c[0],c[1] + c[2]] < self.BLACKCOLOR:
            return -2;
        if pix[c[0],c[1] - c[2]] < self.BLACKCOLOR:
            return -2;

        cardinalpoints = 0
        if self.verifyPoint(im, pix,c[0] + c[2],c[1],True) == 1:
            cardinalpoints = cardinalpoints + 1
        if self.verifyPoint(im, pix,c[0] + c[2],c[1],False) == -1:
            return -2;
        if self.verifyPoint(im, pix,c[0] - c[2],c[1],True) == 1:
            cardinalpoints = cardinalpoints + 1
        if self.verifyPoint(im, pix,c[0] - c[2],c[1],False) == -1:
            return -2;
        if self.verifyPoint(im, pix,c[0],c[1] + c[2],True) == 1:
            cardinalpoints = cardinalpoints + 1
        if self.verifyPoint(im, pix,c[0],c[1] + c[2],False) == -1:
            return -2;
        if self.verifyPoint(im, pix,c[0],c[1] - c[2],True) == 1:
            cardinalpoints = cardinalpoints + 1
        if self.verifyPoint(im, pix,c[0],c[1] - c[2],False) == -1:
            return -2;
        if cardinalpoints < 3:
            return -1;

        for x in imagewidth:
            # Pitagora
            y = int(round(c[1]- math.sqrt(c[2]**2-(c[0]-x)**2)))
            y2= int(round(c[1]+ math.sqrt(c[2]**2-(c[0]-x)**2)))

            howmany = howmany + 2
            if self.verifyPoint(im, pix, x,y,exactfind) == 0:
                missing = missing + 1
                missinglist.append((x,y))
            else:
                pointsofcircle.append((x,y))

            if self.verifyPoint(im, pix, x,y,False) == -1:
                return -2;

            if self.verifyPoint(im, pix, x,y2,exactfind) == 0:
                missing = missing + 1
                missinglist.append((x,y2))
            else:
                pointsofcircle.append((x,y2))

            if self.verifyPoint(im, pix, x,y2,False) == -1:
                return -2;


    def verifyCircle(self, im, pix, c):
        """
            This is the MAIN function to recognize the circle
            returns:
                1 -> Found closed circle
                0 -> Found open circle
                -1 -> Not found circle
                -2 -> Found black position then leave position
        """

        imageheight = range(int(c[1]-c[2]),int(c[1]+c[2]))
        imagewidth = range(int(c[0]-c[2]),int(c[0]+c[2]))

        min_ray = 15
        max_ray = 30
        exactfind = False

        howmany = 0
        missing = 0
        missingconsecutive = 0
        missinglist = []
        minX = 0; maxX = 0; minY = 0; maxY = 0
        pointsofcircle = []

        if (c[2] < min_ray) or (c[2] > max_ray):
            return -1

        # check cardinal points (at least 3) (if found i have to leave this position)
        if pix[c[0] + c[2],c[1]] < self.BLACKCOLOR:
            return -2;
        if pix[c[0] - c[2],c[1]] < self.BLACKCOLOR:
            return -2;
        if pix[c[0],c[1] + c[2]] < self.BLACKCOLOR:
            return -2;
        if pix[c[0],c[1] - c[2]] < self.BLACKCOLOR:
            return -2;

        cardinalpoints = 0
        if self.verifyPoint(im, pix,c[0] + c[2],c[1],True) == 1:
            cardinalpoints = cardinalpoints + 1
        if self.verifyPoint(im, pix,c[0] + c[2],c[1],False) == -1:
            return -2;
        if self.verifyPoint(im, pix,c[0] - c[2],c[1],True) == 1:
            cardinalpoints = cardinalpoints + 1
        if self.verifyPoint(im, pix,c[0] - c[2],c[1],False) == -1:
            return -2;
        if self.verifyPoint(im, pix,c[0],c[1] + c[2],True) == 1:
            cardinalpoints = cardinalpoints + 1
        if self.verifyPoint(im, pix,c[0],c[1] + c[2],False) == -1:
            return -2;
        if self.verifyPoint(im, pix,c[0],c[1] - c[2],True) == 1:
            cardinalpoints = cardinalpoints + 1
        if self.verifyPoint(im, pix,c[0],c[1] - c[2],False) == -1:
            return -2;
        if cardinalpoints < 3:
            return -1;

        for x in imagewidth:
            # Pitagora
            y = int(round(c[1]- math.sqrt(c[2]**2-(c[0]-x)**2)))
            y2= int(round(c[1]+ math.sqrt(c[2]**2-(c[0]-x)**2)))

            howmany = howmany + 2
            if self.verifyPoint(im, pix, x,y,exactfind) == 0:
                missing = missing + 1
                missinglist.append((x,y))
            else:
                pointsofcircle.append((x,y))

            if self.verifyPoint(im, pix, x,y,False) == -1:
                return -2;

            if self.verifyPoint(im, pix, x,y2,exactfind) == 0:
                missing = missing + 1
                missinglist.append((x,y2))
            else:
                pointsofcircle.append((x,y2))

            if self.verifyPoint(im, pix, x,y2,False) == -1:
                return -2;

        for y in imageheight:
            # Pitagora
            x = int(round(c[0]- math.sqrt(c[2]**2-(c[1]-y)**2)))
            x2= int(round(c[0]+ math.sqrt(c[2]**2-(c[1]-y)**2)))

            howmany = howmany + 2
            if self.verifyPoint(im, pix, x,y,exactfind) == 0:
                missing = missing + 1
                missinglist.append((x,y))
            else:
                pointsofcircle.append((x,y))

            if self.verifyPoint(im, pix, x,y,False) == -1:
                return -2;

            if self.verifyPoint(im, pix, x2,y,exactfind) == 0:
                missing = missing + 1
                missinglist.append((x2,y))
            else:
                pointsofcircle.append((x2,y))

            if self.verifyPoint(im, pix, x2,y,exactfind) == -1:
                return -2;

        for p in missinglist:
                # left and bottom
            if (self.verifyPoint(im, pix, p[0]-1, p[1],exactfind) == 1 and \
                self.verifyPoint(im, pix, p[0], p[1]+1,exactfind) == 1):
                missing = missing - 1
            elif (self.verifyPoint(im, pix, p[0]-1, p[1],exactfind) == 1 and \
                self.verifyPoint(im, pix, p[0], p[1]-1,exactfind) == 1):
                missing = missing - 1
                # right and bottom
            elif (self.verifyPoint(im, pix, p[0]+1, p[1],exactfind) == 1 and \
                self.verifyPoint(im, pix, p[0], p[1]+1,exactfind) == 1):
                missing = missing - 1
                # right and up
            elif (self.verifyPoint(im, pix, p[0]+1, p[1],exactfind) == 1 and \
                self.verifyPoint(im, pix, p[0], p[1]-1,exactfind) == 1):
                missing = missing - 1

            if (p[0], p[1]+1) in missinglist or \
                (p[0], p[1]-1) in missinglist or \
                (p[0]+1, p[1]) in missinglist or \
                (p[0]-1, p[1]) in missinglist or \
                (p[0]+1, p[1]+1) in missinglist or \
                (p[0]-1, p[1]+1) in missinglist or \
                (p[0]+1, p[1]-1) in missinglist or \
                (p[0]-1, p[1]-1) in missinglist or \
                self.verifyPoint(im, pix, p[0], p[1],False) == 1:
                missingconsecutive = missingconsecutive + 1
            # else:
            #    pix[p[0], p[1]] = 0

        if missing / howmany > 0:
            indice = c[2] * (missing / howmany)
        else:
            indice = 0

        if len(missinglist) > 0:
            minX = min(missinglist, key=operator.itemgetter(0))[0]
            maxX = max(missinglist, key=operator.itemgetter(0))[0]

            minY = min(missinglist, key=operator.itemgetter(1))[1]
            maxY = max(missinglist, key=operator.itemgetter(1))[1]

        # Assial Simmetric
        if self._DEBUG == True:
            print "Center: " + str(c)
            print "Missing: " + str(missing)
            print "Howmany: " + str(howmany)
            print "Ratio: " + str(missing / howmany)
            print "Missing consecutives: " + str(missingconsecutive)
            print "Missing X lenght: " + str(minX) + ":" + str(maxX)
            print "Missing Y lenght: " + str(minY) + ":" + str(maxY)
            print "Ratio without consecutives: " + str((missing - missingconsecutive) / howmany)
            print "List missing: " + str(missinglist)

        # Lenght of missing cannot be over 75% of diameter

        if maxX - minX >= c[2] * 2 * 0.75:
            return -1;
        if maxY - minY >= c[2] * 2 * 0.75:
            # raw_input('tro')
            return -1;
        """
        # Lenght of missing cannot be less 10% of diameter
        if maxX - minX < c[2] * 2 * 0.10 and maxY - minY < c[2] * 2 * 0.10:
            return -1;
        """

        if missing / howmany > 0.25 or \
            missingconsecutive >= (howmany / 4) * 2 or \
            howmany < 80:
            return -1;
        # elif missing / howmany < 0.10:
        elif missing == 0:
            self.pointsofcirclefound.extend(pointsofcircle)
            return 1;
        elif (missing - missingconsecutive) / howmany < 0.20:
            return 0;
        else:
            self.pointsofcirclefound.extend(pointsofcircle)
            return 1;


    def verifyPoint(self, im, pix, x,y,exact,color = -1):
        # Verify point
        result = 0

        if x < 0 or x >= im.size[0]:
            return result;
        if y < 0 or y >= im.size[1]:
            return result;

        curpix = pix[x,y]
        if (curpix == color and color > -1) or (curpix < self.BACKGROUND and color == -1):
            if curpix > self.BLACKCOLOR:
                result = 1
            else:
                result = -1

        # Verify around
        if (exact == False):
            if x + 1 < im.size[0]:
                curpix = pix[x+1,y]
                if (curpix == color and color > -1) or (curpix < self.BACKGROUND and color == -1):
                    if curpix > self.BLACKCOLOR:
                        result = 1
                if curpix <= self.BLACKCOLOR:
                    result = -1

            if x > 0:
                curpix = pix[x-1,y]
                if (curpix == color and color > -1) or (curpix < self.BACKGROUND and color == -1):
                    if curpix > self.BLACKCOLOR:
                        result = 1
                if curpix <= self.BLACKCOLOR:
                    result = -1
        # print str((x,y)) + " = " + str(result);
        return result


    def decrypt(self, img):
        iDebugSaveFile = 0
        mypalette = None
        for im in ImageSequence(img):
            im.save("orig.png", "png")
            if mypalette != None:
                im.putpalette(mypalette)
            mypalette = im.getpalette()
            im = im.convert('L')

            if self._DEBUG == True:
                iDebugSaveFile = iDebugSaveFile + 1
                # if iDebugSaveFile < 7: continue;
                im.save("output" + str(iDebugSaveFile) + ".png", "png")
                raw_input('frame: '+ str(im))

            pix = im.load()

            stepheight = range(1,im.size[1],2)
            # stepheight = range(45,47)
            imagewidth = range(1,im.size[0])
            lstPoints = [] # Declares an empty list for the points
            lstX = [] # CoordinateX
            lstY = [] # CoordinateY
            lstColors = [] # Declares an empty list named lst
            min_distance = 10
            max_diameter = 70

            if self._DEBUG == True:
                imdebug = im.copy()
                draw = ImageDraw.Draw(imdebug)
                pixcopy = imdebug.load()

            # Clean image for powerfull search
            self.cleanImage(im, pix)
            im.save("cleaned" + str(iDebugSaveFile) + ".png", "png")

            found = set()
            findnewcircle = True

            # finding all the circles
            for y1 in stepheight:
                x1 = 1
                curcolor = -1
                for k in range(1,100):
                    findnewcircle = False
                    retval = self.findFirstPixelX(im, pix, x1, y1, -1, False)
                    x1 = retval[0]
                    curcolor = retval[1]
                    if x1 == -2:
                        break;
                    if x1 == -1:
                        break;
                    if self._DEBUG == True: print "x1, y1 -> " + str((x1,y1)) + ": " + str(pix[x1,y1])

                    if (x1,y1) in self.pointsofcirclefound:
                        if self._DEBUG == True: print 'found ' + str((x1,y1))
                        continue;

                    if self._DEBUG == True: pixcopy[x1,y1] = 45 #(255,0,0,255)
                    # found 1 pixel, seeking x2,y2
                    x2 = x1
                    y2 = y1
                    for i in range(1,100):
                        retval = self.findLastPixelX(im, pix, x2, y2, -1, True)
                        x2 = retval[0]
                        if x1 == -2:
                            findnewcircle = True
                            break;
                        if x2 == -1:
                            break;
                        if self._DEBUG == True: print "x2, y2 -> " + str((x2,y1)) + ": " + str(pix[x2,y1])
                        if abs(x2 - x1) < min_distance:
                            continue;
                        if abs(x2 - x1) > (im.size[1] * 2 / 3):
                            break;
                        if abs(x2 - x1) > max_diameter:
                            break;

                        if self._DEBUG == True: pixcopy[x2,y2] = 65 #(0,255,0,255)
                        # found 2 pixel, seeking x3,y3
                        # verify cord

                        for invert in range(0,2):
                            x3 = math.floor(x2 - ((x2 - x1) / 2))
                            y3 = y1
                            for j in range(1,50):
                                retval = self.findLastPixelY(im, pix, x3, y3, True if invert == 1 else False, -1, True)
                                # print (x3, y3,retval[0],invert)
                                y3 = retval[0]
                                if y3 == -2:
                                    findnewcircle = True
                                    break;
                                if y3 == -1:
                                    break;

                                if self._DEBUG == True: print "x3, y3 -> " + str((x3,y3)) + ": " + str(pix[x3,y3])
                                # verify cord
                                if abs(y3 - y2) < min_distance:
                                    continue;
                                if abs(y3 - y2) > (im.size[1] * 2 / 3):
                                    break;
                                if abs(y3 - y2) > max_diameter:
                                    break;

                                if self._DEBUG == True: pixcopy[x3,y3] = 85
                                # found 3 pixel. try circle
                                c = self.findCircle(pix, x1,y1,x2,y2,x3,y3)

                                if c[0] + c[2] >= im.size[0] or c[1] + c[2] >= im.size[1] or c[0] - c[2] <= 0 or c[1] - c[2] <= 0:
                                    continue;

                                if self._DEBUG == True: pixcopy[c[0],c[1]] = 0
                                # (x-r, y-r, x+r, y+r)
                                verified = self.verifyCircle(im, pix, c)

                                if verified == -1:
                                    verified = -1
                                elif verified == 0:
                                    found.add(((c[0],c[1],c[2]),verified))
                                    findnewcircle = True
                                elif verified == 1:
                                    found.add(((c[0],c[1],c[2]),verified))
                                    findnewcircle = True

                                if self._DEBUG == True:
                                    _pause = ""
                                    # if verified == -1:
                                        # draw.ellipse((c[0]-c[2],c[1]-c[2],c[0]+c[2],c[1]+c[2]),outline=0)
                                        # _pause = "NOTDOUND"
                                        # imdebug.save("debug.png", "png")
                                    if verified == 0:
                                        draw.ellipse((c[0]-c[2],c[1]-c[2],c[0]+c[2],c[1]+c[2]),outline=120)
                                        _pause = "OPENED"

                                    if verified == 1:
                                        draw.ellipse((c[0]-c[2],c[1]-c[2],c[0]+c[2],c[1]+c[2]),outline=65)
                                        _pause = "CLOSED"

                                    imdebug.save("debug.png", "png")

                                    if _pause != "":
                                        valore = raw_input('Found ' + _pause + ' CIRCLE circle press [Enter] = continue / [q] for Quit: ' + str(verified))
                                        if valore == 'q':
                                            sys.exit();

                                if findnewcircle == True:
                                    break;
                            if findnewcircle == True:
                                break;
                        if findnewcircle == True:
                            break;

            if self._DEBUG == True:
                print 'Howmany opened circle? ' + str(len(found)) + ' ' + str(found)

            # clean results
            for c in found:
                verify = c[1]
                if verify == 0:
                    p = c[0]
                    if (
                        ((p[0], p[1]+1,p[2]),1) in found or \
                        ((p[0], p[1]-1,p[2]),1) in found or \
                        ((p[0]+1, p[1],p[2]),1) in found or \
                        ((p[0]-1, p[1],p[2]),1) in found or \
                        ((p[0]+1, p[1]+1,p[2]),1) in found or \
                        ((p[0]-1, p[1]+1,p[2]),1) in found or \
                        ((p[0]+1, p[1]-1,p[2]),1) in found or \
                        ((p[0]-1, p[1]-1,p[2]),1) in found \
                        ):

                        # delete nearly circle
                        verify = -1
                    if (
                        ((p[0], p[1]+1,p[2]+1),1) in found or \
                        ((p[0], p[1]-1,p[2]+1),1) in found or \
                        ((p[0]+1, p[1],p[2]+1),1) in found or \
                        ((p[0]-1, p[1],p[2]+1),1) in found or \
                        ((p[0]+1, p[1]+1,p[2]+1),1) in found or \
                        ((p[0]-1, p[1]+1,p[2]+1),1) in found or \
                        ((p[0]+1, p[1]-1,p[2]+1),1) in found or \
                        ((p[0]-1, p[1]-1,p[2]+1),1) in found \
                        ):

                        # delete nearly circle
                        verify = -1
                    if (
                        ((p[0], p[1]+1,p[2]-1),1) in found or \
                        ((p[0], p[1]-1,p[2]-1),1) in found or \
                        ((p[0]+1, p[1],p[2]-1),1) in found or \
                        ((p[0]-1, p[1],p[2]-1),1) in found or \
                        ((p[0]+1, p[1]+1,p[2]-1),1) in found or \
                        ((p[0]-1, p[1]+1,p[2]-1),1) in found or \
                        ((p[0]+1, p[1]-1,p[2]-1),1) in found or \
                        ((p[0]-1, p[1]-1,p[2]-1),1) in found \
                        ):

                        # delete nearly circle
                        verify = -1

                # if verify == 0:
                    # if self._DEBUG == True:
                    # pix[c[0][0],c[0][1]] = 90 #(255,255,0)
                    # im.save("output.png", "png")
                    # return c[0][0],c[0][1]
                # elif verify == 1:
                    # if self._DEBUG == True:
                        # pix[c[0][0],c[0][1]] = 40 #(255,0,0)
                        # im.save("output.png", "png")
                # else:
                    # if self._DEBUG == True:
                        # pix[c[0][0],c[0][1]] = 180 #(0,0,255)
                        # im.save("output.png", "png")

        if self._DEBUG == True:
            im.save("output.png", "png")


    # Return coordinates of opened circle (eg (x,y))
    def decrypt_from_web(self, url):
        file = cStringIO.StringIO(urllib.urlopen(url).read())
        img = Image.open(file)
        coords = self.decrypt(img);
        print "Coords: " + str(coords)


    # Return coordinates of opened circle (eg (x,y))
    def decrypt_from_file(self, filename):
        coords = self.decrypt(Image.open(filename)); #Can be many different formats.
        print "Coords: " + str(coords)


##DEBUG
# import datetime
# a = datetime.datetime.now()
# x = CircleCaptcha()
# coords = x.decrypt_from_file("decripter/captx.html2.gif")
# coords = x.decrypt_from_web("http://ncrypt.in/classes/captcha/circlecaptcha.php")
# b = datetime.datetime.now()
# print 'Elapsed time: ' + str((b-a).seconds) + ' seconds'
