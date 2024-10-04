#!/usr/bin/env python3

import os
import sys
import subprocess
import click
from pathlib import Path
from typing import Dict, Any
from colorama import Fore
from pyfiglet import Figlet
import platform

def main():
    if len(sys.argv) != 3:
        print("Usage: {} <input_file> <output_directory>".format(sys.argv[0]))
        sys.exit(1)
        
    click.echo(Figlet(justify='center').renderText("DUPLEX M2"))
    input_file = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.isfile(input_file):
        print(f"Input file not found: {input_file}")
        sys.exit(1)

    if not os.path.isdir(output_dir):
        print(f"Output directory not found, creating: {output_dir}")
        os.makedirs(output_dir)

    if platform.system() == "Windows":
        slicer_path = r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"
    else:
        try:
            slicer_path = subprocess.check_output(["locate", "PrusaSlicer.AppImage"]).decode().strip()
        except subprocess.CalledProcessError:
            print("Error: Could not find prusa-slicer-console.exe.")
            sys.exit(1)

    rotater_path = subprocess.check_output(["locate", "ROT_MIR_M2.py"]).decode().strip()

    command1 = [
        'python3',
        rotater_path,
        '-simplex', 'False',
        '-input', input_file,
        '-output', output_dir,
        '-log', output_dir
        
    ]
    
    # Run the subprocess and capture the exit code
    result1 = subprocess.run(command1)
    
    # Check exit code
    if result1.returncode not in (2, 3):
        print(f"Error: ROT_MIR_M2.py failed with exit code {result1.returncode}. Terminating.")
        sys.exit(result1.returncode)

    #----------------------------------------------------------------------------------------------
    #config file exists 
    cf = subprocess.check_output(["locate", "profil.ini"]).decode().strip()

    if os.path.isfile(cf):
        print(f"The config/profile file '{cf}' exists.")
    else:
        print(f"The config/profile file '{cf}' does not exist.")
    
    
    bare_filename = input_file.strip().split(".")
    bf=bare_filename[0].split("/")
    bf2="/"+bf[-1]
    stl_up = output_dir + bf2 + "_up." + bare_filename[1]
    
    profilefile='--load='+cf
    command2 = [
        slicer_path,
        '--slice', 
        '--dont-arrange',
        '--no-ensure-on-bed',
        '--export-gcode', 
        '--info',
        profilefile,
        stl_up
    ]

    result2=subprocess.run(command2)

    if result2.returncode != 0:
        print(f"Error: Prusa upper generation failed with exit code {result2.returncode}. Terminating.")
        sys.exit(result2.returncode)

    #----------------------------------------------------------------------------------------------
    #Generating lower gcode file from STL
    stl_down = output_dir + bf2 + "_down." + bare_filename[1]
    if os.path.exists(stl_down) == True:
        command3 = [
            slicer_path,
            '--slice', 
            '--dont-arrange',
            '--no-ensure-on-bed',
            '--export-gcode', 
            '--info',
            profilefile,
            stl_down
        ]
        result3=subprocess.run(command3)
        if result3.returncode != 0:
            print(f"Error: Prusa lower generation failed with exit code {result3.returncode}. Terminating.")
            sys.exit(result3.returncode)
    else:
        print("No lower file")
    #----------------------------------------------------------------------------------------------
    #Kawasaki robot code generation up
    g_file_up= output_dir + bf2 + "_up.gcode"
    outdir_pg="--output="+ output_dir +"/" 
    command4 = [
        'gcode2as', 
        g_file_up,
        '--inverted=False',
        outdir_pg
    ]
    result4=subprocess.run(command4)
    if result4.returncode != 0:
        print(f"Error: Gcode2as failed with exit code {result4.returncode}. Terminating.")
        sys.exit(result4.returncode)

    #----------------------------------------------------------------------------------------------
    #Kawasaki robot code generation down

    g_file_down= output_dir + bf2 + "_down.gcode"
    if os.path.exists(g_file_down) == True: 
        command5 = [
            'gcode2as', 
            g_file_down,
            '--inverted=True',
            outdir_pg
        ]
        result5=subprocess.run(command5)
        if result5.returncode != 0:
            print(f"Error: Gcode2as failed with exit code {result5.returncode}. Terminating.")
            sys.exit(result5.returncode)
    else:
        print("No lower part")
    click.echo(f'{Fore.MAGENTA}Program end{Fore.RESET}')


if __name__ == "__main__":
    main()
