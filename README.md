# Lazor_Project
This is a project aiming at solving different levels of the game 'LAZOR'
## Background
Lazor is a popular puzzle game in which you need to arrange blocks to let the laser pass though the desire targets. You can get this game on App Store. The difficulty of each level is labelled in the game, and in specific, we will solve these levels: dark_1, mad_1, mad_4, mad_7, numbered_6, showstopper_4, tiny_5, and yarn_5. 

## How to use it?
Get the .bff file of the level you want to play and read it in the code to solve. A standard .bff should look like this:  
***The following demonstration content does not represent the actual level***
```
GRID START
x o o
o o o
o o x
GRID STOP

B 3

L 3 0 -1 1
L 1 6 1 -1
L 3 6 -1 -1
L 4 3 1 -1

P 0 3
P 6 1
```
The grid should be placed between **GRID START** and **GRID STOP**.  
**A**: Reflect block  
**B**: Opaque block  
**C**: Refract block  
**L**: The first two numbers stand for the laser's start coordinates, the last two numbers stand for the laser's direction.  
**P**: The positions that lazers need to intersect.  

This script can solve puzzles really fast (less than 2 minute for each level). 
  

**White Block**: Reflective block  
**Black Block**: Opaque block  
**Red Block**: Refractive block  
**Lighter Gray Block**: The location where the block can be placed  
**Darker Gray Block**: The location where the block cannot be placed.  
**Hollow Red Circle**: The end point the laser needs to pass.  
**Solid Red Circle**: The place where the laser is emitted.  
**Red Line**: The optical path of the laser.  

## How does the code work?

In detail, the code begins by extracting the grid layout, block counts, laser starting points and directions, and the target points from the input bff file. It then “expands” the small grid into a full grid that accounts for half-step movements required for laser simulation. Next, it simulates the laser trajectories, applying reflections and refractions depending on the type of block encountered, using helper functions that decide how the beam changes direction. Finally, it systematically generates all candidate placements of movable blocks by considering every permutation of block types over available positions, checks for a configuration where every target point is hit by some laser path, and, if found, draws and saves an image of the solved puzzle.

