import os
import site
os.popen("sudo cp xenotables.py " + site.getsitepackages()[0])
print("Installed")
