#!/usr/bin/env python
import numpy as np
import rospy
from std_msgs.msg import Float32, Bool, Int32
from sensor_msgs.msg import Image
import threading
import cv2
from cv_bridge import CvBridge, CvBridgeError

class checkRect:
	def __init__(self):
		# init the node
		rospy.init_node("checkRect")
		# init the pubs and subs
		self.img_sub = rospy.Subscriber("/camera/rgb/image_rect_color",\
               		Image, self.cbImage)
		self.angle_pub = rospy.Publisher("/steer_angle",\
			Float32, queue_size=3)		
		self.done_pub = rospy.Publisher("/rect_done",Bool, queue_size=1)
		self.color_pub = rospy.Publisher("/color", Int32, queue_size=1)

		self.flag = True
		self.color = None # 0 is red, 1 is green

		self.RED_LOWER = np.array([7,100,180])
		self.RED_UPPER = np.array([15,255,255])
		self.GRN_LOWER = np.array([67,100,100])
		self.GRN_UPPER = np.array([77,255,255])
		self.final_lower = None
		self.final_upper = None

        def cbImage(self,image_msg):
		if self.flag == False:
			rospy.signal_shutdown("Done with task (checkRect)")
			return
		rospy.loginfo("cbImage")        
		thread = threading.Thread(target=self.processImage,args=(image_msg,))
		thread.setDaemon(True)
		thread.start()

   	def contour(self, image_cv):
		hsv = cv2.cvtColor(image_cv, cv2.cv.CV_BGR2HSV)	# convert to hsv
		if self.color == None:

			binMask = cv2.inRange(hsv, RED_LOWER, RED_UPPER) # take red mask
			binMask2 = cv2.inRange(hsv, GRN_LOWER, GRN_UPPER) # take green mask 

			contours_red, _  = cv2.findContours(binMask, cv2.cv.CV_RETR_EXTERNAL, cv2.cv.CV_CHAIN_APPROX_SIMPLE) # red contour
			contours_grn, _ = cv2.findContours(binMask2, cv2.cv.CV_RETR_EXTERNAL, cv2.cv.CV_CHAIN_APPROX_SIMPLE) # green contour
			
			for c in contours_red: 
				if cv2.contourArea(c) > 2000: 
					self.color == 0 
				else: self.color == 1 # if big red thing is there, red is color, else green
			if self.color == 0: # sets mask bounds for red
				self.final_lower = self.RED_LOWER 
				self.final_upper = self.RED_UPPER
			else: # sets mask bounds for green
				self.final_lower = self.GRN_LOWER
				self.final_upper = self.GRN_UPPER
			self.color_pub.publish(self.color)

		binMask = cv2.inRange(hsv, self.final_lower, self.final_upper) # binary mask
		masked = cv2.bitwise_and(hsv,hsv,mask=binMask) 
	
		contours, _ = cv2.findContours(binMask,cv2.cv.CV_RETR_EXTERNAL,cv2.cv.CV_CHAIN_APPROX_SIMPLE) # contouring
		print len(contours)
		for c in contours:
			#print "contour loop"
			x,y,w,h = cv2.boundingRect(c) # find the rect around the contour
			if w*h < 2000: # if too small, pay no attention
				#print "cont'd"
				continue
			elif w*h > 1e5: # if too big, end the node
			
				self.flag == False
				continue
			msg = x + 0.5 * w # finds x val of center of contour 
			#cv2.rectangle(image_cv, (x,y),(x+w, y+h),(0,255,0),2)

		if self.flag == False: # if we're done
			self.done_pub.publish(self.flag) # say we're done
			return
		error = msg - 640 # distance from center
		self.angle_pub.publish(error * -0.01) # publishes P controlled angle for driving 
		
		

		#cv2.imshow("masked",image_cv)
		#cv2.waitKey(0)
		#cv2.destroyAllWindows()
	
	
        def processImage(self, image_msg):
		if not self.thread_lock.acquire(False):
		    return
		image_cv = self.bridge.imgmsg_to_cv2(image_msg)
		try:
			print "tried"            
			self.contour(image_cv)
		    
		except CvBridgeError as e:
		    print(e)
		self.thread_lock.release()
if __name__ == "__main__":
	rospy.init_node("checkRect")
	e = checkRect()
	rospy.spin()

		
		
