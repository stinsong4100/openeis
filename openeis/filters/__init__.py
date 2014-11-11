# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2014, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# or favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
#
#}}}



import abc

import pkgutil, importlib

from openeis.core.descriptors import (ConfigDescriptorBaseClass,
                                      SelfDescriptorBaseClass)

class BaseFilter(SelfDescriptorBaseClass,
                 ConfigDescriptorBaseClass,
                 metaclass=abc.ABCMeta):
    def __init__(self, parent=None):
        self.parent = parent
        
    @abc.abstractmethod
    def __iter__(self):
        pass
    
class SimpleRuleFilter(BaseFilter, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def rule(self, time, value):
        """Must return time, value pair."""
    
    def __iter__(self):
        def generator():
            for dt, value in self.parent:
                yield self.rule(dt, value)
        return generator()
    
column_modifiers = {}

def register_column_modifier(klass):
    column_modifiers[klass.__name__] = klass
    return klass
 
_extList = [name for _, name, _ in pkgutil.iter_modules(__path__)]

extDict = {}
 
for extName in _extList:
    print('Importing module: ', extName)
    #extDict[extName] = importlib.import_module(extName, 'openeis.filters')
    extDict[extName] = __import__(extName,globals(),locals(),[], 1)    


def apply_filters(generators, configs):
    errors = []
    
    print("column mods: ", column_modifiers)
    
    for topic, filter_name, filter_config in configs:
        if not isinstance(topic, str):
            topic = topic[0]
        parent_filter_dict = generators.get(topic)
        if parent_filter_dict is None:
            errors.append('Invalid Topic for DataMap: ' + str(topic))
            continue
        
        parent_filter = parent_filter_dict['gen']
        parent_type = parent_filter_dict['type']
        
        filter_class = column_modifiers.get(filter_name)
        if filter_class is None:
            errors.append('Invalid filter name: ' + str(filter_name))
            continue
        
        try:
            new_filter = filter_class(parent=parent_filter, **filter_config)
        except Exception as e:
            errors.append('Error configuring filter: '+str(e))
            continue
            
        value = parent_filter_dict.copy()
        
        value['gen']=new_filter
        value['type']=parent_type
        
        generators[topic] = value
    
    return generators, errors


        

    
# class BaseMissingValueRule:
#     def __init__(self, aggrigator):
#         self.aggrigator = aggrigator
#         
# class BaseExtraValueRule:
#     def __init__(self, aggrigator):
#         self.aggrigator = aggrigator  

# def apply_simple_generator(topic, generators, mod_rule_class, *args):
#     mod_rule = mod_rule_class(*args)
#     generators[topic]['gen'] = simple_generator(generators[topic]['gen'], mod_rule)
#     return generators
# 
# def simple_generator(parent_generator, mod_rule):
#     for time, value in parent_generator:
#         yield mod_rule(time, value)
#  
# class BaseModifierRule(metaclass=abc.ABCMeta):
#     @abc.abstractmethod
#     def __call__(self):  
#         pass
#  
# 
# missing_value_rules = {}
# 
# def register_missing_value_rule(klass):
#     missing_value_rules[klass.__name__] = klass
#     return klass
# 
# extra_value_rules = {}
# 
# def register_extra_value_rule(klass):
#     extra_value_rules[klass.__name__] = klass
#     return klass
# 
# aggrigators = {}
# def register_aggrigator(klass):
#     aggrigators[klass.__name__] = klass
#     return klass
    