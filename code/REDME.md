
### Definitions

- **Gantry** - 3 dimensional mechanical structure used to move the camera and interact with the chess pieces.

- **fid** - 'Fiducial ID' aka. a marker identifier.

### Structure

- [calibration] - A directory containing code and images used to calibrate the machine.

- [runtime] - A directory containing any files generated during the operation of the program.

### config.json
The config.json file contains all variable information about the machine. This includes dimensions, fiducial associations, and calibration coefficients. The structure is as follows:

```
{
  "board-corner-fid-mapping": {
    "top-left": <fid>,
    "top-right": <fid>,
    "bottom-left": <fid>,
    "bottom-right": <fid>
  },
  "fid-piece-mapping": {
    <fid>: <chess-piece>,
    ...
  },
  "camera": {
    "width": <width>,
    "height": <height>,
    "calibration": {
      "k": <k-array>,
      "d": <d-array>,
      "fid-correction-coefficients": {
        "default": [<x-coeff>, <y-coeff>],
        <fid>: [<x-coeff>, <y-coeff>],
        ...
      }
    }
  },
  "gantry": {
    "size": [<width>, <height>],
    "x-pins": [<stp>, <dir>],
    "y-pins": [[<stp>, <dir>], ...]
  }
}
```