## Execution Parameters
#### `--mock-gpio`
* This will import a mock GPIO class in place of the RPi GPIO control class. Allows for execution on a laptop (or any device that does not support GPIO).
* Example: `python3 main.py --mock-gpio`

#### `--remote-control`
* This will enable control of the machine from a terminal.
* Example: `python3 main.py --remote-control`

#### `--save-output`
* This will save all output to the runtime directory.
* Example: `python3 main.py --save-output`

#### `--capture-key-position-images`
* Captures the key position images for visible square calibration.
* Example: `python3 main.py --capture-key-position-images`