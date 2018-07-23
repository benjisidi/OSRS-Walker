import win32gui as w32
from lazarus import *
import cv2
import walker
from ast import literal_eval
'''
ToDo
	- Implement find_nearest_dirty in mining
	- For navigation can use accurate version
'''
password = '********'

# Returns a list of the hwnd and titles of open windows
def win_enum_handler(hwnd, outArray):
	outArray.append((hwnd, w32.GetWindowText(hwnd)))


def setup(login=True, resize=True):
	if resize:
		# ---Grab OSRS window and place it---
		windows = []
		w32.EnumWindows(win_enum_handler, windows)
		for i in windows:
			if 'OSBuddy Free' in i[1]:
				osbuddyID = i[0]
				w32.ShowWindow(osbuddyID, 5)
				w32.SetForegroundWindow(osbuddyID)
		try:
			osbuddyID # Check if exists
		except NameError:
			print "Can't find OSBuddy window."
			exit()

		# Move window to 0, 0 and Resize to 720p
		w32.MoveWindow(osbuddyID, 0, 0, 1280, 720, False)
	if login:
		# ---Log in---
		# Cick "Existing User" and type password
		# Then click "log in" and "Click here to play"
		clk(*button_px(646, 305, 790, 343))
		random_type(password) # Password declared at top of file
		clk(*button_px(491, 337, 626, 371))
		sleep(2)
	worldmap = cv2.imread('Assets/f2p_world_map.png')
	nearest_node_file = open('nearest_node.txt')
	nearest_node = nearest_node_file.readline()
	nearest_node = literal_eval(nearest_node)
	waypoint_graph = walker.generate_graph('Assets/f2p_navmap.png', 'Assets/f2p_nodes.png')
	if login:
		clk(*button_px(532, 329, 750, 407))

	pag.keyDown('up')
	sleep(2.5)
	pag.keyUp('up')
	return  nearest_node, worldmap, waypoint_graph


def logout():
	clk(*button_px(*tabCoords['Logout']))
	clk(*button_px(*tabCoords['Logout Button']))


nearest_node, worldmap, waypoint_graph  = setup(login=False, resize=True)