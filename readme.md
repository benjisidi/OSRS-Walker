# OSRS Walker

This is a project aimed at having a computer play [*Old School Runescape*](https://oldschool.runescape.com), with the additional challenge of having it interface with the game in the same way a human would. The only information it has access to are screenshots of the game window. This may seem like an unreasonable restriction; directly interfacing with the game by using an API would be significantly easier and more effective - however this software is not intended to be used by anyone to *play* OSRS; it's simply born of intellectual curiosity and enjoyment of the challenge. Using an automaton to play the game is against the rules and I do not encourage anyone to do so. As a result, I'm going about this in a way that is fun to develop but will inevitably be much less useful to cheaters than the many existing bots.

## Usage

While there exist functions for withdrawing/depositing items from the bank, the only thing that works reliably at the moment is navigation. This can automatically walk a character between any two of the navigation nodes. You can see which areas have nodes by opening *Assets/f2p_navmap_with_nodes.png*.

If you wish to test the program's navigation, follow these steps: 

##### First-Time setup

- Open OSRS using [*OSBuddy*](https://rsbuddy.com/) and log in to your account
- Move to an existing node and write its coordinates in *nearest_node.txt* in the form "[y, x]" where y and x are the px coordinates of the node on the world map (*Assets/f2p_navmap_with_nodes.png*). Alternatively you can find a list of coordinates in the form "(x, y)" in the *coords* dictionary near the bottom of *lazarus.py*

##### General use

- Now that the program knows where you are, you can open *interface.py*, change the destination variable to the coordinates of your desired node and then run it. It will compute the shortest path through the graph and walk your character there using the minimap. The minimap **must be oriented north**.
- Each time the program walks you to a new node, it updates *nearest_node.txt*, so there's no need to do this manually after the first time, unless you walk your character somewhere else in the world yourself.

##### Dependencies

- win32GUI
- openCV
- tqdm
- pyautoGUI
- scikit-image
- numpy



## File Structure

| File/Folder                | Contents                                                     |
| -------------------------- | ------------------------------------------------------------ |
| dijkstra_shortest_path.py  | Contains vertex and graph objects, and a function for implementing dijkstra's shortest path. |
| interface.py               | Houses the functions for interacting with the OSBuddy window |
| lazarus.py                 | Houses all functions related to taking human-like action (moving the mouse, typing, clicking, and combinations thereof) |
| nearest_node.txt           | Records the node nearest to the last know player position    |
| vision.py                  | Houses all functions related to interpreting visual (screenshot) information from the game |
| walker.py                  | Houses all functions related to the navigation (graph traversal) system, with the exception of *dijkstra_shortest_path.py* |
| Assets/f2p_navmap.png      | A map isolating only impassable objects and terrain          |
| Assets/f2p_navmap.psd      | Multi-layer file with full colour map, only obstacles, and only navpoints |
| Assets/f2p_nodes.png       | The navpoint-only layer of the navmap                        |
| Assets/f2p_world_map.png   | Full colour world map                                        |
| Assets/player_adjacent.bmp | Mask of only game squares directly adjacent to the player    |


## Future Improvements

This project is being (slowly) developed to add more function and push what's possible while only interpreting screenshot data. There is no current concrete roadmap of what functions are to be implemented and when.

## Acknowledgements

- K Hong's implementation of dijkstra's shortest path on [bogotobogo](www.bogotobogo.com/python/python_Dijkstras_Shortest_Path_Algorithm.php) did precisely what I wanted pretty much out of the box, so *dijstra_shortest_path.py* is almost entirely his example.
- The function for finding the largest connected component in a binary image is a modification of *Sunreef's* [here](https://stackoverflow.com/questions/47055771/how-to-extract-the-largest-connected-component-using-opencv-and-python)
- The *line* function in *walker.py*, implementing Bresenham's line algorithm, is Luke Taylor's from [here](https://stackoverflow.com/questions/23930274/list-of-coordinates-between-irregular-points-in-python)