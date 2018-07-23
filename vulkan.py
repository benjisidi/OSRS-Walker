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
# Generate global list of tab coordinates
topRowYmin = 391
topRowYmax = 414
botRowYmin = 686
botRowYmax = 708
Xmin = 1042
width = 31
offset = 2

topKeys = ['Combat','Stats','Quests', 'Inventory', 'Equipment','Prayer','Spells']
botKeys = ['Clan', 'Friends','Blocked','Logout','Settings','Emotes','Music']

tabKeys = topKeys + botKeys

topVals = [(Xmin + i*(width+offset), topRowYmin,
			Xmin + i*(width+offset)+width, topRowYmax) for i,_ in enumerate(topKeys)]
botVals = [(Xmin + i*(width+offset), botRowYmin,
			Xmin + i*(width+offset)+width, botRowYmax) for i,_ in enumerate(botKeys)]

tabCoords = {}
for l in ((topKeys, topVals), (botKeys, botVals)):
	for i, key in enumerate(l[0]):
		tabCoords[key] = l[1][i]

# Declare in-tab coords

# ---Logout---
tabCoords['Logout Button'] = (1090, 620, 1220, 645)
tabCoords['World Switcher'] = (1090, 560, 1220, 585)

# ---Skills---
skillKeys = ['Attack', 'Strength', 'Defence', 'Range', 'Prayer', 'Magic',
			'Runecraft', 'Construction', 'HP', 'Agility', 'Herblore',
			'Theiving', 'Crafting', 'Fletching', 'Slayer', 'Hunting',
			'Mining', 'Smithing', 'Fishing', 'Cooking', 'Firemaking',
			'Woodcutting', 'Farming']
skillCenters = [(1093, 436), (1093, 467), (1093, 498)
					,(1093, 529), (1093, 560), (1093, 591)
					,(1093, 622), (1093, 653), (1156, 436)
					,(1156, 467), (1156, 498), (1156, 529)
					,(1156, 560), (1156, 591), (1156, 622)
					,(1156, 653), (1219, 436), (1219, 467)
					,(1219, 498), (1219, 529), (1219, 560)
					,(1219, 591), (1219, 622)]
xOff = 60
yOff = 30  # Skill boxes are 60x30px
for i, key in enumerate(skillKeys):
	tabCoords[key] = (skillCenters[i][0] - .5*xOff, skillCenters[i][1] - .5*yOff,
					  skillCenters[i][0] + .5*(xOff-1), skillCenters[i][1] + .5*(yOff-1))
tabCoords['Close Skill'] = (743, 131, 765, 153)


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

# Open the stat tab, click a random stat, wait and then close the window
def check_stats():
	stat = skillKeys[np.random.randint(0, len(skillKeys))]
	clk(*button_px(*tabCoords['Stats']))
	clk(*button_px(*tabCoords[stat]))
	random_mouse(5)
	clk(*button_px(*tabCoords['Close Skill']))
	clk(*button_px(*tabCoords['Inventory']))

# Open a random tab on the UI
def random_tab():
	tab = tabKeys[np.random.randint(0, len(tabKeys))]
	clk(*button_px(*tabCoords[tab]))
	random_mouse(5)
	clk(*button_px(*tabCoords['Inventory']))

def logout():
	clk(*button_px(*tabCoords['Logout']))
	clk(*button_px(*tabCoords['Logout Button']))

# Resets the compass to North by 
# holding a direction until the N is in
# the correct location
def reset_compass():
	pag.keyDown('right')
	while not pag.pixelMatchesColor(1117, 48, (131,10,11)):
		pass
	pag.keyUp('right')




nearest_node, worldmap, waypoint_graph  = setup(login=False, resize=True)