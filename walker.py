from dijkstra_shortest_path import Graph, dijkstra, shortest
import cv2
import numpy as np
import pyautogui as pag
import vision
import lazarus

def R(a, b):
	return np.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def line(x0, y0, x1, y1):
	"""Bresenham's line algorithm: Return a list of intermediate points between start and end coordinates
	From Luke Taylor
	https://stackoverflow.com/questions/23930274/list-of-coordinates-between-irregular-points-in-python
	"""
	points_in_line = []
	dx = abs(x1 - x0)
	dy = abs(y1 - y0)
	x, y = x0, y0
	sx = -1 if x0 > x1 else 1
	sy = -1 if y0 > y1 else 1
	if dx > dy:
		err = dx / 2.0
		while x != x1:
			points_in_line.append((x, y))
			err -= dy
			if err < 0:
				y += sy
				err += dx
			x += sx
	else:
		err = dy / 2.0
		while y != y1:
			points_in_line.append((x, y))
			err -= dx
			if err < 0:
				x += sx
				err += dy
			y += sy
	points_in_line.append((x, y))
	return points_in_line

# Given two nodes on the navmap, check if there is "line of sight" (i.e. no obstacle between them)
# This prevents clicking on the other side of a very long wall
def see(a, b, map_):
	points = line(a[0], a[1], b[0], b[1])
	for point in points:
		if map_[point] > 0:
			return False
	return True


# Given a navmap and nodes, create a graph by connecting nodes that can 'see' eachother
def generate_graph(map_file, node_file):
	obstacle_map = cv2.imread(map_file, 0)
	node_map = cv2.imread(node_file, 0)
	nodes = np.argwhere(node_map>0)  # Argwhere is what causes weird notation
	g = Graph()
	for node in nodes:
		g.add_vertex(str(node))
	for node in nodes:
		neighbours = [x for x in nodes if (R(node, x) < 65) and (R(node, x) != 0) and
		            str(x) not in g.get_vertex(str(node)).get_connections()]
		for neighbour in neighbours:
			if see(node, neighbour, obstacle_map):
				g.add_edge(str(node), str(neighbour), R(node, neighbour))
	print 'Graph data:'
	'''for v in g:
		for w in v.get_connections():
			vid = v.get_id()
			wid = w.get_id()
			print '( %s , %s, %3d)' % (vid, wid, v.get_weight(w))'''
	return g



# Call diklstra's shortest path on two nodes in the graph.
def path(start, end, g):
	g = generate_graph('Assets/f2p_navmap.png', 'Assets/f2p_nodes.png')
	dijkstra(g, g.get_vertex(start))
	target = g.get_vertex(end)
	path = [target.get_id()]
	shortest(target, path)
	return path[::-1]

# Switch from node string notation to (x,y) coordinates
def node2coords(node):
	y = node[1:5]
	x = node[5:10]
	y = y.replace('[','')
	x = x.replace(']','')
	return (int(x), int(y))

# Switch from (x,y) coordinates to node string notation
# Don't know how 3-digit y and 4-digit x works yet; might cause bug
def coords2node(coords):
	x = str(coords[0])
	y = str(coords[1])
	if len(x) > len(y):
		y = ' ' + y
	elif len(y) > len(x):
		x = ' ' + x
	return '[' + y + ' ' + x + ']'


# Grab a screenshot of the minimap and fit it to the area around the nearest known node to determine player position
def orient(nearest_node, map_, debug=False):
	minimap = np.array(pag.screenshot(region=(1143, 61, 104, 112)))
	centre = nearest_node
	search_region = map_[centre[1]-75:centre[1]+75, centre[0]-75:centre[0]+75]
	#dirty_guess = vision.find_nearest_dirty(search_region, minimap)
	fast_guess = vision.find_nearest_fast(search_region, minimap)
	#best_guess = vision.find_nearest(search_region, minimap)
	#print 'dirty guess: {}\nfast guess: {}\nbest guess: {}\n'.format(dirty_guess, fast_guess, best_guess)
	if debug:
		cv2.imwrite('fast_guess.png',search_region)
		print fast_guess
	origin = (nearest_node[0]-75, nearest_node[1]-75)
	player_pixel = (fast_guess[0] + 52 + origin[0], fast_guess[1] + 56 + origin[1])
	return player_pixel

# Coordinate transformation from map coordinates to location on minimap
def map2minimap(coords, loc):
	minimap_loc = (1195, 117)
	disp = (coords[0] - loc[0], coords[1]-loc[1])
	minimap_coords = (disp[0] + minimap_loc[0], disp[1] + minimap_loc[1])
	return minimap_coords

# Coordinate transformation from map coordinates to location on minimap
def minimap2map(minimap_coords, loc):
	minimap_loc = (1195, 117)
	disp = (minimap_coords[0] - minimap_loc[0], minimap_coords[1]-minimap_loc[1])
	map_coords = (loc[0] + disp[0], loc[1] + disp[1])
	return map_coords

# Walk to a given node by computing djikstra's shortest path and then clicking on each node in turn on the minimap
def go(node, nearest_node, map_, graph):
	print 'Nearest node: ', nearest_node
	loc = orient(nearest_node, map_)
	print 'Nearest, target: ', coords2node(nearest_node), coords2node(node)
	route = path(coords2node(nearest_node), coords2node(node), graph)
	print route
	for waypoint in route:
		waypoint_coords = node2coords(waypoint)
		minimap_coords = map2minimap(waypoint_coords, loc)
		print loc
		print 'Waypoint coords: {}\nMinimap coords: {}\n'.format(waypoint_coords, minimap_coords)
		click_loc = lazarus.node_px(minimap_coords)
		lazarus.clk(*click_loc)
		lazarus.random_mouse(1)
		lazarus.move_wait()
		nearest_node = waypoint_coords
		loc = orient(nearest_node, map_)
	save = open('nearest_node.txt', 'w')
	save.write(str(waypoint_coords))
	print 'New nearest node: ', waypoint_coords
	return waypoint_coords


# Debugging
if __name__ == '__main__':
	mine = '[ 583 1200]'
	bank = '[ 334 1227]'
	lum = '[1214 1389]'
	a = node2coords(mine)
	print coords2node(a)
#generate_graph('Assets/f2p_navmap.png','Assets/f2p_nodes.png')

