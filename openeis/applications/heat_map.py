"""
Heat map: show electricity use by time-of-day, across many days.

Shows extent of daily, weekly, and seasonal load profiles.


Copyright
=========

OpenEIS Algorithms Phase 2 Copyright (c) 2014,
The Regents of the University of California, through Lawrence Berkeley National
Laboratory (subject to receipt of any required approvals from the U.S.
Department of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov
referring to "OpenEIS Algorithms Phase 2 (LBNL Ref 2014-168)".

NOTICE:  This software was produced by The Regents of the University of
California under Contract No. DE-AC02-05CH11231 with the Department of Energy.
For 5 years from November 1, 2012, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, and perform
publicly and display publicly, by or on behalf of the Government. There is
provision for the possible extension of the term of this license. Subsequent to
that period or any extension granted, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, distribute copies
to the public, perform publicly and display publicly, and to permit others to
do so. The specific term of the license can be identified by inquiry made to
Lawrence Berkeley National Laboratory or DOE. Neither the United States nor the
United States Department of Energy, nor any of their employees, makes any
warranty, express or implied, or assumes any legal liability or responsibility
for the accuracy, completeness, or usefulness of any data, apparatus, product,
or process disclosed, or represents that its use would not infringe privately
owned rights.


License
=======

Copyright (c) 2014, The Regents of the University of California, Department
of Energy contract-operators of the Lawrence Berkeley National Laboratory.
All rights reserved.

1. Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   (a) Redistributions of source code must retain the copyright notice, this
   list of conditions and the following disclaimer.

   (b) Redistributions in binary form must reproduce the copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

   (c) Neither the name of the University of California, Lawrence Berkeley
   National Laboratory, U.S. Dept. of Energy nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

2. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
   ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
   ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
   THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

3. You are under no obligation whatsoever to provide any bug fixes, patches,
   or upgrades to the features, functionality or performance of the source code
   ("Enhancements") to anyone; however, if you choose to make your Enhancements
   available either publicly, or directly to Lawrence Berkeley National
   Laboratory, without imposing a separate written license agreement for such
   Enhancements, then you hereby grant the following license: a non-exclusive,
   royalty-free perpetual license to install, use, modify, prepare derivative
   works, incorporate into other computer software, distribute, and sublicense
   such enhancements or derivative works thereof, in binary and source code
   form.

NOTE: This license corresponds to the "revised BSD" or "3-clause BSD" license
and includes the following modification: Paragraph 3. has been added.
"""

from openeis.applications import reports
from openeis.applications import DriverApplicationBaseClass, InputDescriptor,  \
    OutputDescriptor, ConfigDescriptor, Descriptor
from openeis.applications import reports
from .utils import conversion_utils as cu
from django.db.models import Avg
import logging
import pytz

class Application(DriverApplicationBaseClass):

    def __init__(self, *args, building_name=None, **kwargs):
        #Called after app has been staged
        """
        When applications extend this base class, they need to make
        use of any kwargs that were setup in config_param
        """
        super().__init__(*args,**kwargs)

        self.default_building_name_used = False

        if building_name is None:
            building_name = "None supplied"
            self.default_building_name_used = True

        self.building_name = building_name

    @classmethod
    def get_self_descriptor(cls):    
        name = 'Heat Map'
        desc = 'Heat maps are a means of visualizing and presenting the\
                information that is contained in a time series load profile.\
                The maps color-code the size of the load so that hot spots\
                and patterns are easily identified.'
        return Descriptor(name=name, description=desc)
        
    @classmethod
    def get_config_parameters(cls):
        # Called by UI
        return {
            "building_name": ConfigDescriptor(str, "Building Name", optional=True)
            }
    
    @classmethod
    def required_input(cls):
        #Called by UI
        return {
            'load':InputDescriptor('WholeBuildingPower','Building Load'),
            }


    @classmethod
    def output_format(cls, input_object):
        # Called when app is staged
        """
        Output will have the date, hour, and respective load.
        To be graphed in a heat map later.
        """
        topics = input_object.get_topics()
        load_topic = topics['load'][0]
        load_topic_parts = load_topic.split('/')
        output_topic_base = load_topic_parts[:-1]
        date_topic = '/'.join(output_topic_base+['heatmap', 'date'])
        hour_topic = '/'.join(output_topic_base+['heatmap', 'time'])
        load_topic = '/'.join(output_topic_base+['heatmap', 'load'])
        output_needs = {
            'Heat_Map': {
                'date': OutputDescriptor('string', date_topic),
                'hour': OutputDescriptor('integer', hour_topic),
                'load': OutputDescriptor('float', load_topic)
                }
            }
        return output_needs


    def reports(self):
        #Called by UI to create Viz
        """Describe how to present output to user
        Display this viz with these columns from this table

        display_elements is a list of display objects specifying viz and columns
        for that viz
        """

        report = reports.Report('Heat Map for Building Energy Load')

        text_blurb = reports.TextBlurb(text="Analysis of the extent of a building's daily, weekly, and seasonal shut off.")
        report.add_element(text_blurb)

        heat_map = reports.HeatMap(table_name='Heat_Map',
                                   x_column='hour',
                                   y_column='date',
                                   z_column='load',
                                   x_label='Hour of the Day',
                                   y_label='Date',
                                   z_label='Building Energy [kWh]')
        report.add_element(heat_map)

        text_guide1 = reports.TextBlurb(text="Horizontal banding indicates shut off during\
                                              periodic days (e.g. weekends).")
        report.add_element(text_guide1)

        text_guide2 = reports.TextBlurb(text="Unusual or unexplainable \"hot spots\"\
                                              may indicate poor equipment control.")
        report.add_element(text_guide2)

        text_guide3 = reports.TextBlurb(text="Vertical banding indicates consistent\
                                              daily scheduling of usage.")
        report.add_element(text_guide3)

        report_list = [report]

        return report_list

    def execute(self):
        """
        Output values for Heat Map.
        """
        self.out.log("Starting application: heat map.", logging.INFO)

        self.out.log("Querying database.", logging.INFO)
        loads = self.inp.get_query_sets('load', group_by='hour',
                                        group_by_aggregation=Avg,
                                        exclude={'value':None})
        
        self.out.log("Getting unit conversions.", logging.INFO)
        base_topic = self.inp.get_topics()
        meta_topics = self.inp.get_topics_meta()

        load_unit = meta_topics['load'][base_topic['load'][0]]['unit']
        self.out.log(
            "Convert loads from [{}] to [kW].".format(load_unit),
            logging.INFO
            )
        load_convertfactor = cu.getFactor_powertoKW(load_unit)

        self.out.log("Compiling the report table.", logging.INFO)
        for x in loads[0]:
            datevalue = self.inp.localize_sensor_time(base_topic['load'][0], x[0])
            self.out.insert_row("Heat_Map", {
                'date': datevalue.date(),
                'hour': datevalue.hour,
                'load': x[1]*load_convertfactor
                }
            )
