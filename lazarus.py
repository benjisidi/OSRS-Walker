import numpy as np
import pyautogui as pag
from time import sleep, time
import cv2
import vision
import walker
from random import getrandbits

# Return a random # between low and high
def rand(low, high):
	return low + np.random.random() * (high-low)

# transform (top, left, height, width) coords to (top, left, bottom, right)
def HW2BR(coords):
	return (coords[0], coords[1], coords[2]+coords[0], coords[3]+coords[1])

# transform (top, left, bottom, right) coords to (top, left, height, width)
def BR2HW(coords):
	return (coords[0], coords[1], coords[2]-coords[0], coords[3]-coords[1])

# Convenience method for picking a random point on a button
def button_px(TLX, TLY, BRX, BRY):
	xPx = np.random.randint(TLX, BRX)
	yPx = np.random.randint(TLY, BRY)
	return (xPx, yPx)

# Pick a random pixel on a 3x3 node to click
def node_px(node):
	xPx = np.random.randint(node[0]-3, node[0]+3)
	yPx = np.random.randint(node[1]-3, node[1]+3)
	return (xPx, yPx)

# Moves mouse to coords and clicks.
def clk(x, y, button='left', tLow=.8, tHigh=2.1, click=True):
	t = rand(tLow, tHigh)
	pag.moveTo(x, y, t, pag.easeOutQuad)
	if click:
		pag.click(button=button)

# Types a string with human-like delays between keystrokes
def random_type(string):
	for char in string:
		pag.typewrite(char)
	t = rand(.48, 2.96)
	sleep(t)

# Move the mouse through the screen region containing the booths until "use bank" text is detected in the top right
# (by colour). Then click the bank booth.
def use_bank(location):
	search_region = bank_search_regions[location]
	search_pixels_x = range(search_region[0], search_region[0] + search_region[2], 30)
	search_pixels_y = range(search_region[1], search_region[1] + search_region[3], 38)
	banking = False
	x_i = 0
	y_i = 0
	while not banking:
		x = search_pixels_x[x_i%len(search_pixels_x)]
		y = search_pixels_y[y_i%len(search_pixels_y)]
		clk(x, y, tLow=0, tHigh=0, click=False)
		banking = vision.colour_in_region((2, 219, 217), (0, 32, 200, 25), tolerance=8)
		x_i += 1
		if x_i%len(search_pixels_x) == 0:
			y_i+=1
	clk(x, y, tLow=0, tHigh=0)
	sleep(rand(2.1, 2.5))

# Deposit everything in the inventory. Remove tools after doing so if necessary
def deposit_all(tools):
	deposit_button = HW2BR(tool_slots['deposit'] + (25, 25))
	clk(*button_px(*deposit_button))
	if tools != []:
		tool_tab = HW2BR(tool_slots['tool_tab'] + (25, 25))
		clk(*button_px(*tool_tab))
		for tool in tools:
			tool_slot = HW2BR(tool_slots[tool] + (25, 25))
			clk(*button_px(*tool_slot))
		# inf_tab = HW2BR(tool_slots['inf'] + (25, 25))
		# clk(*button_px(*inf_tab))


# Random mouse movement and right clicking
def random_mouse(reps, xmin=10, xmax=1270, ymin=10, ymax=700):
	click = 0 # getrandbits(1)
	move = getrandbits(1)
	x = np.random.randint(xmin, xmax)
	y = np.random.randint(ymin, ymax)
	t = rand(.5, 2.1)
	for i in range(reps):
		if click:
			clk(x, y, button='right')
		elif move:
			pag.moveTo(x, y, t, pag.easeOutQuad)
		sleep(rand(0.511, 4.145))
		click = getrandbits(1)
		move = getrandbits(1)
		x = np.random.randint(10, 1270)
		y = np.random.randint(10, 700)
		t = rand(.5, 2.1)

# Takes coordinates of an inventory slot and returns corresponding pixel coordinates
def inventory_coordinates(x, y):
	inv_coords = np.empty([4,7], dtype=tuple)
	dX = 9
	dY = 7
	slotW = 33
	slotH = 29
	for row in range(0, 7):
		slotY = 429 + row * (slotH + dY)
		for col in range(0, 4):
			slotX = 1077 + col * (slotW + dX)
			inv_coords[col, row] = (slotX, slotY, slotX + slotW, slotY + slotH)
	return inv_coords[x, y]


# Waits until character has stopped moving by checking
# the px next to the char in the minimap
# Might fail in VERY busy worlds
def move_wait():
	sleep(.2)
	red = np.array([0, 255, 255], dtype=np.uint8)
	check = True
	while check:
		minimap = np.array(pag.screenshot(region=(1119, 41, 154, 157)))
		minimapHSV = cv2.cvtColor(minimap,cv2.COLOR_RGB2HSV)
		mask=cv2.inRange(minimapHSV,red, red)
		flag = np.nonzero(mask)
		check = flag[0].size != 0
	sleep(1)

# Having arrived at a mine, find an active ore spot and triple click it to ensure movement.
# Avoids clicking on NPCS - this still fails/locks up occasionally
def walk_to_ore(rgb):
	print 'finding ore spot...'
	search_region = (153,53,880,497)
	mask = vision.colour_in_region(rgb, search_region, return_mask=True)
	LCC = vision.largest_connected(mask, search_region)
	while LCC is None:
		print 'waiting for ore to exist...'
		mask = vision.colour_in_region(rgb, search_region, return_mask=True)
		LCC = vision.largest_connected(mask, search_region)
		print 'ore spot found, moving...'
	pixel = np.random.randint(0, len(LCC))

	# Deals with NPCS
	blocked = not vision.colour_in_region((2, 219, 217), (0, 32, 200, 25), tolerance=8)
	if blocked:
		print 'Blocked by an NPC.'
	while blocked:
		pixel = np.random.randint(0, len(LCC))
		clk(*LCC[pixel], tLow=0.1, tHigh=0.3, click=False)
		blocked = not vision.colour_in_region((2, 219, 217), (0, 32, 200, 25), tolerance=8)
		if not blocked:
			sleep(.5)  # Accounts for jitters
			blocked = not vision.colour_in_region((2, 219, 217), (0, 32, 200, 25), tolerance=8)

	# Triple click ensures the player moves even if ore gets mined while clicking
	clk(*LCC[pixel])
	clk(*LCC[pixel], tLow=0, tHigh=.001)
	clk(*LCC[pixel], tLow=0, tHigh=.001)
	move_wait()


def mine_ore_spot(rgb):
	ore_present = False
	player_mask = cv2.imread('Assets/player_adjacent.bmp', 0)
	print "Looking for ore..."
	while not ore_present:
		search_region = (577, 321, 120, 112)
		mask = vision.colour_in_region(rgb, search_region, return_mask=True)
		mask = cv2.bitwise_and(mask, player_mask)
		LCC = vision.largest_connected(mask, search_region)
		if LCC is not None:
			ore_present=True
			print 'Found ore.'
	pixel = np.random.randint(0, len(LCC))
	clk(*LCC[pixel], tLow=0.1, tHigh=0.3, click=False)

	# Deals with NPCS
	blocked = not vision.colour_in_region((2, 219, 217), (0, 32, 200, 25), tolerance=8)
	if blocked:
		print 'Blocked by an NPC.'
	while blocked:
		pixel = np.random.randint(0, len(LCC))
		clk(*LCC[pixel], tLow=0.1, tHigh=0.3, click=False)
		blocked = not vision.colour_in_region((2, 219, 217), (0, 32, 200, 25), tolerance=8)
		if not blocked:
			sleep(.5) # Accounts for jitters
			blocked = not vision.colour_in_region((2, 219, 217), (0, 32, 200, 25), tolerance=8)
	clk(*LCC[pixel], tLow=0, tHigh=0)
	# Wait for spot to be mined
	mine_start = time()
	elapsed = 0
	while vision.colour_in_region(rgb, region=LCC, pixel_mode=True) and elapsed < 15: # break to prevent hanging
		elapsed = time() - mine_start

def mine_ore(mine_loc, bank_loc, ore, duration, nearest_node, worldmap, waypoint_graph):
	rgb = ore_colours[ore]
	# Walk to the mine
	nearest_node = walker.go(coords[mine_loc], nearest_node, worldmap, waypoint_graph)
	# Move to an ore spot
	walk_to_ore(rgb)
	# Give time for movement/spot to be mined
	sleep(rand(3, 4))
	starttime = time()

	while (time() - starttime)/60. < duration: # Duration is in minutes
		# Click to mine the spot
		mine_ore_spot(rgb)

		inventory_full  = vision.colour_in_region(rgb, region = inventory_coordinates(3, 6))
		if inventory_full:
			# Head back to bank and deposit
			nearest_node = walker.go(coords[bank_loc], nearest_node, worldmap, waypoint_graph)
			use_bank(bank_loc)
			sleep(rand(1.1,2.2))
			deposit_all(['picaxe'])
			# Head back to mine
			nearest_node = walker.go(coords[mine_loc], nearest_node, worldmap, waypoint_graph)
			sleep(rand(1.1,2.2))
			# Find a new spot and start again
			walk_to_ore(rgb)
			sleep(rand(3, 4))
			mine_ore_spot(rgb)
	return nearest_node

# Remove a full inventory of ores from the bank
def withdraw_ores(metal):
	ore_tab = HW2BR(tool_slots['ores'] + (25, 25))
	clk(*button_px(*ore_tab))
	for ore, amount in required_ores[metal].iteritems():
		button = HW2BR(ore_slots[ore] + (25, 25))
		x, y = button_px(*button)
		clk(x, y, button='right')
		x_offset = np.random.randint(0, 30)
		y_offset = np.random.randint(82, 90)
		x += x_offset
		y += y_offset
		clk(x, y)
		sleep(rand(1.5, 1.8))
		random_type(str(amount))
		pag.press('return')
		sleep(rand(1, 1.5))
		#inf_tab = HW2BR(tool_slots['inf'] + (25, 25))
		#clk(*button_px(*inf_tab))

# Check if the inventory is full or not by looking for whether the last slot contains the background colours
def inventory_complete(slot=(3,6)):
	return vision.compound_mask(BR2HW(inventory_coordinates(*slot)), [(59,50,38),(62,53,41),(64,54,44),(64,56,45)])


# Remove ores from bank, walk to forge, and make bars until inventory contains no more ore. Repeat for duration.
def smelt_ore(forge_loc, bank_loc, metal, duration, nearest_node, worldmap, waypoint_graph):
	start_time = time()
	while time() - start_time < duration*60:
		nearest_node = walker.go(coords[bank_loc], nearest_node, worldmap, waypoint_graph)
		use_bank(bank_loc)
		deposit_all([])
		withdraw_ores(metal)
		nearest_node = walker.go(coords[forge_loc], nearest_node, worldmap, waypoint_graph)
		use_bank(forge_loc)
		sleep(.5)
		random_type(str(smelt_commands[metal]))
		finished = inventory_complete(smelt_slots[metal])
		while not finished:
			# Levelling up breaks auto smelting so we have to restart it
			level_up = pag.pixelMatchesColor(228, 658, (0, 0, 255))
			if level_up:
				use_bank(forge_loc)
				sleep(.5)
				random_type(str(smelt_commands[metal]))
			finished = inventory_complete(smelt_slots[metal])

# Remove bars from bank, walk to anvil, and smith items until inventory contains no more bars. Repeat for duration.
def smith_item(anvil_loc, bank_loc, metal, item, duration, nearest_node, worldmap, waypoint_graph):
	start_time = time()
	while time() - start_time < duration*60:
		nearest_node = walker.go(coords[bank_loc], nearest_node, worldmap, waypoint_graph)
		use_bank(bank_loc)
		deposit_all([])
		withdraw_bars(metal) # <- ToDo: Write this
		nearest_node = walker.go(coords[anvil_loc], nearest_node, worldmap, waypoint_graph)
		use_bank(anvil_loc)
		sleep(.5)
		random_type(str(smelt_commands[metal]))
		finished = inventory_complete(smelt_slots[metal])
		while not finished:
			level_up = pag.pixelMatchesColor(228, 658, (0, 0, 255))
			if level_up:
				use_bank(anvil_loc)
				sleep(.5)
				random_type(str(smelt_commands[metal]))
			finished = inventory_complete(smelt_slots[metal])

# Resets the compass to North by
# holding a direction until the N is in
# the correct location
def reset_compass():
	pag.keyDown('right')
	while not pag.pixelMatchesColor(1117, 48, (131,10,11)):
		pass
	pag.keyUp('right')

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


# Set up global information
ore_colours = {'iron':(43, 22, 14), 'coal':(26,26,15)}
coords = {'Varrock_west_bank':(1227, 334), 'Varrock_west_mine':(1212, 625),'Edgeville_bank':(869, 136),
          'Barbarian_village_mine':(836,409), 'Falador_forge':(395, 619), 'Falador_west_bank':(286, 622)}

bank_search_regions = {'Edgeville_bank': (637,376, 398, 336), 'Varrock_west_bank': (654, 278, 386, 164),
                       'Falador_forge':(665,372,372,329), 'Falador_west_bank': (669, 399, 356, 321)}

tool_slots = {'tool_tab': (402, 78), 'inf':(323, 78), 'picaxe':(379, 115), 'axe': (331,115), 'hammer':(427,115),
              'fly fishing rod': (457,115), 'feathers':(524,115), 'deposit':(686,516), 'ores':(443,79)}

ore_slots = {'iron':(331, 115),'coal':(379, 115)}
required_ores = {'bronze': {'tin': 14, 'copper':14}, 'iron':{'iron':28}, 'silver':{'silver':28},
                 'steel':{'iron':9, 'coal':18,}, 'gold':{'gold':28}, 'mithril':{'mithril':5, 'coal':20},
                 'adamantite':{'adamantite':4, 'coal':24}, 'rune':{'rune':3, 'coal:':24}}
smelt_commands = {'bronze':1, 'iron':2, 'silver':3, 'steel':4, 'gold':5, 'mithril':6, 'adamantite':7, 'rune':8}
smelt_slots = {}
for metal in smelt_commands.keys():
	total = sum(required_ores[metal].itervalues())
	row = total/4 - 1 # of complete rows
	col = total % 4 # remaining ores
	if col == 0:
		slot = (3, row)
	else:
		slot = (col-1, row+1)
	smelt_slots[metal] = slot


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