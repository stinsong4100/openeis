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

'''This command iterates through all tables in the database. All tables
which name starts with appoutputdata_ and are empty are dropped.
'''

from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.db import connection, transaction


class Command(NoArgsCommand):
    help = 'Remove orphaned dynamic application output tables.'
    option_list = NoArgsCommand.option_list + (
        make_option('-n', '--dry-run', action='store_true', default=False,
                    help='Do everything except modify the database.'),
        make_option('-a', '--all-tables', action='store_true', default=False,
                    help='Also drop non-empty dynamic tables.'),
    )

    def handle_noargs(self, *, verbosity=1, dry_run=False, all_tables=False,
                      **options):
        verbosity = int(verbosity)
        with transaction.atomic():
            cursor = connection.cursor()
            for table in cursor.db.introspection.get_table_list(cursor):
                if not table.startswith('appoutputdata_'):
                    continue
                if not all_tables:
                    if verbosity >= 1:
                        self.stdout.write('Clearing unused records from dynamic table ' + table)
                    if not dry_run:
                        cursor.execute('DELETE FROM {} WHERE source_id NOT IN '
                                       '(SELECT id FROM projects_appoutput)'.format(table))
                        cursor.execute('SELECT COUNT(*) FROM ' + table)
                    else:
                        cursor.execute('SELECT COUNT(*) FROM {} WHERE source_id IN '
                                       '(SELECT id FROM projects_appoutput)'.format(table))
                    count, = cursor.cursor.fetchone()
                    if count:
                        continue
                if verbosity >= 1:
                    self.stdout.write('Dropping dynamic table ' + table)
                if not dry_run:
                    cursor.execute('DROP TABLE ' + table)
