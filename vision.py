from skimage.measure import compare_ssim as ssim
import cv2
from time import time
from operator import itemgetter
from tqdm import tqdm
import pyautogui as pag
import numpy as np

# takes a 2d list_ and returns the argument of the inner list with the maximum value at position i
def max_val(list_, i):
	return max(enumerate(map(itemgetter(i), list_)),key=itemgetter(1))

# takes a 2d list_ and returns the argument of the inner list with the minimum value at position i
def min_val(list_, i):
	return min(enumerate(map(itemgetter(i), list_)),key=itemgetter(1))

# Takes a screenshot and grabs just the region around the player
def crop_around_player(image):
	iH, iW = image.shape
	centre = (int(iH/2), int(iW/2))
	return image[227:centre[0]+227, 274:centre[1]+274]

# Transforms coordinates from the image returned by crop_around_player back to the full screenshot
def cropped2full(coords):
	return (coords[0] + 274, coords[1] + 227)

# Take a sample and find its nearest match in an image using a structural similarity index
def find_nearest(image, sample):
	image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	sample = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)
	sH, sW = sample.shape
	iH, iW = image.shape
	results = []
	for x in tqdm(range(0, iW-sW)):
		for y in range(0, iH-sH):
			crop = image[y:y+sH,x:x+sW]
			s = ssim(crop, sample)
			results.append([x, y, s])
	maxVal = max_val(results, 2)
	return results[maxVal[0]]

# Take a region of a screenshot and return a mask of where any of the r,g,b values appear
def compound_mask(region, values):
	region_px = cv2.cvtColor(np.array(pag.screenshot(region=region),dtype='uint8'), cv2.COLOR_RGB2HSV)
	masks = []
	for rgb in values:
		hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV)[0][0]
		mask = cv2.inRange(region_px, hsv, hsv)
		masks.append(mask)
	stack = np.zeros([region[3], region[2]], dtype='uint8')
	for mask in masks:
		stack = cv2.bitwise_or(stack, mask)
	return stack[np.nonzero(stack)].size == stack.size


# Experiment: Rather than moving the template 1px at a time, move it 3px at a time, then take the best 3x3 candidate
# region and template match the 9px in that area to find the best one.
def find_nearest_fast(image, sample, dx=0, dy=0, bw=False):
	if not bw:
		image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		sample = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)
	sH, sW = sample.shape
	iH, iW = image.shape
	prelim_results = []
	for x in tqdm(range(0, iW-sW, 2)):
		for y in range(0, iH-sH, 2):
			crop = image[y:y+sH,x:x+sW]
			s = ssim(crop, sample)
			prelim_results.append([x, y, s])
	maxVal = max_val(prelim_results, 2)
	prelim_point = prelim_results[maxVal[0]]
	honed_results = []
	for x in tqdm(range(prelim_point[0]-3, prelim_point[0]+3)):
		for y in range(prelim_point[1]-3, prelim_point[1]+3):
			crop = image[y:y+sH,x:x+sW]
			try:
				s = ssim(crop, sample)
				honed_results.append([x, y, s])
			except ValueError:
				pass
	newMaxVal = max_val(honed_results, 2)
	coords = honed_results[newMaxVal[0]]
	return (coords[0] + dx, coords[1] + dy, int(coords[0] + sW) + dx, int(coords[1] + sH) + dy)

# Check if an rgb value appears in a region of a screenshot. Can take a list of pixels instead of a (top, left, width, height)
# region, can return a mask instead of a boolean, and can take a hue tolerance value
def colour_in_region(rgb, region, return_mask=False, pixel_mode=False, tolerance=None):
	if pixel_mode:
		x_max, y_max = region.max(axis=0)
		x_min, y_min = region.min(axis=0)
		region_sq = (x_min, y_min, max(x_max-x_min, 1), max(y_max-y_min, 1)) # Stops width/height erroneously being 0
		region_image = pag.screenshot(region=region_sq)
		region_px = cv2.cvtColor(np.array(region_image, dtype='uint8'), cv2.COLOR_RGB2HSV)
	else:
		region_px = cv2.cvtColor(np.array(pag.screenshot(region=region), dtype='uint8'), cv2.COLOR_RGB2HSV)
	hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV)[0][0]
	if tolerance is None:
		hsv_low = hsv_high = hsv
	else:
		target_colour_h = hsv[0]
		hsv_low = np.array([max(tolerance, target_colour_h) - tolerance, 50, 50])
		hsv_high = np.array([min(255 - tolerance, target_colour_h) + tolerance, 255, 255])
	mask = cv2.inRange(region_px, hsv_low, hsv_high)
	if return_mask:
		return mask
	return np.nonzero(mask)[0].size != 0


# Largest component - Sunreef on stackoverflow
# https://stackoverflow.com/questions/47055771/how-to-extract-the-largest-connected-component-using-opencv-and-python
# Modified: Takes biary image, returns px coords of largest connected region
def largest_connected(image, region):
	nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(image, connectivity=4)
	sizes = stats[:, -1]
	max_label = 1
	try:
		max_size = sizes[1]
	except IndexError:
		return None
	for i in range(2, nb_components):
		if sizes[i] > max_size:
			max_label = i
			max_size = sizes[i]
	return np.array([[x[2] + region[0], x[1] + region[1]] for x in np.argwhere([output == max_label])])


# Use the absolute difference instead of the SSIM to template-match. Much faster but less accurate.
def find_nearest_dirty(image, sample, dx=0, dy=0, bw=False):
	if not bw:
		image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		sample = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)
	sH, sW = sample.shape
	iH, iW = image.shape
	results = []
	for x in tqdm(range(0, iW-sW)):
		for y in range(0, iH-sH):
			crop = image[y:y+sH,x:x+sW]
			s = cv2.absdiff(crop, sample)
			results.append([x, y, s.mean()])
	minVal = min_val(results, 2)
	coords = (results[minVal[0]][0], results[minVal[0]][1])
	return (coords[0] + dx, coords[1] + dy, int(coords[0] + sW) + dx, int(coords[1] + sH) + dy)

# Benchmarking find_nearest_dirty algorithm. Test images not included in git to avoid clutter.
if __name__ == '__main__':
	test = cv2.imread('minetest_easy.png')
	icon = cv2.imread('tin.png')
	starttime = time()
	find_nearest_dirty(test, icon)
	endtime = time()
	print 'Finished in {}s'.format(endtime-starttime)