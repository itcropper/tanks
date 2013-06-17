
import numpy as np
from numpy import linalg as LA
import math

class Tank:

	def __init__(self, tank):
		self.setTank(tank)
		self.init_kalman()
		self.path = []

	def setTank(self, tank):
		self.x = tank.x
		self.y = tank.y
		self.angle = tank.angle
		
		try:
			self.index = tank.index
			self.shots_avail = tank.shots_avail
			self.time_to_reload = tank.time_to_reload
			self.team = 0
			self.vx = tank.vx
			self.vy = tank.vy
			self.angvel = tank.angvel

		except AttributeError:
			self.team = 1
		
		self.callsign = tank.callsign
		self.status = tank.status
		self.flag = tank.flag

		self.ticker = 0

		self.hist = []

	def historyCheck(self, position):
		if len(self.hist) > 10:
			self.hist.pop()
			self.hist.insert(0, position)

		if len(self.hist) >= 10 and self.hist[0] == self.hist[-1]:
			print "Tank: " + str(self.callsign) + " is stuck"
			return True
		else:
			return False

	def set_world_size(self, ws):
		self.world_size = ws

	def set_path(self, path):
		self.path = path

	def update(self, tank):
		#print tank.x, tank.y
		self.x = tank.x
		self.y = tank.y
		self.angle = tank.angle
		self.status = tank.status
		self.flag =  tank.flag
		

	def update_kalman(self, dT):

		self.updateZt()

		const = self.F(dT)*self.sigma*np.transpose(self.F(dT)) + self.sig0

		self.nextMu(dT, const)
		self.nextSig(dT, const)

	def nextK(self, dT, const):
		Ht = np.transpose(self.H)
		t = ((const)
			*Ht
			*LA.inv(self.H 
				*const
				*Ht
				+self.SigZ))
		return t


	def nextMu(self, dT, const):
		self.mu = (self.F(dT) 
					* self.mu 
					+ self.nextK(dT, const) 
					* (self.Zt 
						- (self.H 
							* self.F(dT) 
							* self.mu)))


	def nextSig(self, dT, const):
		self.sigma = (np.identity(6) - self.nextK(dT, const) * self.H )* const


	def shoot(self, x, y, enemies):
		shouldShoot = False
		for enemy in enemies:
			pointTheta = math.atan2(enemy.x, enemy.y)
			
			ang = math.sqrt((enemy.x - self.x)**2 + (enemy.y - self.y)**2)
						
			angleTol = math.sqrt(math.atan2(3, ang)) / 5

			targetAngle = math.atan2(enemy.y - self.y, enemy.x - self.x)

			if abs(self.angle - targetAngle) < angleTol:
				shouldShoot = True
		# if shouldShoot:
			# print "SHOOT IT FOX!"
		# self.normalize_angle(math.atan2(y - self.y, x - self.x)  - self.angle) * 2.0

		return (self.index, 1, self.normalize_angle(math.atan2(y - self.y, x - self.x)  - self.angle) * 2.0, shouldShoot)

		

	def normalize_angle(self, angle):
		"""Make any angle be between +/- pi."""
		angle -= 2 * math.pi * int (angle / (2 * math.pi))
		if angle <= -math.pi:
			angle += 2 * math.pi
		elif angle > math.pi:
			angle -= 2 * math.pi
		return angle


	def init_kalman(self):
		self.mu=np.matrix([[self.x],
						   [0],
						   [0],
						   [self.y],
						   [0],
						   [0]])

		self.Xt = np.matrix([[0],
							 [0],
							 [0],
							 [0],
							 [0],
							 [0]])

		self.F = lambda delta	:np.matrix([[1,   delta, (delta**2)/2,	 0.0,		0.0,		  0.0],
											 [0.0,	 1,		delta,	 0.0,		0.0,		  0.0],
											 [0.0,	 0,			1,	 0.0,		0.0,		  0.0],
											 [0.0,   0.0,		  0.0,	   1,	  delta, (delta**2)/2],
											 [0.0,   0.0,		  0.0,	 0.0,		  1,		delta],
											 [0.0,   0.0,		  0.0,	 0.0,		  0,			1]])

		pCert = .1
		vCert = .1
		aCert = .2

		self.sigma  =  np.matrix([[pCert,0.0,  0.0,   0.0,   0.0,   0.0],
									[0.0,vCert,  0.0,   0.0,   0.0,   0.0],
									[0.0,  0.0,aCert,   0.0,   0.0,   0.0],
									[0.0,  0.0,  0.0, pCert,   0.0,   0.0],
									[0.0,  0.0,  0.0,   0.0, vCert,   0.0],
									[0.0,  0.0,  0.0,   0.0,   0.0, aCert]])

		self.sig0	=   np.matrix([[pCert,0.0,  0.0,   0.0,   0.0,   0.0],
									[0.0,vCert,  0.0,   0.0,   0.0,   0.0],
									[0.0,  0.0,aCert,   0.0,   0.0,   0.0],
									[0.0,  0.0,  0.0, pCert,   0.0,   0.0],
									[0.0,  0.0,  0.0,   0.0, vCert,   0.0],
									[0.0,  0.0,  0.0,   0.0,   0.0, aCert]])

		self.H = np.matrix([[1, 0, 0, 0, 0, 0],
							[0, 0, 0, 1, 0, 0]])

		self.Zt = np.matrix([[0, 0]])


	def setSigZ(self, variance):
		self.SigZ = np.matrix([[variance**2, 0],
							  [0, variance**2]])

	def updateZt(self):

		self.ticker += 1

		if self.ticker > 1000:
			self.resetMu(self.x, self.y)

		self.Zt = np.matrix([[self.x], [self.y]])



	def resetMu(self, x, y):
		self.mu=np.matrix([[x],
						   [0],
						   [0],
						   [y],
						   [0],
						   [0]])
		self.ticker = 0
		# print "RESET"


	def get_target(self, dT, shotSpeed, tank):

		dtime = 0
		predictedcoord = ((self.F(dT) * self.mu).item(0,0),(self.F(dT) * self.mu).item(3,0))

		xDist = (predictedcoord[0] - tank.x)**2
		yDist = (predictedcoord[1] - tank.y)**2
		dtime = math.sqrt( xDist + yDist) / shotSpeed

		shootAtMatrix = self.F(dtime ) * self.mu

		predictedcoord = (shootAtMatrix.item(0,0), shootAtMatrix.item(3, 0))

		#print shootAtMatrix

		return predictedcoord
