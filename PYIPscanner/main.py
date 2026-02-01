from scanner import scan
scan()

"""
                          Dev note:
    Yes, i know that this looks absolutely stupid and useless,
    however it MAY make the scanner faster because normally,
    python compiles every file except the file you run/execute
    into a .pyc file (Yes, python does that) and puts it in 
    __pycache__ folder. And because compiled program = faster
    i made this 2 line program that cannot really be any faster
    and forces python to compile the actual program and make it
    faster by .00000001 second on some devices.
    
"""