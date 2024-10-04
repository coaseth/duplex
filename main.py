import io
from pathlib import Path
from typing import Dict, Any
import configparser
import click
import re
from colorama import Fore
from pyfiglet import Figlet
import subprocess

from gcode2as.cli import CLICommand, CLICommandOptions
from gcode2as.cli.fdm import FDM
from gcode2as.cli.laser_cut import LaserCut
from gcode2as.cli.metal import Metal
from gcode2as.formatter import format_program
from gcode2as import __version__

DEFAULT_MIN_DISTANCE = 2
DEFAULT_LINE_WIDTH = 2.4
DEFAULT_LAYER_HEIGHT = 1
DEFAULT_FIRST_LAYER_HEIGHT = 1.2
DEFAULT_USED_MATERIAL = 0
DEFAULT_PRINTING_TIME = 0

def read_input_parameters(file_path: str) -> configparser.ConfigParser:
    """Read input parameters from a given configuration file."""
    config = configparser.ConfigParser()
    file_path = subprocess.check_output(["locate", "input_parameters.txt"]).decode().strip()
    try:
        config.read(file_path)
        
        if not config.sections():
            raise configparser.MissingSectionHeaderError(file_path)
        
        return config  # Return the ConfigParser object here
    
    except Exception as e:
        print(f"Error reading parameters from {file_path}: {e}")
        return None  # Return None in case of an error

def update_parameters(config: configparser.ConfigParser, params: Dict[str, Any]) -> None:
    """Update parameters in the ConfigParser object and write back to the file."""
    for key, value in params.items():
        config['DEFAULT'][key] = str(value)  # Update or add new parameters
    
    with open('input_parameters.txt', 'w') as configfile:
        config.write(configfile)

def parse_options_ini(file_path: str) -> Dict[str, Any]:
    """Parse the options.ini file and return the parameters as a dictionary."""
    options = {}
    config = configparser.ConfigParser()
    config.read(file_path)

    if 'DEFAULT' in config:
        for key in config['DEFAULT']:
            options[key] = config['DEFAULT'].get(key)

    return options

def update_parameters_based_on_input(options: Dict[str, Any], welding_speed: float, line_width: float, layer_height: float, first_layer_height: float) -> None:
    """Update parameters based on input values."""
    if 'layer_height' in options:
        layer_height = float(options['layer_height'])
    
    if 'first_layer_height' in options:
        first_layer_height = float(options['first_layer_height'])
    
    if 'line_width' in options:
        line_width = float(options['line_width'])

    return welding_speed, line_width, layer_height, first_layer_height

def parse_3d_printing_stats(file_path: str) -> Dict[str, Any]:
    """Parse the file to extract estimated printing time, filament cost, and filament used."""
    stats = {
        'estimated_printing_time': None,
        'total_filament_cost': None,
        'total_filament_used': None
    }

    # Regular expressions to capture the values
    time_pattern = re.compile(r';\s*estimated printing time \(normal mode\)\s*=\s*(.*)')
    cost_pattern = re.compile(r';\s*total filament cost\s*=\s*(\d+\.?\d*)')
    filament_used_pattern = re.compile(r';\s*total filament used \[g\]\s*=\s*(\d+\.?\d*)')

    with open(file_path, 'r') as file:
        for line in file:
            time_match = time_pattern.search(line)
            cost_match = cost_pattern.search(line)
            filament_used_match = filament_used_pattern.search(line)

            if time_match:
                stats['estimated_printing_time'] = time_match.group(1).strip()
            if cost_match:
                stats['total_filament_cost'] = float(cost_match.group(1))
            if filament_used_match:
                stats['total_filament_used'] = float(filament_used_match.group(1))

    return stats

@click.command()
@click.argument('file', type=click.File())
@click.option('-d', is_flag=True, default=False, help="Use the default values for the options")
@click.option('-v', is_flag=True, default=False, help="More verbosity in the generated code")
@click.option('--mode', type=str, help='Mode of operation')
@click.option('--min_dist', type=float, help='Minimum distance')
@click.option('--vase_mode', type=bool, help='Vase mode flag')
@click.option('--welding_speed', type=float, help='Welding speed')
@click.option('--inverted', type=bool, help='Inverted flag')
@click.option('--output', type=str, help='Output directory')
@click.option('--line_width', type=float, help='Line width')
@click.option('--layer_height', type=float, help='Layer height')
@click.option('--first_layer_height', type=float, help='First layer height')
def cli(file: io.TextIOWrapper, d: bool, v: bool, mode, min_dist, vase_mode, welding_speed, inverted, output, line_width, layer_height, first_layer_height):
    # Display the fancy logo
    # click.echo(Figlet(justify='center').renderText("gcode2as by Lasram modded by Duplex3D"))

    # Available modes for the program
    modes: Dict[str, CLICommand] = {mode.message: mode for mode in [FDM(), Metal(), LaserCut()]}

    filepath = Path(file.name)
    filename = filepath.stem

    # Read the input parameters from the file
    config = read_input_parameters('input_parameters.txt')
    if config is None:
        return

    # Parse options.ini to get additional parameters
    options = parse_options_ini('options.ini')
    
    # Set default values for the parameters
    default_params = {
        'mode': 'Metal 3D Printing',
        'min_dist': DEFAULT_MIN_DISTANCE,
        'vase_mode': False,
        'welding_speed': 30.0,
        'inverted': False,
        'output': './',
        'line_width': DEFAULT_LINE_WIDTH,
        'layer_height': DEFAULT_LAYER_HEIGHT,
        'first_layer_height': DEFAULT_FIRST_LAYER_HEIGHT
    }

    # Create a dictionary to hold the parameters
    param_dict = {
        'mode': mode or default_params['mode'],
        'min_dist': min_dist if min_dist is not None else default_params['min_dist'],
        'vase_mode': vase_mode if vase_mode is not None else default_params['vase_mode'],
        'welding_speed': welding_speed if welding_speed is not None else default_params['welding_speed'],
        'inverted': inverted if inverted is not None else default_params['inverted'],
        'output': output or default_params['output'],
        'line_width': line_width if line_width is not None else default_params['line_width'],
        'layer_height': layer_height if layer_height is not None else default_params['layer_height'],
        'first_layer_height': first_layer_height if first_layer_height is not None else default_params['first_layer_height']
    }

    # Update parameters based on the parsed options from options.ini
    welding_speed, line_width, layer_height, first_layer_height = update_parameters_based_on_input(options, param_dict['welding_speed'], param_dict['line_width'], param_dict['layer_height'], param_dict['first_layer_height'])

    # Update config with new or default values, but don't overwrite already set ones
    for key, default_value in default_params.items():
        if key not in param_dict:  # If the param was not passed through CLI
            if key not in config['DEFAULT']:  # If not already set in config, set the default
                config['DEFAULT'][key] = str(default_value)
        else:
            config['DEFAULT'][key] = str(param_dict[key])  # Update with CLI provided param

    # Write the updated parameters back to the file
    update_parameters(config, param_dict)

    # Access parameters from the ConfigParser
    mode = config.get('DEFAULT', 'mode', fallback=default_params['mode'])
    min_distance = config.getfloat('DEFAULT', 'min_dist', fallback=default_params['min_dist'])
    use_different_output = config.getboolean('DEFAULT', 'use_different_output', fallback=False)
    out_dir = config.get('DEFAULT', 'output', fallback=None)

    # Validate mode
    if mode not in modes:
        click.echo(f"Error: The selected mode '{mode}' is not valid. Choose from: {', '.join(modes.keys())}.")
        return

    selected_mode = modes[mode]

    # Validate min_distance
    try:
        min_distance = float(min_distance)
    except ValueError:
        click.echo("Error: Minimum distance must be a valid number.")
        return

    # Execute the mode with given options
    lines_as = selected_mode.execute(
        options=CLICommandOptions(file=file, min_distance=min_distance, verbose=v, params=config)
    )
    if lines_as is None:
        return

    # Format the generated program
    formatted = format_program(lines_as, filename)

    # Determine output directory
    if out_dir is None:
        out_dir = filepath.absolute().parent

    out_path = Path(out_dir).joinpath(f'{filename}.pg')
    click.echo(f'Saving generated file as {Fore.GREEN}{out_path}{Fore.RESET}')

    with open(out_path, 'w', encoding='utf8') as f_open:
        f_open.write(formatted)

    def remove_semicolon_lines(input_file, output_file, welding_speed, line_width, layer_height, first_layer_height, stats: Dict[str, Any]):
        """Remove lines with semicolons and add header lines."""
        # Prepare the header lines with the given values and stats
        header_lines = [
            f"; Welding speed = {welding_speed}\n",
            f"; Line_width = {line_width}\n",
            f"; Layer_height = {layer_height}\n",
            f"; First_layer_height = {first_layer_height}\n",
            f"Estimated_printing_time = {stats['estimated_printing_time']}\n",
            f"Total_filament_cost = {stats['total_filament_cost']}\n",
            f"Total_filament_used = {stats['total_filament_used']}\n"
        ]

        # Regular expressions to match specific patterns for layer_height and first_layer_height
        layer_height_pattern = re.compile(r'^\t; layer_height\s*=\s*\S+')
        first_layer_height_pattern = re.compile(r'^\t; first_layer_height\s*=\s*\S+')

        # Open the input file for reading
        with open(input_file, 'r') as file:
            lines = file.readlines()

        cleaned_lines = []
        for line in lines:
            stripped_line = line.strip()
            # Check if the line contains a semicolon
            if ';' in stripped_line:
                # Check if it matches the specific pattern for layer_height or first_layer_height
                if layer_height_pattern.match(stripped_line) or first_layer_height_pattern.match(stripped_line):
                    cleaned_lines.append(line)
                else:
                    cleaned_line = stripped_line.split(';', 1)[0].strip()
                    if cleaned_line:
                        cleaned_lines.append(cleaned_line + '\n')
            else:
                cleaned_lines.append(line)

        # Write the header lines and cleaned lines to the output file
        with open(output_file, 'w') as file:
            file.writelines(header_lines)
            file.writelines(cleaned_lines)

    # Parse stats from the file
    stats = parse_3d_printing_stats(file.name)

    # Call remove_semicolon_lines with welding_speed, other params, and stats
    out_path2 = out_path
    remove_semicolon_lines(
        out_path, out_path2, welding_speed=welding_speed,
        line_width=line_width, layer_height=layer_height, first_layer_height=first_layer_height, stats=stats
    )

if __name__ == '__main__':
    cli()
