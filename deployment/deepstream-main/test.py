import configparser

config_streammux = configparser.ConfigParser()
config_streammux.read("configs/test.txt")
config_streammux.sections()

print(config_streammux["property"])

for key,value in config_streammux.items("property"):
    print(key,value) 
    