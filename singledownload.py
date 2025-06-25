import sys, getopt
import re
import json
import traceback
import time
import os
import random
import shlex
import subprocess
import pathlib

from selenium.webdriver.chrome.options import Options
import logging
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from pathlib import Path
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from fake_useragent import UserAgent
from selenium.webdriver.support import expected_conditions as EC


import logging

#options = Options()
options = webdriver.ChromeOptions()
service = Service()
options.set_capability(
    "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
)
options.log_path='/home/cesarin/IdeaProjects/Seleniumtest1/geckodriver_log_path.log'
options.add_argument("--enable-logging --v=1")
options.add_argument("--log-level=3")
options.enable_bidi = True
options.add_argument("----mute-audio")
options.add_argument("--auto-open-devtools-for-tabs")
options.add_argument("--window-size=3840,2160")
#options.add_argument("--headless")
#options.add_argument("--start-maximized")

ua = UserAgent()
#my_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
options.add_argument(f"--user-agent={ua.random}") #generates random user agents to prevent blockades.
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'}) #critical to get the mp3u8




def mainProgram(Website, username, password, webDriver, path): #main program if run as a single video
    StartLogin(Website, username, password, webDriver)
    DownloadVideo(Website, webDriver)
    fileList_finalm3u8 = CreatingFileList(webDriver)
    titleList = CreatingTitle(webDriver)
    
    completedProcess = ProcessingVideo(titleList,fileList_finalm3u8, webDriver, path)
    if completedProcess == True:
        print("Video Download Completed")
        webDriver.quit()
        sys.exit()
    else:
        print("Download Failed, check the error output")
        webDriver.quit()
        sys.exit()
def setLoop(urlList, username, password, webDriver, path): #main porogram if run as a list
    WebSite = "https://bsky.app/notifications"
    #webDriver.get("https://bsky.app/notifications")
    time.sleep(1)
    StartLogin(WebSite, username, password, webDriver)
    time.sleep(1)
    listOfFiles = []
    
    for url in urlList:
        #time.sleep(1)
        original_window = webDriver.current_window_handle
        time.sleep(1)
        webDriver.execute_script("window.open('about:blank','secondtab');")
        time.sleep(1)
        webDriver.switch_to.window("secondtab")
        #time.sleep(1)
        second_window = webDriver.current_window_handle
        #print("Main tab: "+ original_window + "\n Second tab: " + second_window)
        listofTabs = webDriver.window_handles
        #for eachTab in listofTabs:
        #  print("Tab: "+ str(listofTabs.index(eachTab)+1) + " of " + str(len(listofTabs)) + " Tabs. Name: " + eachTab)
        time.sleep(1)
        WebSite = url
        statusOfSite = DownloadVideo(WebSite, webDriver)
        if statusOfSite == True: #if the website returns true, the website is not valid or it has incorrect credentials.
            webDriver.window_handles.remove(second_window)        
            #webDriver.close()
            webDriver.switch_to.window(original_window)
            continue
        time.sleep(1)
        finalm3u8=CreatingFileList(webDriver)
        time.sleep(1)
        getpagetitle = CreatingTitle(webDriver)
        time.sleep(1)
        completedProcess = ProcessingVideo(getpagetitle,finalm3u8, webDriver, path)
        time.sleep(1)
        if completedProcess == True:
            print("Video #" + str(urlList.index(url)+1) + " out of " + str(len(urlList))+" Downloaded.    ")
            listOfFiles.append(url)
        else:
            print("Download Failed, check the error output")
        webDriver.window_handles.remove(second_window)
        
        #webDriver.close()
        webDriver.switch_to.window(original_window)
        time.sleep(1)
    print("Video Collection Download Completed. Total of " + str(len(listOfFiles)) + " files downloaded.")
    webDriver.quit()
    sys.exit()
def checkFileConfig():
    print("Checking Configuration File...")    
    try:
        with open('config.ini') as f: 
            content = f.readlines()
            if content == []:
                print("Fatal Error, config.ini is empty. Please check config.ini file. \n and run again. \n")
                sys.exit()
            else: 
                username = content[0]
                password = content[1]
            return username, password
            
    except Exception:
        print("Config file not found. Please create a config.ini file and add your username and password. \n")
        sys.exit()
def CheckUrlList():
    print("Checking URL List File...")    
    try:
        with open('url_list.txt') as f: 
            content = f.readlines()
            for each in content:
                print("Url #" + str(content.index(each)+1) + " of " + str(len(content)) + ": "+ each)
            
            return content
            
    except Exception:
        print("url list file not found. Please create a url_list.txt file and add your list of urls, one url per line. \n")
        sys.exit()
def makeDirectory():
    print("Checking status of the Download Directory...")
    path = Path("Downloads")
    try:
        if path.exists():
            print("Download Directory already exists, skipping creation")
            
        else:
            path.mkdir(parents=True, exist_ok=True)
            print("Directory 'Downloads' Created")
    except OSError:
        print("Creation of the directory %s failed" % path)
        sys.exit()
    return path

def setChromeDriver():
    print("Phase 1: Setting up Chrome webDriver...")
    webDriver = webdriver.Chrome(service=service, options=options)
    log_entries = webDriver.get_log("performance")
    webDriver.script.add_console_message_handler(log_entries.append)
    wait = WebDriverWait(webDriver, 8)
    webDriver.implicitly_wait(8)
    return webDriver

    print("Phase 2: Set defaults...")

def StartLogin(WebSite, username, password, webDriver):
    if "https://bsky.app/" in WebSite:
        def GetWebSite():
            print("Browsing: " + WebSite)
            #webDriver.implicitly_wait(3)
        GetWebSite()
        time.sleep(2)    
        def LoginSite(WebSite, webDriver):        
                
            print("Phase 5: Trying to login..."  )
            
            
            #print("Phase 5: Trying to login...  Checking status: " + hasLoggedIn.__str__())
            try:
                webDriver.get("https://bsky.app/notifications")
                time.sleep(1)
                
            except Exception:
                webDriver.switch_to.window(webDriver.window_handles[0])
                time.sleep(1)
                webDriver.get("https://bsky.app/notifications")
                
            
            time.sleep(3)
            try:
                #if webDriver.find_element(By.PARTIAL_LINK_TEXT, value="Sign in").is_displayed():
                logcode = webDriver.find_element(By.CSS_SELECTOR, value="#root > div > div > div > div > div > div > div > div:nth-child(1) > div:nth-child(2) > button:nth-child(2)")
                logcode.click()
                time.sleep(2)
                    
                    
                
                
            except Exception:
                print(traceback.format_exc())
                print("Error trying to find to open the login form.")
                webDriver.quit()
                sys.exit()
                
                
            #    webDriver.find_element(By.PARTIAL_LINK_TEXT, value="Close active dialogue").is_displayed():
            #    adultcode =webDriver.find_element(By.CSS_SELECTOR,value="#root > div > div > div > div > div > div:nth-child(2)")
            #    adultcode.click()
            #    SendLogin()     
        LoginSite(WebSite, webDriver)    
                
                                
        def SendLogin(username, password, webDriver):
            try: 
                time.sleep(1)
                currentAddress = webDriver.current_url 
                elem = webDriver.find_element(By.CSS_SELECTOR, value="#root > div > div > div > div > div > div > div > div > div.css-g5y9jx.r-dta0w2 > div > div > div > div > div:nth-child(2) > div.css-g5y9jx > div:nth-child(1) > input")
                elem.send_keys(username)
                time.sleep(1)
                elem2 = webDriver.find_element(By.CSS_SELECTOR, value="#root > div > div > div > div > div > div > div > div > div.css-g5y9jx.r-dta0w2 > div > div > div > div > div:nth-child(2) > div.css-g5y9jx > div:nth-child(2) > input")
                elem2.send_keys(password)
                time.sleep(0.500)
                try:
                    elem3 = webDriver.find_element(By.CSS_SELECTOR('div#root > div > div > div > div > div > div > div > div > div:nth-of-type(2) > div > div > div > div > div:nth-of-type(4)'))
                    elem3.click()
                   
                except Exception:
                    pass
                try :
                    time.sleep(2)
                    if webDriver.find_element(By.XPATH, value="//*[text()='Incorrect username or password']").is_displayed():
                        print("Error: Incorrect username or password, check credentials and try again.")
                        webDriver.quit()
                        sys.exit()
                        
                except Exception:
                    print("Login OK...")
                
            except Exception:
                time.sleep(2)
                webDriver.quit()
                print(traceback.format_exc())
                print("Error, Unable to login or no login elements found")
                sys.exit()  
            except NameError:
                # hasLoggedIn = False
                pass    
                
            # hasLoggedIn =  True
            # return hasLoggedIn
        SendLogin(username, password, webDriver)
    else:
        print("Error: Website url is malformed")
        webDriver.quit()
        sys.exit()
        
def DownloadVideo(WebSite,webDriver):
    print("Phase 6: Checking content status on: " + WebSite)
    try :        
        webDriver.get(WebSite)
        time.sleep(3)
        if webDriver.find_element(By.XPATH, value="//*[text()='Post not found']").is_displayed():
            print("Error: url has been removed or not found")
            skipUrl = True
            return skipUrl
        elif webDriver.find_element(By.XPATH, value="//*[@aria-label='Press to retry']").is_displayed():
            print("Error: url has been removed or not found")
            skipUrl = True
            return skipUrl
        elif webDriver.find_element(By.XPATH, value="//*[text()='Unable to resolve handle']").is_displayed():
            print("Error: url has been removed or not found")
            skipUrl = True
            return skipUrl
        elif webDriver.find_element(By.XPATH, value="//*[text()='Internal Server Error']").is_displayed():
            print("Error: url has been removed or not found")
            skipUrl = True
            return skipUrl
        #webDriver.find_element(By.XPATH, value="//*[text()='Post not found']") #works
        #m = webDriver.find_element(By.XPATH, value="//*[@aria-label='Press to retry']") #works
        
    except Exception:
        print("Phase 6-0 - URL is valid")
    
   
    try : 
        
        if webDriver.find_element(By.XPATH, value="//*[text()='Adult Content']").is_displayed():
            print("Error: File is Adult Content, enable adult content to be able to see this content")
            skipUrl = True
            return skipUrl
    except Exception:
        print("Phase 6-2 - Access levels ok")
            
   
    try:
        try: 
            webDriver.refresh()
            time.sleep(1)
            webDriver.execute_script("window.scrollTo(0, document.body.scrollHeight/2;")
            #elemvid = WebDriverWait(webDriver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".r-sa2ff0 > div:nth-child(3) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > button:nth-child(1)")))
            try: 
                elemvid = WebDriverWait(webDriver, 3).until(EC.presence_of_element_located(By.XPATH, value="//*[contains(@aria-label),'Unmute video']")).click()
            except:
                pass
            try: 
                elemvid = webDriver.find_element(By.CSS_SELECTOR, "video:nth-child(1)").click()
            except:
                pass
        except:
            print(" Video element not found, trying to continue...")
            
        try: 
            elembox = webDriver.find_element(By.PARTIAL_LINK_TEXT, value="Play video")
            if elembox.is_displayed():
                elembox.click()
        except Exception:
            pass
            #print("Trying partial text method.")
            
        try: 
            elembox = webDriver.find_element(By.XPATH, value="/html/body/div[1]/div/div/div/div/main/div/div/div/div/div/div[2]/div[2]/div[2]/div/div[3]/div/div/div[2]/div[1]/div[2]/div/div/div/div/div/div[1]/div/div[1]/button")
            if elembox.is_displayed():
                elembox.click()
        except Exception:
            pass
            #print("Trying XPath method.")                
                  
                
        
        try: 
            elembox = webDriver.find_element(By.PARTIAL_LINK_TEXT, value="Unmute video")
            if elembox.is_displayed():
                elembox.click()
        except Exception:
            pass
            #print("Trying partial text method #2.")  
        time.sleep(3)
    except Exception:
        print(traceback.format_exc())
        print("Fatal error trying to find video element, check video url and try again.")
        webDriver.close() 
        webDriver.quit()
        sys.exit()



def CreatingFileList(webDriver):
    print("Phase 7: Creating File List")
    
    def getLogs(webDriver):
        
        logs = webDriver.get_log('performance')
        #logs2 = logs.split(',')
        #for each in logs:           
        #    print(each)
        
        time.sleep(1)

        def __init__(self, url):
            self.url = url
            self.webDriver = webDriver
            self.webDriver.get(self.url)
            
        addresses = []
        try:
            for i in logs:
                log = json.loads(i['message'])
                if log['message']['method'] == 'Network.responseReceived':
                    if log['message']['params']['response']['mimeType'] == 'application/vnd.apple.mpegurl':
                        addresses.append(log['message']['params']['response']['url'])
            check = set([i.split('/')[-1] for i in addresses])
            
            if len(check) > 0:
                print("Addresses: " + str(addresses))
                print ("Returning Addresses...")
                return addresses
                    

            print ("Phase 7-2: return addresses clean up")
            #if len(addresses) >= 1: print(json.dumps(addresses, indent=4), addresses)
        except Exception:
            print(traceback.format_exc())
            print("Error, element file elements, data not found or error when processing")
            webDriver.close()
            webDriver.quit()
            sys.exit()
        return addresses
    
    addresses = getLogs(webDriver)
    def sizeOfList(addresses):

        print (" Address: " + addresses[len(addresses)-1].split("m3u8",1)[0] + "m3u8")
        sizeOfList = addresses[len(addresses)-1].split("m3u8",1)[0] + "m3u8"
        
        return sizeOfList
    try:
        if len(addresses) == 0 or addresses == None:
            print("Error, element file elements, data not found or error when processing")
            webDriver.close()
            webDriver.quit()
            sys.exit()
        else:    
            finalm3u8 = sizeOfList(addresses)                
    except Exception:
        print(traceback.format_exc())
        print("Error on final phase of creating file list. The addresses list is possible empty")
        webDriver.close()
        webDriver.quit()
        sys.exit()
    print ("Phase 7-3: return addresses to single string")
    #global finalm3u8
    return finalm3u8

    
def CreatingTitle(webDriver):
    
    getAddress = webDriver.current_url.split("/post/",1)[1]
    sanitizeTitle1 = (webDriver.current_url.split("/",5)[4])
    if "." in sanitizeTitle1:
        sanitizeTitle1 = sanitizeTitle1.split(".",1)[0]
    sanitizeTitle =   re.sub('[^A-Za-z0-9]+', '', sanitizeTitle1)  
    #sanitizeTitle = (webDriver.title.split(":",1)[0]).translate(str.maketrans('', '', ':. -"()!@#$\''))
    getpagetitle = sanitizeTitle + "_" + getAddress + ".mp4"
    # getpagetitle = (webDriver.title.split("@",1)[0]).translate(str.maketrans('', '', ':. -"()!@#$\''))+ "_" + getAddress + ".mp4"
    print(" Generated title: " + getpagetitle)
    return getpagetitle  

def ProcessingVideo(getpagetitle,finalm3u8, webDriver, path):
    print("Phase 8: Processing Video")
    try:
        
        print(" Phase 8-1: Downloading Video and muxing...")
        #initialcommand = 'ffmpeg -y -i ' + '"'+ finalm3u8 +'"' + ' -c copy '+getpagetitle+' -report'
        #command = shlex.split(initialcommand)
        code1 = '"'+ finalm3u8 +'"'
        fullPath = os.path.join((path), (getpagetitle))
        fullPathPathmode = Path(fullPath)
        command = shlex.split('ffmpeg -y -i "'+finalm3u8+'" -c copy "'+fullPath +'" -loglevel error') 
        #command = ['ffmpeg','-y','-i', '"'+ finalm3u8 +'"','c copy',getpagetitle,'-hide_banner -report']
        print(" Checking if file exists, if it does it will be skipped")
        if fullPathPathmode.is_file():
            print(" File exists on disk, Location: " + fullPath+" \n Skipping download and muxing...")
            return True
        else:
            print("File dnot found, downloading...") 
            print("Phase 8-2: Running ffmpeg with the following command: "+ command.__str__())
            subprocess.run(command)
            print("Phase 8: Finished - Check script directory for the final output, generated file: " + str(pathlib.Path().resolve()) + fullPath)
            return True
        time.sleep(2)
        
        
    except Exception:
        print(traceback.format_exc())
        print("Error, Error launching sub-process or when processing and muxing the video streams")
        webDriver.close()
        webDriver.quit()
        
        sys.exit()



def start_service():
    if len(sys.argv) < 2:   
        print("Welcome to the basic BlueSky video Downloader")
        print("\n")
        print("No arguments provided. If you want help please run with -h or --help arguments or help. \n") 
        sys.exit()
    else:
        print(" Arguments provided: ", sys.argv)
        match sys.argv[1]:
            case ["-h" , "--help"]:
                print("BlueSky video Downloader Help: \n Command line arguments: \n python3 blueskydownloader.py -ARGUMENT -ADDRESS \n \n  Available Arguments in ARGUMENTS: -1 for single url download, -l"+ 
                    "for list. \n For ADDRESS in combination with argument -1 is a single url, for -l is a url list file. \n Enter username and password ina config.ini before using.  \n  For more than a single url, please use a list file named url_list.txt with one url per line. \n Requires: Selenium, WebDriver, ChromeDrive, Pathlib, json, traceback and a few more libraries.")
                
            case None:
                print("Welcome to the basic BlueSky video Downloader")
                print("\n")
                print("No arguments provided. If you want help please run with -h or --help arguments or help. \n")
                sys.exit()
                
            case ["-1", "--single"]:
                print("Welcome to the basic BlueSky video Downloader")
                print("\n using standard single download mode. \n")
                print("Arguments provided:  ", str(sys.argv))
                setChromeDriver()
                time.sleep(1)
                credentialsFile = checkFileConfig()  #returns tuple, currentpath and passCombo
                username = credentialsFile[0]
                password = credentialsFile[1]
                WebSite = sys.argv[2]
                mainProgram(WebSite,username,password)
                
                
            case ["-l", "--list"]:
                print("Welcome to the basic BlueSky video Downloader")
                print("\n using LIST mode. \n")
                print("Arguments provided:  ", str(sys.argv)  )
                setChromeDriver()
                credentialsFile = checkFileConfig()  #returns tuple, currentpath and passCombo
                username = credentialsFile[0]
                password = credentialsFile[1]
                WebSite = sys.argv[2]
                urlList = CheckUrlList() #returns list
                setLoop(urlList, username, password, )            
                
            case _:
                print("Invalid arguments provided. If you want help please run with -h or --help arguments or help. \n")
                sys.exit()    
                
def start_service2():
    print("Welcome to the basic BlueSky video Downloader")
    print("\n")
    while True:
        try:
            selectionOfMenu = int(input("Select the number of the argument you want to use: \n .-1 for single url download \n .-2 for list of urls \n .-3 for help \n"))
            break
        except ValueError:
            print("Invalid option detected. Please try again with a valid option. \n")
            
    match int(selectionOfMenu):
        case 3:
            print("BlueSky video Downloader Help: \n Command line arguments: \n python3 blueskydownloader.py -ARGUMENT -ADDRESS \n \n  Available Arguments in ARGUMENTS: -1 for single url download, -l"+ 
                "for list. \n For ADDRESS in combination with argument -1 is a single url, for -l is a url list file. \n Enter username and password ina config.ini before using.  \n  For more than a single url, please use a list file named url_list.txt with one url per line. \n Requires: Selenium, WebDriver, ChromeDrive, Pathlib, json, traceback and a few more libraries.")
            
        case None:
            #print("Welcome to the basic BlueSky video Downloader")
            #print("\n")
            print("Invalid option detected. Please try again with a valid option. None detected.\n")
            sys.exit()
            
        case 1:
            #print("Welcome to the basic BlueSky video Downloader")
            print("\n using standard single download mode. \n")
            #print("Arguments provided:  ", str(sys.argv))
            WebSite = input("Please insert the url of the website you want to download starting with a https://bsky.app url \n")
            webDriver = setChromeDriver()
            time.sleep(1)
            credentialsFile = checkFileConfig()  #returns tuple, currentpath and passCombo
            username = credentialsFile[0]
            password = credentialsFile[1]
            path = makeDirectory()
            mainProgram(WebSite,username,password, webDriver, path)
            
            
        case 2:
            #print("Welcome to the List based BlueSky video Downloader")
            print("\n using LIST mode. \n")
            webDriver = setChromeDriver()
            credentialsFile = checkFileConfig()  #returns tuple, currentpath and passCombo
            username = credentialsFile[0]
            password = credentialsFile[1]
            path = makeDirectory()
            #inputWebSite = input("Please insert the url of the website you want to download: \n")
            #WebSite = inputWebSite
            urlList = CheckUrlList() #returns list
            setLoop(urlList, username, password, webDriver, path)            
            
        case _:
            print("Invalid arguments provided. If you want help please run with -h or --help arguments or help. \n")
            sys.exit()  
                
start_service2()
