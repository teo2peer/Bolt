from cmath import e, inf
from re import sub
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
from adafruit_rgb_display import st7735 as TFT # pylint: disable=unused-import
from adafruit_rgb_display import color565
from PIL import Image, ImageDraw, ImageFont
import plotly.graph_objects as go
import psutil
import digitalio
import board
import asyncio
from datetime import datetime
import time
import math
import requests as rq
import random
import multiprocessing as mp

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Screen(mp.Process):
    

    def __init__(self,screen_pipe ,cs_pin=board.CE0, dc_pin=board.D25, reset_pin=board.D24, baudrate=24000000,led=board.D23, SPI_SPEED_MHZ=10):
        
        # 
        super().__init__()
        self.screen_pipe = screen_pipe

        """
        Initialize the screen
        """        
        cs_pin = digitalio.DigitalInOut(cs_pin)
        dc_pin = digitalio.DigitalInOut(dc_pin)
        reset_pin = digitalio.DigitalInOut(reset_pin)
        BAUDRATE = baudrate

        # initialize SPI
        spi = board.SPI()

        # enable led
        led = digitalio.DigitalInOut(led)
        led.direction = digitalio.Direction.OUTPUT
        led.value = True


        # create and initialize TFT LCD display
        disp = TFT.ST7735R(
            spi, 
            rotation=270,# 1.8" ST7735R
            cs=cs_pin,
            dc=dc_pin,
            rst=reset_pin,
            baudrate=BAUDRATE,
        )

        self.WIDTH = disp.height
        self.HEIGHT = disp.width

        # WIDTH = 160
        # HEIGHT = 128

        # save variables
        self.disp = disp 
        
        # for async gif thread play

        self.gif_to_show = None
        self.gif_cached = None

        


    def run(self):
        text = "";
        while True:

            # check if new pipe is received
            if self.screen_pipe.poll():
                text = self.screen_pipe.recv()

            if text == "clear":
                self.clear_screen()
                continue
            
            elif text == "love":
                self.show_gif("/home/pi/robot/images/sending-love.gif")
            elif text == "normal":
                self.show_gif("/home/pi/robot/images/normal.gif")



            elif text == "exit":
                break
            else:
                continue


    def clear_screen(self):
        """
        Clear the screen
        """
        if self.disp.rotation % 180 == 90:
            HEIGHT = self.disp.width  # we swap height/width to rotate it to landscape!
            WIDTH = self.disp.height
        else:
            WIDTH = self.disp.width  # we swap height/width to rotate it to landscape!
            HEIGHT = self.disp.height
        image = Image.new("RGB", (WIDTH, HEIGHT))
        # Get drawing object to draw on image.
        draw = ImageDraw.Draw(image)

        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, WIDTH, HEIGHT), outline=0, fill=(0, 0, 0))
        self.disp.image(image)
    
        
    
    def resize_image(self, image, auto_save=False, path=""):
        if(auto_save):
            image = Image.open(path)
        image_ratio = image.width / image.height
        screen_ratio = self.WIDTH / self.HEIGHT
        if screen_ratio < image_ratio:
            scaled_width = image.width * self.HEIGHT // image.height
            scaled_height = self.HEIGHT
        else:
            scaled_width = self.WIDTH
            scaled_height = image.height * self.WIDTH // image.width
        image =  image.resize((scaled_width, scaled_height), Image.BICUBIC)
        # Crop and center the image
        x = scaled_width // 2 - self.WIDTH // 2
        y = scaled_height // 2 - self.HEIGHT // 2
        image = image.crop((x, y, x + self.WIDTH, y + self.HEIGHT))
        image = image.convert("RGBA")

        if(auto_save):
            image.save(path)
        return image

    def show_text(self, text, fontSize=15, color="white",  background="black"):
        """
        Functon to show text on the screen
        :param text: text to show
        :param color: color of the text
        :param fontSize: font size of the text
        :param background: background color
        """

        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color=background)
        draw = ImageDraw.Draw(img)

        # Load default font.
        font = ImageFont.truetype("/home/pi/robot/font/RobotoFlex-Regular.ttf", fontSize)

        # TODO if whidth of text is longer than width of the screen add an \n to split the text in two lines
        

        # Write text always in the center
        w, h = draw.textsize(text, font=font)
        draw.text(((self.WIDTH - w) / 2, (self.HEIGHT - h) / 2), text, font=font, fill=color)

        self.disp.image(self.resize_image(img))
    

    def show_image(self, image, plain=False):
        """
        Function to write an image to the screen
        :param image: image to write
        """
        
        if plain:
            self.disp.image(self.resize_image(image))
        else:
            image = Image.open(image)
            self.disp.image(self.resize_image(image))

    def show_gif(self, gif, times =1):
        """
        Function to show a gif on the screen
        :param gif: gif to show
        :param times: how many times to show the gif
        """

        if self.gif_to_show != gif:
            self.gif_to_show = gif
            gif = Image.open(gif)
            self.gif_cached = gif
        else:
            gif = self.gif_cached


        frame = 0
        gifDelay = 0.01


        for i in range(gif.n_frames):
            if self.screen_pipe.poll():
                break
            try:
                gif.seek(frame)
                self.disp.image(self.resize_image(gif.copy()))
                frame += 1
                time.sleep(gifDelay)

            except EOFError:
                frame = 0


        

    def stop_gif(self):
        self.gif_loop = False
        self.gif_to_show = None
        self.thread = False

    def change_gif(self, gif):
        self.gif_to_show = gif
    # draw loading circle with percentage and text inside

    def draw_circle_percent(self, percent, text, arcBg=(255, 255, 255), bg=(0, 0, 0), fontSize=20):
        """
        Function to draw a loading circle on the screen
        :param percent: percentage of the circle
        :param text: text inside the circle
        :param arcBg: background color of the arc
        :param bg: background color of the circle
        :param fontSize: font size of the text
        """
        # create image
        out = Image.new("RGB", (self.WIDTH, self.HEIGHT), bg)
        draw = ImageDraw.Draw(out)
        
        draw.ellipse((25, 10, self.HEIGHT+5, self.HEIGHT-10), fill=(0, 0, 0), width=5)
        draw.ellipse((25, 10, self.HEIGHT+5, self.HEIGHT-10), outline=(100, 100, 100), width=5)
        draw.arc((25, 10, self.HEIGHT+5, self.HEIGHT-10), -90, 360*percent-90 , fill=arcBg, width=5)


        # draw the text in the middle
        font = ImageFont.truetype("/home/pi/robot/font/RobotoFlex-Regular.ttf", fontSize)
        w, h = draw.textsize(text, font=font)
        draw.text(((self.WIDTH-w)/2, (self.HEIGHT-h)/2), text, font=font, fill=(255, 255, 255))

        draw = self.check_notification(draw)
        self.disp.image(out)


    # progress bar
    # https://as.com/meristation/imagenes/2013/08/17/album/1376694720_694720_000002_album_normal.jpg
    """
        Function to draw a progress bar on the screen
        :param x: x position of the progress bar
        :param y: y position of the progress bar
        :param w: width of the progress bar
        :param h: height of the progress bar
        :param progress: percentage of the progress bar
        :param text: text inside the progress bar
        :param bg: background color of the progress bar
        :param font_size: font size of the text
        :param fg: foreground color of the progress bar
        """

    def progress_bar(self, x, y, w, h, progress,text="Downloading...", font_size=15, bg="black",  fg="white"):
        

        # draw background
        out = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        d = ImageDraw.Draw(out)
        d.rectangle((x+h/2, y-3, x+w+h/2 +4, y+h +4), outline=fg)


        # draw progress bar
        w *= progress
        d.rectangle((x+(h/2)+3, y, x+w+(h/2), y+h+1),fill=fg)


        # draw percentage progress in the middle of the bar
        if progress < 0.47:
            d.text((self.WIDTH/2 -7 , y+(h/2)-4), str(int(progress*100))+"%", fill=(255,255,255))
        else:
            d.text((self.WIDTH/2 -7, y+(h/2)-4), str(int(progress*100))+"%", fill=(0,0,0))

        font = ImageFont.truetype("/home/pi/robot/font/RobotoFlex-Regular.ttf",font_size)

        # draw in small downloading in the top left corner of the bar
        # get height of the text
        w, h = d.textsize(text, font=font)
        # d.text((x+h/2, y+h/2), text, font=font, fill=fg)
        d.text((x+h/2, y+h/2 - (h+18)), text,font=font, fill=(255,255,255))

        self.show_image(out,True)

    





        # time clock
    def time_clock(self,serenity):
        # get actual time
        now = datetime.now()

        # get the hour and minute
        hour = now.hour
        minute = now.minute
        second = now.second
        # get miliseconds
        miliseconds = now.microsecond//1000 
        out = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0,0,0))
        draw = ImageDraw.Draw(out)
        
        i=miliseconds
        # draw elipse that starts from center and becomes bigger
        # draw.ellipse((25-((self.HEIGHT/2)*(i%1000)/1000), 10-((self.HEIGHT/2)*(i%1000)/1000), (self.HEIGHT+((self.HEIGHT/2)*(i%1000)/1000)+5, self.HEIGHT-10+((self.HEIGHT/2)*(i%1000)/1000))), outline=(150, 0, 0), width=5)
        # invert the elipse to go from in to out
        if (serenity):
            if(second%2==0):
                draw.ellipse(((self.WIDTH/2)-(50*(i%1000)/1000), ((self.HEIGHT/2)-50*(i%1000)/1000), (self.WIDTH/2+((50)*(i%1000)/1000), self.HEIGHT/2+((50)*(i%1000)/1000))), outline=(150, 0, 0), width=5)
            else:
                draw.ellipse(((25)+(self.WIDTH/2*(i%1000)/1000), ((12)+(self.HEIGHT/2 +10)*(i%1000)/1000), (self.HEIGHT+5-((self.WIDTH/2)*(i%1000)/1000), (self.HEIGHT-12)-((self.HEIGHT/2 +10)*(i%1000)/1000))), outline=(150, 0, 0), width=5)
        draw.ellipse((25, 10, self.HEIGHT+5, self.HEIGHT-10), outline=(100, 100, 100), width=5)


        # draw hours
        hourPos = 360/12*(hour%12)
        draw.arc((25, 10, self.HEIGHT+5, self.HEIGHT-10), hourPos-90, hourPos-86 , fill=(0,0,255), width=10)

        # draw minutes
        minPos = 360/60*minute
        draw.arc((25, 10, self.HEIGHT+5, self.HEIGHT-10), minPos-90, minPos-86 , fill=(255,0,0), width=10)

        # draw seconds
        secPos = 360/60*second
        draw.arc((25, 10, self.HEIGHT+5, self.HEIGHT-10), secPos-90, secPos-86 , fill=(225,255,255), width=10)


        # have always 2 digits for the hour and minute
        hour = "0"+str(hour) if hour<10 else str(hour)
        minute = "0"+str(minute) if minute<10 else str(minute)

        # draw the text in the middle
        font = ImageFont.truetype("/home/pi/robot/font/RobotoFlex-Regular.ttf", 20)
        text = hour+":"+minute 
        w, h = draw.textsize(text, font=font)
        draw.text(((self.WIDTH-w)/2, (self.HEIGHT-h)/2), text, font=font, fill=(255, 255, 255))

        w, h = draw.textsize(text, font=font)
        draw.text(((self.WIDTH-w)/2, (self.HEIGHT-h)/2), text, font=font, fill=(255, 255, 255))

        draw = self.check_notification(draw)

        self.disp.image(out)
        time.sleep(0.05)




        
    def show_board_info():
        # get ram, temp and cpu usage
        ram = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        temp = psutil.sensors_temperatures()
        ram = ram.percent
        temp = temp["cpu_thermal"][0].current
        print(bcolors.OKGREEN + "RAM: " + bcolors.FAIL + str(ram) + bcolors.ENDC + " | " + bcolors.OKGREEN + "CPU: " + bcolors.FAIL + str(cpu) + bcolors.ENDC + " | " + bcolors.OKGREEN + "TEMP: " + bcolors.FAIL + str(temp) + bcolors.ENDC)


        info = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        # split screen in 3 parts
        widthOfSegment = self.WIDTH // 3
        draw = ImageDraw.Draw(info)

        heighMax = self.HEIGHT*0.2
        heightMin = self.HEIGHT*0.8
        # map the percentage of each segment


        cpuPercent=((cpu/100)*(heightMin-heighMax))+heighMax
        ramPercent=((ram/100)*(heightMin-heighMax))+heighMax
        tempPercent=((temp/100)*(heightMin-heighMax))+heighMax
        # draw cpu bar
        draw.rectangle((10, 10, widthOfSegment*0.8, self.HEIGHT*0.80), outline=(255, 255, 255))
        # draw cpu rectangle with the cpu usage as a percentage height from bottom to top beeing 0% the bottom and 100% the top
        draw.rectangle((10, self.HEIGHT*0.8, widthOfSegment*0.8, cpuPercent), fill=(255, 255, 255))
        draw.text((widthOfSegment*0.1, self.HEIGHT*0.80), str(cpu), fill=(255, 255, 255))
        # draw temp bar
        draw.rectangle((widthOfSegment*1.1, 10, widthOfSegment*1.8, self.HEIGHT*0.80), outline=(255, 255, 255))
        draw.rectangle((widthOfSegment*1.1, self.HEIGHT*0.8, widthOfSegment*1.8, ramPercent), fill=(255, 255, 255))
        draw.text((widthOfSegment*1.1, self.HEIGHT*0.80), str(temp), fill=(255, 255, 255))
        # draw ram bar
        draw.rectangle((widthOfSegment*2.1, 10, widthOfSegment*2.8, self.HEIGHT*0.80), outline=(255, 255, 255))
        draw.rectangle((widthOfSegment*2.1, self.HEIGHT*0.8, widthOfSegment*2.8, tempPercent), fill=(255, 255, 255))
        draw.text((widthOfSegment*2.1, self.HEIGHT*0.80), str(ram), fill=(255, 255, 255))
        # write the image to the display


        self.disp.image(info)

        
    """
        Draw an crypto graph
        :param crypto: the crypto to draw
        :param days: the number of days to draw
        :param timePeriod: the time period to draw
        :param toShow: the number of days to show
        :return:
        """
    def show_crypto_graph(self, crypto="dogecoin",days=1, timePeriod="hour", toShow=12):
        try:

            self.drawProgressBar(2, self.HEIGHT/2 - 6, self.WIDTH-25, 15, 0, "Fetching data...", "white", (255,255,255))

            print(bcolors.WARNING + "Getting data from coingecko" + bcolors.ENDC)
            url = "https://api.coingecko.com/api/v3/coins/{0}/ohlc?vs_currency=usd&days={1}&interval={2}'".format(crypto,days,timePeriod)
            print(bcolors.WARNING + "URL: " + bcolors.ENDC + url)
            response = urllib.request.urlopen(url)
            # progress bar from 0% to 35% 
            for i in range(0,35):
                drawProgressBar(2, self.HEIGHT/2 - 6, self.WIDTH-25, 15, i/100, "Fetching data...", "white", (255,255,255))
                time.sleep(0.002)


            data = json.loads(response.read().decode())
            # get the data from the api
            # data = data[0]
            
            timeMap=[]
            open = []
            high = []
            low = []
            close = []
            # for i in range(len(data)):
            #     timeMap.append(data[i][0])
            #     priceMap.append(data[i][1])
            print(bcolors.WARNING + "Drawing graph... " + bcolors.ENDC, end="")
            toShow = 0 if toShow == 0 else len(data) - toShow

            percentageStep = len(data)-toShow;

            for i in range(toShow,len(data)):
                timeMap.append(data[i][0])
                open.append(round(data[i][1],6))
                high.append(round(data[i][2],6))
                low.append(round(data[i][3],6))
                close.append(round(data[i][4],6))
            
            # percentage bar from 35 to 80%
            for i in range(35,80):
                self.drawProgressBar(2, self.HEIGHT/2 - 6, self.WIDTH-25, 15, i/100, "Drawing graph...", "white", (255,255,255))
                time.sleep(0.002)

            minPrice = min(low)
            maxPrice = max(open)

            # create the crypto graph
            # font to 10 px
            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=timeMap,
                        open=open,
                        high=high,
                        low=low,
                        close=close,
                        increasing_line_color= '#00ff00',
                        decreasing_line_color= '#ff0000'

                    )
                ]
            )

            fig.update_layout(
                title=crypto + " Price History",
                title_x=0.5,
                xaxis_tickformat='%H:%M',
                xaxis_title_font_size=30,
                xaxis_tickfont_size=30,
                yaxis_title="Price",
                xaxis=dict(
                    rangeslider_visible=False,
                    type="date"
                ),  
                font=dict(
                    size=35
                )

            )

            # fig to image and pass to writeImageToDisplay function

            self.drawProgressBar(2, self.HEIGHT/2 - 6, self.WIDTH-25, 15, 0.90, "Displaying graph...", "white", (255,255,255))
            fig.write_image("/home/pi/robot/tmp/graph.png")
            img = Image.open("/home/pi/robot/tmp/graph.png")

            self.show_image(img,True)


        except Exception as e:
            print(e)
            print("Error getting data from coingecko api")
            return None


    def warframe_info(self):
        # info in spanish as querry paramter
        if(self.last_check == None or (time.time() - self.last_check) > 10):
            if(time.time() - self.last_check > 10):
                cetus_info = rq.get("https://api.warframestat.us/pc/cetusCycle", params={"language":"es"})
                void_trader_info = rq.get("https://api.warframestat.us/pc/voidTrader", params={"language":"es"})
                self.last_check = time.time()
                self.last_api=[cetus_info,void_trader_info]
            else:
                cetus_info = self.last_api[0]
                void_trader_info = self.last_api[1]        
            #get the data from the api
            cetus_info = cetus_info.json()
            void_trader_info = void_trader_info.json()

            is_day = cetus_info["isDay"]
            time_left = cetus_info["timeLeft"]
            # if m is in the string, replace it with minutes
            try:
                if("h" in time_left):
                    hours = ((int)(time_left.split('h')[0]))*60*60
                    minutes = ((int)(time_left.split('h')[1].split('m')[0]))*60
                    seconds = ((int)(time_left.split('h')[1].split('m')[1].split('s')[0]))
                elif "m" in time_left:
                    minutes = ((int)(time_left.split('m')[0]))*60
                    seconds = int(time_left.split('m')[1].split('s')[0])
                    hours = 0
                else:
                    seconds = int(time_left.split('s')[0])
                    minutes = 0
                    hours = 0
                total_time = hours+ minutes + seconds
            except:
                return
            
            if(total_time<0):
                is_day = not is_day

            
            out = Image.new("RGBA", (self.WIDTH, self.HEIGHT), (0, 0, 0))


            d = ImageDraw.Draw(out)

            

            if(is_day):
                bg_img = Image.open("/home/pi/robot/lib/assets/images/warframe/dia.png")
                out.paste(bg_img, (-22, 0))
            else:
                bg_img = Image.open("/home/pi/robot/lib/assets/images/warframe/noche.png")
                out.paste(bg_img, (-22, 0))


                # d.ellipse((0, self.HEIGHT/2, self.WIDTH, self.HEIGHT+self.HEIGHT/2), outline=(255, 255, 255))
        
            font = ImageFont.truetype("/home/pi/robot/font/RobotoFlex-Regular.ttf", 16)
            # center the text
            text_width, text_height = font.getsize(time_left)
            positionx = (self.WIDTH/2)-text_width/2
            positiony = self.HEIGHT-text_height-2
            d.text((positionx, positiony), time_left, font=font, fill=(255, 255, 255))

            
            if(void_trader_info["active"]):
                text = void_trader_info["endString"]
                color = (0,255,0)
            else:
                text = void_trader_info["startString"].split("m")[0]+"m"
                color = (255,0,0)
            # write at the top right next time that the void trader will be open
            font = ImageFont.truetype("/home/pi/robot/font/RobotoFlex-Regular.ttf", 16)

            text=text.split(" ")[0]
            text_width, text_height = font.getsize(text)
            positionx = self.WIDTH-text_width-1
            positiony = self.HEIGHT-text_height-2
            d.text((positionx, positiony), text, font=font, fill=color)


            d= self.check_notification(d)

            self.show_image(out,True)


        time.sleep(0.1)

        


