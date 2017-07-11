#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lib.task import Task

__author__ = 'Matteo'

import json

class Config(object):

    def __init__(self, config_file, tasks_file):

        infos = json.loads(open(config_file).read())
        tasks = json.loads(open(tasks_file).read())

        print "There is a mistake in printing"

        self.tasker_config = infos['tasker_config']
        self.google_calendar_config = infos['google_calendar_config']
        self.default_time_start_working_day = infos['default_time_start_working_day']
        self.default_time_start_lunch = infos['default_time_start_lunch']
        self.default_time_end_lunch = infos['default_time_end_lunch']
        self.default_time_end_working_day = infos['default_time_end_working_day']
        self.default_time_start_dinner = infos['default_time_start_dinner']
        self.default_time_end_dinner = infos['default_time_end_dinner']
        self.default_time_end_day = infos['default_time_end_day']
        self.default_early = infos['default_early']
        self.default_central = infos['default_central']
        self.default_late = infos['default_late']
        self.task_type_code = infos['task_type_code']
        self.daymoment_activity_probability = infos['daymoment_activity_probability']
        self.default_activity_mode = infos['default_activity_mode']
        self.task_type_default = infos['task_type_default']
        self.task_reminders = infos['task_reminders']

        self.task_list = tasks['task_list']

        if self.default_activity_mode < 2:
            self.task_type_default = Config.generate_dtv_from_configfile(self, self.task_type_default)
        elif self.default_activity_mode == 2:
            self.task_type_default = Task.generate_dtv_from_tasklist(self, self.task_list)

        self.task_list = Task.generate_otl_from_taskfile(self, self.task_list)

    def generate_dtv_from_configfile(config, tasks, code = False):

        # default dictionary
        task_type_default = {}

        # for each type in configuration file
        for type_code, type_values in tasks.iteritems():

            task_type = str(type_values['task_type'])

            slot_duration = None
            importance    = None
            best_moment   = None
            other_names       = None
            max_qty       = None

            if "slot_duration" in type_values.keys(): slot_duration = type_values['slot_duration']
            if "importance" in type_values.keys():    importance = type_values['importance']
            if "best_moment" in type_values.keys():   best_moment = type_values['best_moment']
            if "other_names" in type_values.keys():       other_names = type_values['other_names']
            if "max_qty" in type_values.keys():       max_qty = type_values['max_qty']

            obj_task = Task(str(task_type), str(task_type), config,
                          slot_duration = slot_duration,
                          importance    = importance,
                          other_names       = other_names,
                          max_qty       = max_qty,
                          best_moment   = best_moment)

            task_type_default[str(task_type)] = obj_task

        # return default tasks
        return task_type_default