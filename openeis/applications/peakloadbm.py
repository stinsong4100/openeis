from openeis.applications import DriverApplicationBaseClass, InputDescriptor, OutputDescriptor, ConfigDescriptor
import logging
import datetime
import numpy
import math
from datetime import timedelta
import django.db.models as django
from django.db.models import Max, Min,Avg,Sum,StdDev
from django.db import models
from dateutil.relativedelta import relativedelta
from .utils.spearman import findSpearmanRank

import dateutil
from django.db.models.aggregates import StdDev

class Application(DriverApplicationBaseClass):
    
    def __init__(self,*args,building_sq_ft=-1, building_name=None,**kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)
        
        self.default_building_name_used = False
        
        if building_sq_ft < 0:
            raise Exception("Invalid input for building_sq_ft")
        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True
        
        self.sq_ft = building_sq_ft
        self.building_name = building_name
        
   
    
    @classmethod
    def get_config_parameters(cls):
        #Called by UI
        return {
                    "building_sq_ft": ConfigDescriptor(float, "Square footage", minimum=200),
                    "building_name": ConfigDescriptor(str, "Building Name", optional=True)
                }
        
    
    @classmethod
    def required_input(cls):
        #Called by UI
        # Sort out units.
        return {
                    'load':InputDescriptor('WholeBuildingElectricity','Building Load')
                }
        
    @classmethod
    def output_format(cls, input_object):
        #Called when app is staged
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1] 
        value_topic = '/'.join(output_topic_base+['peakloadbm','peakloadbm'])
        
        output_needs =  {'Peak Load Benchmark': 
                            {'value':OutputDescriptor('String', value_topic)},
                        }
        return output_needs
        
    def report(self):
        #Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table
        
        
        display elements is a list of display objects specifying viz and columns for that viz 
        """
        display_elements = []
        
        return display_elements
        
    def execute(self):
        #Called after User hits GO
        "Do stuff"
        self.out.log("Starting Spearman rank", logging.INFO)
        
        
        load_query = self.inp.get_query_sets('load', group_by='hour',group_by_aggregation=Avg,
                                             exclude={'value':None})
        
        load_values = []
         
        for x in load_query['load'][0]: 
            load_values.append(x[1])
        
        # for some reason, it has to be in watts    
        peakLoad = max(load_values) * 1000
        peakLoadIntensity = peakLoad / self.sq_ft
         
        self.out.insert_row("Peak Load Benchmark", {'value': str(peakLoadIntensity)})
        