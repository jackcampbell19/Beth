
### Definitions

- **Camera** -  A camera attached to the main arm of the machine, moves with the arm.

- **Piece** - Any chess piece on the board.

- **Snapshot** - Image of part of the board.

- **Anchor** - Specific fiducials placed on the board with known positions. Spread out so that one will be present in each snapshot.


### Algorithms

1. Move to a given marker
* Take a snapshot of the board
* If the target marker is not in the snapshot, move the arm to a random location on the board until the target piece is in the snapshot
* Calculate the vector between the current position and the target location in the snapshot and move the arm along that vector
* Repeat until the marker is within a bounding box of the center of the snapshot
