# -*- coding: utf-8 -*-

import logging
import time

from base import Application

class DeviceAbortException(Exception):
	pass

# pylint: disable=R0904,R0902,C0103
class Device(object):
	"""
	A base class for a device. Any plugin adding devices must subclass this class.
	"""
	TURNON = 1  #: Device flag for devices supporting the on method.
	TURNOFF = 2  #: Device flag for devices supporting the off method.
	BELL = 4     #: Device flag for devices supporting the bell method.
	TOGGLE = 8   #: Device flag for devices supporting the toggle method.
	DIM = 16     #: Device flag for devices supporting the dim method.
	LEARN = 32   #: Device flag for devices supporting the learn method.
	EXECUTE = 64 #: Device flag for devices supporting the execute method.
	UP = 128     #: Device flag for devices supporting the up method.
	DOWN = 256   #: Device flag for devices supporting the down method.
	STOP = 512   #: Device flag for devices supporting the stop method.
	RGB = 1024   #: Device flag for devices supporting the rgb method.
	RGBW = 1024  #: Device flag for devices supporting the rgb method, this is depricated, use RGB.
	THERMOSTAT = 2048  #: Device flag for devices supporting thermostat methods.

	TYPE_UNKNOWN = '0000000-0001-1000-2005-ACCA54000000'
	TYPE_ALARM_SENSOR = '0000001-0001-1000-2005-ACCA54000000'
	TYPE_CONTAINER = '0000002-0001-1000-2005-ACCA54000000'
	TYPE_CONTROLLER = '0000003-0001-1000-2005-ACCA54000000'
	TYPE_DOOR_WINDOW = '0000004-0001-1000-2005-ACCA54000000'
	TYPE_LIGHT = '0000005-0001-1000-2005-ACCA54000000'
	TYPE_LOCK = '0000006-0001-1000-2005-ACCA54000000'
	TYPE_MEDIA = '0000007-0001-1000-2005-ACCA54000000'
	TYPE_METER = '0000008-0001-1000-2005-ACCA54000000'
	TYPE_MOTION = '0000009-0001-1000-2005-ACCA54000000'
	TYPE_ON_OFF_SENSOR = '000000A-0001-1000-2005-ACCA54000000'
	TYPE_PERSON = '000000B-0001-1000-2005-ACCA54000000'
	TYPE_REMOTE_CONTROL = '000000C-0001-1000-2005-ACCA54000000'
	TYPE_SENSOR = '000000D-0001-1000-2005-ACCA54000000'
	TYPE_SMOKE_SENSOR = '000000E-0001-1000-2005-ACCA54000000'
	TYPE_SPEAKER = '000000F-0001-1000-2005-ACCA54000000'
	TYPE_SWITCH_OUTLET = '0000010-0001-1000-2005-ACCA54000000'
	TYPE_THERMOSTAT = '0000011-0001-1000-2005-ACCA54000000'
	TYPE_VIRTUAL = '0000012-0001-1000-2005-ACCA54000000'
	TYPE_WINDOW_COVERING = '0000013-0001-1000-2005-ACCA54000000'
	TYPE_PROJECTOR_SCREEN = '0000014-0001-1000-2005-ACCA54000000'

	UNKNOWN = 0                 #: Sensor type flag for an unknown type
	TEMPERATURE = 1             #: Sensor type flag for temperature
	HUMIDITY = 2                #: Sensor type flag for humidity
	RAINRATE = 4                #: Sensor type flag for rain rate
	RAINTOTAL = 8               #: Sensor type flag for rain total
	WINDDIRECTION = 16          #: Sensor type flag for wind direction
	WINDAVERAGE	= 32            #: Sensor type flag for wind average
	WINDGUST = 64               #: Sensor type flag for wind gust
	UV = 128                    #: Sensor type flag for uv
	WATT = 256                  #: Sensor type flag for watt
	LUMINANCE = 512             #: Sensor type flag for luminance
	DEW_POINT = 1024            #: Sensor type flag for dew point
	BAROMETRIC_PRESSURE = 2048  #: Sensor type flag for barometric pressure

	SCALE_UNKNOWN = 0
	SCALE_TEMPERATURE_CELCIUS = 0
	SCALE_TEMPERATURE_FAHRENHEIT = 1
	SCALE_HUMIDITY_PERCENT = 0
	SCALE_RAINRATE_MMH = 0
	SCALE_RAINTOTAL_MM = 0
	SCALE_WIND_VELOCITY_MS = 0
	SCALE_WIND_DIRECTION = 0
	SCALE_UV_INDEX = 0
	SCALE_POWER_KWH = 0
	SCALE_POWER_WATT = 2
	SCALE_LUMINANCE_PERCENT = 0
	SCALE_LUMINANCE_LUX = 1
	SCALE_BAROMETRIC_PRESSURE_KPA = 0

	FAILED_STATUS_RETRIES_FAILED = 1
	FAILED_STATUS_NO_REPLY = 2
	FAILED_STATUS_TIMEDOUT = 3
	FAILED_STATUS_NOT_CONFIRMED = 4
	FAILED_STATUS_UNKNOWN = 5

	BATTERY_LOW = 255  # Battery status, if not percent value
	BATTERY_UNKNOWN = 254  # Battery status, if not percent value
	BATTERY_OK = 253  # Battery status, if not percent value

	def __init__(self):
		super(Device, self).__init__()
		self._id = 0
		self._ignored = None
		self._loadCount = 0
		self._name = None
		self._manager = None
		self._state = Device.TURNOFF
		self._stateValue = ''
		self._sensorValues = {}
		self._confirmed = True
		self.valueChangedTime = {}
		self.lastUpdated = None  # internal use only, last time state was changed
		self.lastUpdatedLive = {}

	def id(self):
		return self._id

	def allParameters(self):
		"""
		Similar as parameters() but this returnes more values such as the device type
		"""
		params = self.parameters()
		params['devicetype'] = self.deviceType()
		return params

	def battery(self):  # pylint: disable=R0201
		"""
		Returns the current battery value
		"""
		return None

	# pylint: disable=R0913
	def command(self, action, value=None, origin=None, success=None,
	            failure=None, callbackArgs=None, ignore=None):
		"""This method executes a method with the device. This method must not be
		subclassed. Please subclass :func:`_command()` instead.

		  :param action: description
		  :return: return description

		Here below is the results of the :func:`Device.methods()` docstring.
		"""
		if callbackArgs is None:
			callbackArgs = []
		# Prevent loops from groups and similar
		if ignore is None:
			ignore = []
		if self.id() in ignore:
			return
		ignore.append(self.id())
		if isinstance(action, str) or isinstance(action, unicode):
			method = Device.methodStrToInt(action)
		else:
			method = action
		if method == Device.DIM:
			if value is None:
				value = 0  # this is an error, but at least won't crash now
			else:
				value = int(value)
		elif method == Device.RGB:
			if isinstance(value, str):
				value = int(value, 16)
			elif not isinstance(value, int):
				value = 0
			if action == 'rgbw':
				# For backwards compatibility, remove white component
				value = value >> 8
		elif method == Device.THERMOSTAT:
			pass
		else:
			value = None
		def triggerFail(reason):
			if failure:
				try:
					failure(reason, *callbackArgs)
				except DeviceAbortException:
					return
		def s(state=None, stateValue=None):
			if state is None:
				state = method
			if stateValue is None:
				stateValue = value
			if success:
				try:
					success(state=state, stateValue=stateValue, *callbackArgs)
				except DeviceAbortException:
					return
			self.setState(state, stateValue, origin=origin)

		if method == 0:
			triggerFail(0)
			return
		try:
			self._command(method, value, success=s, failure=triggerFail, ignore=ignore)
		except Exception as error:
			Application.printException(error)
			triggerFail(0)

	# pylint: disable=R0201,W0613
	def _command(self, action, value, success, failure, **__kwargs):
		"""Reimplement this method to execute an action to this device."""
		failure(0)

	def confirmed(self):
		return self._confirmed

	def containingDevices(self):
		return []

	def deviceType(self):
		return Device.TYPE_UNKNOWN

	def flattenContainingDevices(self):
		devices = []
		ids = []
		toCheck = list(self.containingDevices())
		while len(toCheck):
			d = toCheck.pop()
			if isinstance(d, int):
				d = self._manager.device(d)
			if d is None:
				continue
			if d is self:
				# Ignore ourself
				continue
			if d.id() in ids:
				continue
			devices.append(d)
			ids.append(d.id())
			toCheck.extend(d.containingDevices())
		return devices

	# pylint: disable=W0212
	def loadCached(self, olddevice):
		self._id = olddevice._id
		self._name = olddevice._name
		self._loadCount = 0
		self.setParams(olddevice.params())
		(state, stateValue) = olddevice.state()
		self._state = state
		self._stateValue = stateValue
		self._ignored = olddevice._ignored
		self._sensorValues = olddevice._sensorValues

	def loadCount(self):
		return self._loadCount

	def load(self, settings):
		if 'id' in settings:
			self._id = settings['id']
		if 'name' in settings:
			self._name = settings['name']
		if 'params' in settings:
			self.setParams(settings['params'])
		#if 'state' in settings and 'stateValue' in settings:
		#	self.setState(settings['state'], settings['stateValue'])

	def localId(self):
		"""
		This method must be reimplemented in the subclass. Return a unique id for
		this device type.
		"""
		return 0

	def ignored(self):
		return self._ignored

	def isDevice(self):
		"""
		Return True if this is a device.
		"""
		return True

	def isSensor(self):
		"""
		Return True if this is a sensor.
		"""
		return False

	def manager(self):
		return self._manager

	def metadata(self, key=None, default=None):
		"""
		Returns a metadata value set by the user. If key is none then all values are returned as
		a dictionary.
		"""
		if key is None:
			return {}
		return default

	def methods(self):
		"""
		Return the methods this supports. This is an or-ed in of device method flags.

		Example:
		return Device.TURNON | Device.TURNOFF
		"""
		return 0

	def model(self):
		return 'n/a'

	def name(self):
		return self._name if self._name is not None else 'Device %i' % self._id

	def parameters(self):
		"""
		Returns a static dictionary of paramters describing the device.
		These should not containd the current state of the device, only descriptive parameters.
		"""
		return {}

	def params(self):
		return {}

	def paramUpdated(self, param):
		if self._manager:
			self._manager.deviceParamUpdated(self, param)

	def protocol(self):
		return self.typeString()

	def sensorValue(self, valueType, scale):
		"""
		Returns a sensor value of a the specified valueType and scale. Returns None
		is no such value exists
		"""
		if valueType not in self._sensorValues:
			return None
		for sensorType in self._sensorValues[valueType]:
			if sensorType['scale'] == scale:
				return float(sensorType['value'])
		return None

	def sensorValues(self):
		"""
		Returns a list of all sensor values this device has received.
		"""
		return self._sensorValues

	def setId(self, newId):
		self._id = newId

	def setIgnored(self, ignored):
		self._ignored = ignored
		if self._manager:
			self._manager.save()

	def setManager(self, manager):
		self._manager = manager

	def setName(self, name):
		self._name = name
		self.paramUpdated('name')

	def setParams(self, params):
		pass

	def setSensorValue(self, valueType, value, scale):
		if valueType not in self._sensorValues:
			self._sensorValues[valueType] = []
		found = False
		for sensorType in self._sensorValues[valueType]:
			if sensorType['scale'] == scale:
				if sensorType['value'] != str(value) or valueType not in self.valueChangedTime:
					# value has changed
					self.valueChangedTime[valueType] = int(time.time())
				else:
					if sensorType['lastUpdated'] > int(time.time() - 1):
						# Same value and less than a second ago, most probably
						# just the same value being resent, ignore
						return
				sensorType['value'] = str(value)
				sensorType['lastUpdated'] = int(time.time())
				found = True
				break
		if not found:
			self._sensorValues[valueType].append({
				'value': str(value),
				'scale': scale,
				'lastUpdated': int(time.time())
			})
			self.valueChangedTime[valueType] = int(time.time())
		if self._manager:
			self._manager.sensorValueUpdated(self, valueType, value, scale)
			self._manager.save()

	def setState(self, state, stateValue=None, ack=None, origin=None):
		if stateValue is None:
			stateValue = ''
		if self._state == state \
		   and self._stateValue == stateValue \
		   and self.lastUpdated \
		   and self.lastUpdated > int(time.time() - 1):
			# Same state/statevalue and less than one second ago, most probably
			# just the same value being resent, ignore
			return
		self.lastUpdated = time.time()
		self._state = state
		self._stateValue = stateValue
		if self._manager:
			self._manager.stateUpdated(self, ackId=ack, origin=origin)

	def setStateFailed(self, state, stateValue='', reason=0, origin=None):
		if self._manager:
			self._manager.stateUpdatedFail(self, state, stateValue, reason, origin)

	def state(self):
		"""
		Returns a tuple of the device state and state value

		Example:
		state, stateValue = device.state()
		"""
		return (self._state, self._stateValue)

	def typeString(self):
		"""
		Must be reimplemented by subclass. Return the type (transport) of this
		device. All devices from a plugin must have the same type.
		"""
		return ''

	# pylint: disable=R0911
	@staticmethod
	def methodStrToInt(method):
		"""Convenience method to convert method string to constants.

		Example:
		"turnon" => Device.TURNON
		"""
		if method == 'turnon':
			return Device.TURNON
		if method == 'turnoff':
			return Device.TURNOFF
		if method == 'dim':
			return Device.DIM
		if method == 'bell':
			return Device.BELL
		if method == 'learn':
			return Device.LEARN
		if method == 'up':
			return Device.UP
		if method == 'down':
			return Device.DOWN
		if method == 'stop':
			return Device.STOP
		if method == 'rgb' or method == 'rgbw':
			return Device.RGB
		if method == 'thermostat':
			return Device.THERMOSTAT
		logging.warning('Did not understand device method %s', method)
		return 0

	@staticmethod
	def maskUnsupportedMethods(methods, supportedMethods):
		# Up -> Off
		if (methods & Device.UP) and not (supportedMethods & Device.UP):
			methods = methods | Device.TURNOFF

		# Down -> On
		if (methods & Device.DOWN) and not (supportedMethods & Device.DOWN):
			methods = methods | Device.TURNON

		# Cut of the rest of the unsupported methods we don't have a fallback for
		return methods & supportedMethods

	@staticmethod
	def sensorTypeIntToStr(sensorType):
		types = {
			Device.TEMPERATURE: 'temp',
			Device.HUMIDITY: 'humidity',
			Device.RAINRATE: 'rrate',
			Device.RAINTOTAL: 'rtot',
			Device.WINDDIRECTION: 'wdir',
			Device.WINDAVERAGE: 'wavg',
			Device.WINDGUST: 'wgust',
			Device.UV: 'uv',
			Device.WATT: 'watt',
			Device.LUMINANCE: 'lum',
			Device.DEW_POINT: 'dewp',
			Device.BAROMETRIC_PRESSURE: 'barpress',
			#Device.GENRIC_METER: 'genmeter'
		}
		return types.get(sensorType, 'unknown')

class Sensor(Device):
	"""A convenience class for sensors."""
	def isDevice(self):
		return False

	def isSensor(self):
		return True

	def name(self):
		return self._name if self._name is not None else 'Sensor %i' % self._id

class CachedDevice(Device):  # pylint: disable=R0902
	def __init__(self, settings):
		super(CachedDevice, self).__init__()
		self.paramsStorage = {}
		self.load(settings)
		self._confirmed = False
		self._localId = 0
		self.mimikType = ''
		self.storedmethods = 0
		self.batteryLevel = Device.BATTERY_UNKNOWN
		self._isSensor = False
		if 'localId' in settings:
			self._localId = settings['localId']
		if 'loadCount' in settings:
			self._loadCount = settings['loadCount']+1
		if 'type' in settings:
			self.mimikType = settings['type']
		if 'methods' in settings:
			self.storedmethods = settings['methods']
		if 'state' in settings:
			self._state = settings['state']
		if 'stateValue' in settings:
			self._stateValue = settings['stateValue']
		if 'battery' in settings:
			self.batteryLevel = settings['battery']
		if 'ignored' in settings:
			self._ignored = settings['ignored']
		if 'sensorValues' in settings:
			self.setSensorValues(settings['sensorValues'])
		if 'isSensor' in settings:
			self._isSensor = settings['isSensor']
		if 'declaredDead' in settings:
			self.declaredDead = settings['declaredDead']

	def isSensor(self):
		return self._isSensor

	def localId(self):
		return self._localId

	def methods(self):
		return self.storedmethods

	def params(self):
		return self.paramsStorage

	def setParams(self, params):
		self.paramsStorage = params

	def setSensorValues(self, sensorValues):
		# this method just fills cached values, no signals or reports are sent
		for valueTypeFetch in sensorValues:
			valueType = int(valueTypeFetch)
			if valueType not in self._sensorValues:
				self._sensorValues[valueType] = []
			sensorType = sensorValues[valueTypeFetch]
			for sensorValue in sensorType:
				value = sensorValue['value']
				scale = sensorValue['scale']
				if 'lastUpdated' in sensorValue:
					lastUpdated = sensorValue['lastUpdated']
				else:
					# not in cache, perhaps first time lastUpdated is used
					# (maybe this should be logged?)
					lastUpdated = int(time.time())
				self._sensorValues[valueType].append({
					'value': value,
					'scale': scale,
					'lastUpdated': lastUpdated
				})

	def typeString(self):
		return self.mimikType
