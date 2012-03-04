#!/bin/env python
# Copyright (c) 2012 David Zwarg
# david.zwarg@gmail.com
# http://www.zwarg.com/
#
# A simple game for the OpenMoko phone, using pyGame and built in accelerometers.
import pygame, sys,os,struct
from pygame.locals import * 
 
pygame.init() 

# mostly default values, low buffer to reduce latency
pygame.mixer.init(22050, -16, 1, 1024)
 
window = pygame.display.set_mode((480,575)) 
pygame.display.set_caption('bounce') 
screen = pygame.display.get_surface() 
(width,height) = screen.get_size()

# accelerometer values
xaccel = 0
yaccel = 0
zaccel = 0

# accelerometer device
# see: http://wiki.openmoko.org/wiki/Accelerometer_data_retrieval
secondsensorfile = "/dev/input/event3"
#int, int, short, short, int
fmt = 'iihhi'
#open file in binary mode
in_file = open(secondsensorfile,"rb")
damping = 512.0
friction = 0.99

class Ball():
	"""
	A Ball object that is represented by a sprite, and has a contact
	sound when impacting the edges of the screen.
	"""
	def __init__(self):
		"""
		Create a new Ball object. This stores the Ball's position, old position,
		velocity vector, size, and impact sound.
		"""
		screen = pygame.display.get_surface()
		(w,h) = screen.get_size()
		self.x = w/2
		self.y = h/2
		self.oldx = w/2
		self.oldy = h/2
		self.vector = [ 0.0, 0.0 ]
		self.radius = 20
		# Turns out that wav files have less latency than ogg
		#self.ogg = pygame.mixer.Sound('/home/root/Metal_Hit.ogg')
		self.ogg = pygame.mixer.Sound('/home/root/bang_1.wav')
		self.prebounce = False
		self.pb_amt = 20

	def impulse(self, x, y):
		"""
		Give the Ball an impulse, based on some 2D inputs. This updates the Ball's
		position and velocity vector.
		
		@param x: The x impulse
		@param y: The y impulse
		"""
		self.oldx = self.x
		self.oldy = self.y

		# Update the velocity vector with the inputs.
		self.vector[0] = (self.vector[0] + x) * friction
		self.vector[1] = (self.vector[1] - y) * friction

		# Bounce off the right or left side.
		if ( self.x <= self.radius ) or (self.x >= width-self.radius):
			if ( self.x <= self.radius ):
				self.x = self.radius
			elif ( self.x >= width-self.radius ):
				self.x = width-self.radius
			self.vector[0] = self.vector[0] * (-0.9)

		# Bounce off the top or bottom side.
		if ( self.y <= self.radius ) or (self.y >= height-self.radius):
			if ( self.y <= self.radius ):
				self.y = self.radius
			if ( self.y >= height-self.radius ):
				self.y = height - self.radius
			self.vector[1] = self.vector[1] * (-0.9)

		# Anticipate that the Ball will hit the edge, and play the impact
		if ( (self.x + (self.vector[0] * self.pb_amt)) <= self.radius or (self.x + (self.vector[0] * self.pb_amt)) >= width-self.radius):
			if ( not self.prebounce ):
				self.ogg.play()
				self.prebounce = True
		# Anticipate that the Ball will hit the edge, and play the impact
		elif ( (self.y + (self.vector[1] * self.pb_amt)) <= self.radius or (self.y + (self.vector[1] * self.pb_amt)) >= height-self.radius):
			if ( not self.prebounce ):
				self.ogg.play()
				self.prebounce = True

		if (self.x <= self.radius) or (self.x >= width-self.radius):
			self.prebounce = False
		elif (self.y <= self.radius) or (self.y >= height-self.radius):
			self.prebounce = False

		self.x = self.x + self.vector[0]
		self.y = self.y + self.vector[1]

	def draw(self):
		"""
		Draw the Ball sprite on the screen, and return the rectangles/areas of
		the screen that need to be updated (erased or drawn upon).
		
		@returns: An array of rectangles that should be redrawn.
		"""
		rects = []
		rects.append( pygame.draw.circle( screen, ( 0, 0, 0 ), ( int(round(self.oldx)), int(round(self.oldy)) ), self.radius, 0 ) )
		rects.append( pygame.draw.circle( screen, ( 51, 51, 51 ), ( int(round(self.x)), int(round(self.y)) ), self.radius, 0 ) )
		rects.append( pygame.draw.circle( screen, ( 102, 102, 102 ), ( int(round(self.x-1)), int(round(self.y-1)) ), self.radius-2, 0 ) )
		rects.append( pygame.draw.circle( screen, ( 153, 153, 153 ), ( int(round(self.x-2)), int(round(self.y-2)) ), self.radius-4, 0 ) )
		rects.append( pygame.draw.circle( screen, ( 203, 204, 204 ), ( int(round(self.x-3)), int(round(self.y-3)) ), self.radius-6, 0 ) )
		rects.append( pygame.draw.circle( screen, ( 255, 255, 255 ), ( int(round(self.x-4)), int(round(self.y-4)) ), self.radius-8, 0 ) )
		self.rect = rects[1]
		return rects

class Axis():
	"""
	An object that represents a 3D vector representation.
	"""
	def __init__(self, x_clr, y_clr, z_clr):
		"""
		Create a new Axis indicator.
		
		@param x_clr: The color of the X axis
		@param y_clr: The color of the Y axis
		@param z_clr: The color of the Z axis
		"""
		self.position = (0,0)
		self.value = (0,0,0)
		self.oldvalue = (0,0,0)
		self.screen = pygame.display.get_surface()
		self.area = screen.get_rect()
		(self.width,self.height) = screen.get_size()
		self.color = ( x_clr, y_clr, z_clr )
		self.center = (self.width/2, self.height/2)
		
	def update(self,x,y,z):
		"""
		Update the axis, based on the provided accelerometer inputs.
		
		@param x: The X measurement
		@param y: The Y measurement
		@param z: The Z measurement
		"""
		(cx, cy) = self.center
		self.oldvalue = self.value
		self.value = ( (x*(cx)/2048), (y*(cx)/2048), (z*(cx)/2048) )
		
	def draw(self):
		"""
		Draw the Axis on the screen, and return the rectangles to be updated.
		
		@returns: An array of rectangles to be erased or drawn.
		"""
		(xclr, yclr, zclr) = self.color
		(cx,cy) = self.center
		rects = []

		(x,y,z) = self.oldvalue

		# erase old x axis
		w = x/20
		rects.append( pygame.draw.line( self.screen, (0,0,0), (cx,cy-w), (cx,cy+w), 1 ) )       # |
		rects.append( pygame.draw.line( self.screen, (0,0,0), (cx,cy+w), (cx+x,cy+w), 1 ) )     # -
		rects.append( pygame.draw.line( self.screen, (0,0,0), (cx+x,cy+w), (cx+x,cy-w), 1 ) )   # -
		rects.append( pygame.draw.line( self.screen, (0,0,0), (cx+x,cy-w), (cx,cy-w), 1 ) )     # |

		w = y/20
		rects.append( pygame.draw.line( self.screen, (0,0,0), (cx-w,cy), (cx+w,cy), 1 ) )
		rects.append( pygame.draw.line( self.screen, (0,0,0), (cx+w,cy), (cx+w,cy-y), 1 ) )
		rects.append( pygame.draw.line( self.screen, (0,0,0), (cx+w,cy-y), (cx-w,cy-y), 1 ) )
		rects.append( pygame.draw.line( self.screen, (0,0,0), (cx-w,cy-y), (cx-w,cy), 1 ) )

		(x,y,z) = self.value

		# draw new x axis
		w = x/20
		rects.append( pygame.draw.line( self.screen, xclr, (cx,cy-w), (cx,cy+w), 1 ) )       # |
		rects.append( pygame.draw.line( self.screen, xclr, (cx,cy+w), (cx+x,cy+w), 1 ) )     # -
		rects.append( pygame.draw.line( self.screen, xclr, (cx+x,cy+w), (cx+x,cy-w), 1 ) )   # -
		rects.append( pygame.draw.line( self.screen, xclr, (cx+x,cy-w), (cx,cy-w), 1 ) )     # |

		w = y/20
		rects.append( pygame.draw.line( self.screen, yclr, (cx-w,cy), (cx+w,cy), 1 ) )
		rects.append( pygame.draw.line( self.screen, yclr, (cx+w,cy), (cx+w,cy-y), 1 ) )
		rects.append( pygame.draw.line( self.screen, yclr, (cx+w,cy-y), (cx-w,cy-y), 1 ) )
		rects.append( pygame.draw.line( self.screen, yclr, (cx-w,cy-y), (cx-w,cy), 1 ) )

		return rects;
 
def input(events):
	"""
	An input event handler, called once every 'frame' to get the reading off
	the accelerometer.
	"""
	for event in events: 
		if event.type == QUIT: 
			sys.exit(0)
			in_file.close()
		if event.type == KEYDOWN and event.unicode == 'q':
			sys.exit(0)
			in_file.close()
		if event.type == MOUSEBUTTONUP:
			# Click anywhere to reset the ball to the middle of the screen
			ball.x = width/2
			ball.oldx = ball.x
			ball.y = width/2
			ball.oldy = ball.y
			ball.vector = [0.0,0.0]
			screen.fill( (0,0,0) )
			pygame.display.update( screen.get_rect() )
			
# Begin the main execution loop
event = in_file.read(16)
ball = Ball()
axis = Axis( (255,0,0), (0,255,0), (0,0,255) )
while event:
	(time1,time2, type, code, value) = struct.unpack(fmt,event)
	
	if type == 2 or type == 3:
		if code == 0:
			xaccel = value
		if code == 1:
			yaccel = value
		if code == 2:
			zaccel = value
	elif type == 0 and code == 0:
		ball.impulse( xaccel/damping, yaccel/damping )
		axis.update( xaccel, yaccel, zaccel )

		screen.lock()
		rects = ball.draw()
#		rects.extend( axis.draw() )

		pygame.display.update( rects )
		screen.unlock()
		
	input(pygame.event.get())
	event = in_file.read(16)
