# from InquirerPy import inquirer
# from pyfiglet import Figlet
# name = inquirer.text(message="what is your name : ").execute()

# f = Figlet(font="slant")
# print(f.renderText(f"\t{name}"))

# from rich import print
# from rich.console import Console
# console = Console()
# console.print("hello world", style="bold red")
# print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())

import json 

with open("zte_router_automation/mac_address.json", "r") as file:
    data = json.load(file)

print(data)
print()
print(data["OMCP-DMG-001"])