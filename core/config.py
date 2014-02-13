#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core.constants import CL_ROOT

import os
import sys
import ConfigParser

class Dictionary(dict):
    def __getattr__(self, key):
        return self.get(key, None)

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
	
class Config:
	def __init__(self, cfg=os.path.join(CL_ROOT, 'conf', 'cl.conf')):
		config = ConfigParser.ConfigParser()
		config.read(cfg)
		
		for section in config.sections():
			setattr(self, section, Dictionary())
			for name, raw_value in config.items(section):
				try:
					value = config.getboolean(section, name)
				except ValueError:
					try:
						value = config.getint(section, name)
					except ValueError:
						value = config.get(section, name)
						
				setattr(getattr(self, section), name, value)
				
	def get(self, section):
		try:
			return getattr(self, section)
		except AttributeError as e:
			raise e
			