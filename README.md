## Execution Parameters

#### `--help`
* Prints out the available commands.

#### `--mock-gpio`
* This will import a mock GPIO class in place of the RPi GPIO control class. Allows for execution on a laptop (or any device that does not support GPIO).
* Example: `python3 main.py --mock-gpio`

#### `--remote-control`
* This will enable control of the machine from a terminal.
* Example: `python3 main.py --remote-control`

#### `--save-output`
* This will save all output to the runtime directory.
* Example: `python3 main.py --save-output`

#### `--capture-key-positions`
* Captures the key position images for visible square calibration.
* Example: `python3 main.py --capture-key-position-images`

#### `--capture-fcc-top`
* Captures an images assuming that the pieces are placed on the board. Used for calculating the fid coefficient map.

#### `--capture-fcc-base`
* Captures an images assuming that there are base markers for each piece placed on the board. Used for calculating the fid coefficient map.

#### `--calculate-fcc`
* Calculates the fid correction coefficients using the captured images.

#### `--determine-current-position`
* Determines the current position of the gantry by calibrating itself from where it is manually positioned.

#### `--capture-frame --no-distortion? --show-markers?`
* Captures a frame and saves it to the runtime directory. `--no-distortion` and `--show-markers` are optional flags.