**BLUE SKY BASIC DOWNLOADER for version 0.1p**

**What it is?** 🤔
- It is a simple script made in python, leveraging Selenium and Google Chrome to process the download of videos from the platform BlueSky (https://bsky.app/)

** What can I use it for? **
- It is pesky to use specific tools in your browser to download ONE VIDEO At a time and then have to deal with the quality.
- Or using dubious websites that add their watermark everywhere!
- This tool can automate downloading hundreds of videos from a list or just launch to download one.

** What are the requirements? **
- Any system that supports both Python( at least 3.X) and Selenium ( 4.X ), ffmpeg(to convert the files) and Chrome(to navigate and get the needed links).
- Internet Connection.
- This script was tested in Fedora based Nobara Linux ( 42 ) on x86 intel cpu. 
- an unlocked bluesky account. Unlocked as with the limitations removed ( For example, if you want to download adult videos from the platform, not judging mind you. You will need to enable adult content on the account itself) 🤷‍♂️
- The script by requires english on all tools. That includes Chrome, Selenium/Python.
- fill config.ini with your credentials in plain text.
- Optional: add the urls, one per line inside url_list.txt

** How does this script work? **
- It reads the required files (config.ini and url_list.txt).
- The first contains the username and password in plain text for the bluesky account you want to use.
- The url_list should contain all the bluesky video urls you want to process. But it is not needed if you only want to proceed a single video.
- Then it sets up the appropiate directories.
- Then launches Selenium using Chrome to boot up a headless version of chrome to try to login, check the video, and then use ffmpeg to convert.
- Easy peasy! 

** Found a bug? ** 🪚
Please report it! I have been chasing some shenaningans from Selenium along with Chrome with the particularities of Bluesky.
For example, I noticed that if I used chrome+selenium, the login page auto logins after setting up the password! With Standalone versions of Brave, Firefox and Chrome. They do not do this!.


** Usage **
first install the pre-requisites using the requirements.txt file
via: *pip install -r requirements.txt*
then: python3 singledownload.py
then select the mode:
- mode 1 will ask for a single url to download. 
- mode 2 will check the file url_list.txt for the files to download.
- mode 3 will just show the help file.

** Want to support me? ** 🎊
Awesome! you can throw a few to my paypal tamalero@gmail.com or payoneer 🥇


** notes ** 
- This is the first public revision of the script.

** TODO **
- Clean up the code for readability.
- Clean up the output to better inform the users of the progress.
- Make the code more resilient.
- Make the code more modular and tiddy. 

