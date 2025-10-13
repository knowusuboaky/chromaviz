
        __                                  ______                      __            ___     
  _____/ /_  _________  ____ ___  ____ _   / __/ /___ _      __   _____/ /___  ______/ (_)___ 
 / ___/ __ \/ ___/ __ \/ __ `__ \/ __ `/  / /_/ / __ \ | /| / /  / ___/ __/ / / / __  / / __ \\
/ /__/ / / / /  / /_/ / / / / / / /_/ /  / __/ / /_/ / |/ |/ /  (__  ) /_/ /_/ / /_/ / / /_/ /
\___/_/ /_/_/   \____/_/ /_/ /_/\__,_/  /_/ /_/\____/|__/|__/  /____/\__/\__,_/\__,_/_/\____/ 


Author:	CoffeeCodeConverter
GitHub:	https://github.com/coffeecodeconverter

Project:	Chromw Flow Studio 
Github:	




==============================
System Requirements:
==============================
- ~300MB for the basic app, but ~1.7GB in Drive Space for all other libraries and dependancies (mainly torch)
- Python 3.10 (may also work in 3.11, but hasnt been tested)
- Pip 24.3.1
- VENV installed (optional, but HIGHLY, and STRONGLY recommended)
- ChromaDB 0.5.20+ to support hnsw config specified in metadata - tested and works on v0.6.1 too (latest as of writing this)
- Chroma-hnswlib==0.7.6+
- Set environment variable CHROMA_SERVER_CORS_ALLOW_ORIGINS=["*"]
- Check the requirements.txt for package version info 




PLEASE NOTE:
The "chromaviz" and "vite" folders are taken from the "chromaviz Github project" (https://github.com/mtybadger/chromaviz)
and arent required to run Chroma Flow Studio, but are a nice addition if you want to visualise your data





=====================
Install Instructions
=====================
NOTE:
Seeing as this is for windows, i like to create a ChromaDB folder under "C:\Program Files\ChromaDB" 
and install the client there as an offical appliation, then add the "Run.bat" as a shortcut to start meun
but you can install Chroma Flow Studio Anywhere. 


EASY METHOD:
- Amend the path in the VENV_Create.bat to point to your python 3.10 folder (where python.exe is)
- Then double click "VENV_Create.bat" to create virtual environment
- Double click "install.bat", it installs everything from requirements.txt 
- When finished, double click "Run.bat" to launch Chroma Flow Studio
- Enjoy!



OR
MANUAL METHOD

Do these commands directly in a seperate cmd window 
(so it stays open after each command below)


- in CMD, firstly, change to the directory where you decided to install this client. 
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  cd "C:\Path\to\where\you\decided\to\install"
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- assuming you already have python 3.10 installed, enter this command and press enter
  ~~~~~~~~~~~~~~~~~~~~
  python -m venv venv
  ~~~~~~~~~~~~~~~~~~~~
  (you dont need to activate the python environment, 
  because thats included in the .bat files in the steps below)

- invoke the "install.bat"
  (installs the requirements.txt for you)

- invoke the App with "Run.bat" 
  it runs a Flask Server and should auto-launch in a browser 
  (if not, copy and paste endpoint into a browser manually - default is 127.0.0.1:5000)











====================
OTHER NOTES
====================

the "import-files" sub-folder contains test .json files 
for 20, 50, and 2000 dummy documents respectively, for testing the import functions
and seeing how a system handles that much data. 


the "learn" sub-folder contains useful notes about embedding models, and chromadb syntax. 
It also contains a list of test scripts that get you up and running for your own projects. 
they isolate each task per script, like just creating a collection, just adding a document, 
just deleting a document, searching for a document, etc. 
you can copy and paste from them to quickly build your own python clients. 


default-config subfolder holds a default "appSettings.json" 
on first launch, it will copy this into the root directory 
if its ever missing, even from the default-config file, the app will write new config anyway, 
its hard coded. 

