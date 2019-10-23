from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import argparse, time, random, ctypes, os, sys, urllib
import urllib.request as url
from PIL import Image, ImageDraw, ImageFont

import pygame


#Googles API client require you to set up a developer account and a project to begin. 
#Instructions can be found on the API sites https://developers.google.com/photos/library/guides/overview
#The api client library can be installed using "pip3 install google-api-python-client" 
#It also requires the oauth2client library "pip3 install oauth2client"

#initially the script will try to load myphoto.jpg from when the script was ran last
#as it takes a couple of minutes to get a photo initially.  A Timer icon will also display.
#if the photo doesn't exist it displays a blank screen - just wait for it to compile the list from the album.


os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()

fullscreen = True

info = pygame.display.Info()
screen_width,screen_height = info.current_w,info.current_h
display_width,display_height = screen_width,screen_height
max_display_width, max_display_height = display_width, display_height
#display size automatically set using the screen height/width above.    If manual is required uncomment below
#display_height = 1080
#display_width = 1920

disp = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
pygame.display.set_caption('Google Image Slideshow')

black = (0,0,0)
pygame.mouse.set_visible(False)

playAll = False #This can take quite a while to get a list of all photos on initialisation and every hour at refresh (see timerDelay below)
photoAlbum = "Google Photos Slideshow"
oldRandom = None
photoName = 'myPhoto.jpg'
timerSet = 0
timerDelay = 3600 #Google Photos Authorisation lapses every hour, this sets the timeout on when to reauth and refresh the photos
photoTimer = 0
slideshowDelay = 30 #download and show a photo every 30 seconds 
_WAIT_CURSOR = (
" XXXXXXXXXXXXXX ",
"  XX........XX  ",
"   X...XX...X   ",
"   X..XXXX..X   ",
"   XXXXXXXXXX   ",
"    XXXXXXXX    ",
"      XXXX      ",
"       XX       ",
"      X..X      ",
"    X......X    ",
"   X...X....X   ",
"   X........X   ",
"   X...X....X   ",
"   X...XX...X   ",
"  XX..XXXX..XX  ",
" XXXXXXXXXXXXXX ")
_HCURS, _HMASK = pygame.cursors.compile(_WAIT_CURSOR, ".", "X")
WAIT_CURSOR = ((16, 16), (5, 1), _HCURS, _HMASK)

def ConnectToGoogleImages():
    pygame.mouse.set_visible(True)
    pygame.mouse.set_cursor(*WAIT_CURSOR)
    try:
        SCOPES = 'https://www.googleapis.com/auth/photoslibrary.readonly'
        gdriveservice = None
        credsFileName = 'mycreds.txt'
        store = file.Storage(credsFileName)
        creds = store.get()
        if not creds or creds.invalid:
            if not pygame.display.iconify():
                #pygame.display.toggle_fullscreen()
                disp = pygame.display.set_mode((int(display_width/8),int(display_height/8)), pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE)
            flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
            parser = argparse.ArgumentParser(add_help=False)
            parser.add_argument('--logging_level', default='ERROR')
            parser.add_argument('--noauth_local_webserver', action='store_true',
                default=True, help='Do not run a local web server.')
            args = parser.parse_args([])
            creds = tools.run_flow(flow, store, args)
            gdriveservice = build('photoslibrary', 'v1', http=creds.authorize(Http()))
            credentials_file = open(credsFileName, 'wb')
            store.put(creds)
            disp = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        else:
            gdriveservice = build('photoslibrary', 'v1', http=creds.authorize(Http()))
        album_results = gdriveservice.albums().list(pageSize=20).execute()
        album_items = album_results.get('albums', [])
        album_id_array = []
        slideshowAlbumId = None
        for item in album_items:
            print(u'{0} ({1})'.format(item['title'].encode('utf8'), item['id']))
            album_id_array.append(item['id'])
            if not playAll:
                if photoAlbum in item['title']:
                    slideshowAlbumId = item['id']
                    print ("Got ID for album ", photoAlbum)

        nextPageToken = ''
    
        if playAll:
            print ("Getting list of all photos")
            media_results = gdriveservice.mediaItems().search(body={"pageSize" :50, "pageToken" : nextPageToken}).execute() #search all items
        else:
            print ("Getting list of all photos in album ", photoAlbum)
            media_results = gdriveservice.mediaItems().search(body={"albumId": slideshowAlbumId, "pageSize" :25, "pageToken" :nextPageToken}).execute()
        media_list = media_results['mediaItems']
    #print(media_list)
        while 'nextPageToken' in media_results: 
            nextPageToken = media_results['nextPageToken']
            if playAll:
                media_results = gdriveservice.mediaItems().search(body={"pageSize" :50, "pageToken" : nextPageToken}).execute() #search all items
            else:
                media_results = gdriveservice.mediaItems().search(body={"albumId": slideshowAlbumId, "pageSize" :25, "pageToken" : nextPageToken}).execute()
            for item in media_results['mediaItems']:
                media_list.append(item)
            #print(len(media_list))
        print ("Total: ",len(media_list))
        if fullscreen:
            pygame.mouse.set_visible(False)
        else:
            pygame.mouse.set_visible(True)
        pygame.mouse.set_cursor(*pygame.cursors.arrow)
        if fullscreen:
            pygame.mouse.set_visible(False)
        return media_list
    except:
        raise
    
def getRandom(firstNum, lastNum): #function to get a random number
    global oldRandom # get the global variable
    randomNumber = random.randint(firstNum, lastNum) # get the random number
    if randomNumber == oldRandom: # if the value is the same as the last one
        randomNumber = getRandom(firstNum, lastNum) #go again
    else: #if its different
        oldRandom = randomNumber # save the value for the next run
    return randomNumber #return the number

def pygameDisplayImage(imagefile, fullscreen_mode):
    disp.fill(black)
    info = pygame.display.Info()
    window_width,window_height = disp.get_size()
    display_width,display_height = window_width,window_height
    print(display_width,display_height)
    hCenter = display_height/2
    wCenter = display_width/2
    if os.path.exists(imagefile):
        image = Image.open(imagefile)
        if not fullscreen_mode:
            image.thumbnail((display_width,display_height), Image.ANTIALIAS)
        mode = image.mode
        size = image.size
        data = image.tobytes()
        pygameImage = pygame.image.fromstring(data,size,mode)
        imagewidth = pygameImage.get_width()
        imageheight = pygameImage.get_height()
        startx = hCenter - (imageheight/2)
        starty = wCenter - (imagewidth/2)
        disp.blit(pygameImage,(starty, startx))
    pygame.display.update()
    
    
def DownloadRandomPhoto(media_list, mxWidth, mxHeight):
    #for item in media_list:
        #print ("filename: ",item['filename'], " | id: ",item['id'])
    downloadFile = media_list[getRandom(0, len(media_list)-1)]
    filetype = downloadFile['mimeType']
    if filetype == 'image/jpeg':
        downloadUrl = downloadFile['baseUrl']+'=w'+str(mxWidth)+'-h'+str(mxHeight)
        try:
            url.urlretrieve(downloadUrl, photoName)
        except urllib.error.HTTPError:
            media_list = ConnectToGoogleImages()
        except urllib.error.URLError:
            media_list = ConnectToGoogleImages()
        except:
            raise
media_list = None
running = True

singleClick = False
doubleClickDelay = .350
doubleClickTimer = 0
while(running):
    try:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                print("MouseButtonUp")
                if singleClick:
                    print("DoubleClick")
                    info = pygame.display.Info()
                    if (fullscreen):
                        fullscreen = False
                        pygame.mouse.set_visible(True)
                        window_width,window_height = pygame.display.get_surface().get_size()
                        display_width,display_height = (window_width/2-10),(window_height/2-10)
                        disp = pygame.display.set_mode((int(display_width),int(display_height)), pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE)
                        
                    else:
                        fullscreen = True
                        pygame.mouse.set_visible(False)
                        screen_width,screen_height = info.current_w,info.current_h
                        display_width,display_height = screen_width,screen_height
                        disp = pygame.display.set_mode((max_display_width,max_display_height), pygame.FULLSCREEN)
                        
                    pygame.display.flip()
                    pygameDisplayImage(photoName, fullscreen)
                    singleClick = False
                    
                else:
                    print("SingleClick")
                    singleClick = True
                    doubleClickTimer = time.time()
            elif event.type == pygame.VIDEORESIZE:
                print("VideoResize")
                info = pygame.display.Info()
                window_width,window_height = pygame.display.get_surface().get_size()
                display_width,display_height = window_width,window_height
                print(display_width,display_height)
                disp = pygame.display.set_mode((event.w, event.h), pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE)
                pygame.display.flip()
                pygameDisplayImage(photoName, fullscreen)           
            elif event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
        if ((time.time() - timerSet) > timerDelay) or (media_list == None):
            timerSet = time.time()
            pygameDisplayImage(photoName, fullscreen) 
            media_list = ConnectToGoogleImages()
        if (time.time() - photoTimer > slideshowDelay):
            photoTimer = time.time()
            print("Downloading File")
            DownloadRandomPhoto(media_list, max_display_width, max_display_height)
            googlePhoto = Image.open(photoName)
            print ("opening Image", photoName);
            #googlePhoto.show()
            pygameDisplayImage(photoName, fullscreen)
        if (singleClick):
            if (time.time() - doubleClickTimer > doubleClickDelay):
                singleClick = False
                print ("Resetting SingleClick")
        
        #running = False
        time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        pygame.quit()
        sys.exit()
    except :
        raise
        pygame.quit()
        sys.exit()
