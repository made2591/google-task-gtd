#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Matteo'

import random
import sys
import datetime

class Task(object):
    """
    This class represents an Activity: it has a name, a type, an importance, a list of daytimes in which it is more appropriate, 
    a description that contains a count for several daytime slots in which the activity will be replicated during the day. 
    It may also contain constraints.
    """
    def __init__(self, n, t, config, **options):
        """
        Builder of Activity
        :param name: activity name
        :param task_type: activity type
        :param description: activity description
        :param slot_duration: activity minute duration
        :param importance: activity importance
        :param best_moment: activity importance in several day time
        :param other_names: minimum amount of minutes for the activity
        :param max_qty: maximum amount of minutes for the activity
        :return:
        """
        # required parameter
        self.name = n
        self.task_type = t

        # optional parameter
        self.description = None
        if options.get('description') != None: self.description = options.get('description')

        # pseudo-optional parameter
        self.slot_duration = config.tasker_config['default_slot_duration']
        self.importance = 0
        self.best_moment = {}
        self.other_names = []
        self.max_qty = 0

        # parameter with a default value
        if options.get('slot_duration') != None: self.slot_duration = options.get('slot_duration')
        if options.get('importance') != None:    self.importance    = options.get('importance')
        if options.get('best_moment') != None:   self.best_moment   = options.get('best_moment')
        if options.get('other_names') != None:   self.other_names   = options.get('other_names')
        if options.get('max_qty') != None:       self.max_qty       = options.get('max_qty')

        # best moment init zero-init
        if self.best_moment == None:
            for moment in config.tasker_config['day_timezone']:
                self.best_moment[moment] = 0

        # missing best moment zero-init
        for moment in config.tasker_config['day_timezone']:
            if moment not in self.best_moment and config.default_activity_mode == 0:
                self.best_moment[moment] = 0

        # compiled during task generation
        self.probability = 0.0

    @staticmethod
    def induce_probabilities(config):
        """
        Calculates the total probability with Laplace correction (m-estimate, m = 1)
        """

        tasks = config.task_list.values()

        total_importance = 0.0
        for task in tasks:
            config.tasker_config['all_act_name'].append(task.name)
            total_importance += task.importance
            if task.importance == 0: total_importance += 1

        for task in tasks:
            task.prob = task.importance / total_importance if task.importance > 0 else 1 / total_importance
            total_probabilities = 0.0
            for moment, probability in task.best_moment.iteritems():
                total_probabilities += probability
                if probability == 0: total_probabilities += 1
            for moment in task.best_moment:
                task.best_moment[moment] = task.prob * task.best_moment[moment] / total_probabilities \
                                if task.best_moment[moment] > 0 else task.prob * 1 / total_probabilities

        daymoment_activity_probability = {}
        for moment in config.tasker_config['day_timezone']:
            daymoment_activity_probability[moment] = {}
            total_probabilities = 0.0
            for task in tasks:
                total_probabilities += task.best_moment[moment]
                if task.best_moment[moment] == 0: total_probabilities += 1
            for task in tasks:
                daymoment_activity_probability[moment][task.name] = task.best_moment[moment] / total_probabilities \
                                if task.best_moment[moment] > 0 else 1 / total_probabilities

        config.daymoment_activity_probability = daymoment_activity_probability
        config.tasker_config['minimum_activity_slot'] = min(task.slot_duration for task in tasks)

    @staticmethod
    def generate_otl_from_taskfile(config, tasks):
        # task (object) list
        tasks_list = {}

        # for each task in file
        for name, task in tasks.iteritems():

            # fix the task type
            task_type = str(task['task_type'])

            # default set up
            slot_duration = None
            importance    = None
            best_moment   = None
            description   = None
            other_names   = None
            max_qty       = None

            # if description is specified in configuration
            if "description" in task.keys():   description   = task['description']

            # set of specified fields
            if "slot_duration" in task.keys(): slot_duration = task['slot_duration']
            if "importance" in task.keys():    importance    = task['importance']
            if "best_moment" in task.keys():   best_moment   = task['best_moment']
            if "other_names" in task.keys():   other_names   = task['other_names']
            if "max_qty" in task.keys():       max_qty       = task['max_qty']

            # Uses the default that is in the default of the types in the config file
            # (Already updated during construction)
            if config.default_activity_mode != 0:
                if "slot_duration" not in task.keys() and 'task_type' in config.task_type_default.keys():
                    slot_duration = config.task_type_default[task_type].slot_duration
                if "importance" not in task.keys() and 'task_type' in config.task_type_default.keys():
                    importance = config.task_type_default[task_type].importance
                if "best_moment" not in task.keys() and 'task_type' in config.task_type_default.keys():
                    best_moment = config.task_type_default[task_type].best_moment
                if "other_names" not in task.keys() and 'task_type' in config.task_type_default.keys():
                    other_names = config.task_type_default[task_type].other_names
                if "max_qty" not in task.keys() and 'task_type' in config.task_type_default.keys():
                    max_qty = config.task_type_default[task_type].max_qty

            # for each day time
            for moment in config.tasker_config['day_timezone_ordered']:
                # if wasn't set in day time list, set to default
                if config != None and task_type != None and task_type in config.task_type_code.keys() and \
                   moment not in best_moment and config.default_activity_mode != 0:
                    best_moment[moment] = config.task_type_default[task_type].best_moment[moment]
                # if there's not a default ready to use, set to zero
                if moment not in best_moment and config.default_activity_mode == 0:
                    best_moment[moment] = 0

            # append object to task list
            tasks_list[name] = (Task(name, task_type, config, slot_duration = slot_duration,
                                                       importance    = importance,
                                                       best_moment   = best_moment,
                                                       description   = description,
                                                       other_names   = other_names,
                                                       max_qty       = max_qty
                                                       ))
        # return task list
        return tasks_list

    @staticmethod
    def task_to_dict(tasks):
        dict_info = {}
        for ttp, task in tasks.iteritems():
            dict_info[task.task_type] = {}
            dict_info[task.task_type]['task_type']     = task.task_type
            dict_info[task.task_type]['probability']   = task.probability
            dict_info[task.task_type]['slot_duration'] = task.slot_duration
            dict_info[task.task_type]['importance']    = task.importance
            dict_info[task.task_type]['best_moment']   = task.best_moment
            dict_info[task.task_type]['other_names']   = task.other_names
            dict_info[task.task_type]['max_qty']       = task.max_qty
        return dict_info

    @staticmethod
    def generate_dtv_from_tasklist(config, tasks):

        # generate task types from the task list
        type_codes = sorted(list(set(task['task_type'] for name, task in tasks.iteritems())))

        # default dictionary
        task_type_default = {}

        # for each type of code
        for type_code in type_codes:

            # create task fields
            best_moments_means = {}
            counter_activity_of_type_code = 0.0
            slot_duration_accumulator = 0.0
            importance_accumulator = 0.0
            other_names = None # []
            max_qty_accumulator = 0.0

            # for each day time, I set up day time to 0
            for m in config.tasker_config['day_timezone_ordered']:
                best_moments_means[m] = 0.0

            # for each task in list
            for name, task in tasks.iteritems():
                # if the task type is in currently analyzed type
                if str(task['task_type']) == str(type_code):
                    # increase the number of activities of that type
                    counter_activity_of_type_code += 1
                    # for each day time
                    for m in config.tasker_config['day_timezone_ordered']:
                        # if the best day time of that task is present
                        if 'best_moment' in task.keys() and m in task['best_moment'].keys():
                            # increase the mean of the day time for task of that type
                            best_moments_means[m] += task['best_moment'][m]
                    # increase the counter for each field present
                    if 'slot_duration' in task.keys(): slot_duration_accumulator += task['slot_duration']
                    if 'importance' in task.keys():    importance_accumulator += task['importance']
                    if 'max_qty' in task.keys():       max_qty_accumulator += task['max_qty']

            # calculate the mean of the day time
            for m in config.tasker_config['day_timezone_ordered']:
                best_moments_means[m] = round(best_moments_means[m]/counter_activity_of_type_code)

            # create Task object
            obj_task = Task(str(type_code), str(type_code), config,
                          slot_duration = round(slot_duration_accumulator/counter_activity_of_type_code),
                          importance    = round(importance_accumulator/counter_activity_of_type_code),
                          other_names   = other_names,
                          max_qty       = round(max_qty_accumulator/counter_activity_of_type_code),
                          best_moment   = best_moments_means)

            task_type_default[str(type_code)] = obj_task

        return task_type_default

    @staticmethod
    def tasks_to_json(config, rootname, tasks):
        jsonstr = "{ \""+rootname+"\":\n\t{\n"
        c = 0
        for task in tasks:
            if task.task_type == "1":
                jsonstr += '\t\t"'+task.name+'" : {\n'
                jsonstr += '\t\t\t\t"task_type" : '+str(task.task_type)

                if task.probability != None:   jsonstr += ',\n\t\t\t\t"probability" :'+str(task.probability)
                if task.slot_duration != None: jsonstr += ',\n\t\t\t\t"slot_duration" :'+str(task.slot_duration)
                if task.importance != None:    jsonstr += ',\n\t\t\t\t"importance" :'+str(task.importance)
                if task.best_moment != None:   jsonstr += ',\n\t\t\t\t"best_moment" : { '+str((''.join('"%s" : %d, ' % (m, task.best_moment[m]) for m in config.tasker_config['day_timezone_ordered'])+'},').replace(', },', ' }'))
                if task.other_names != None:   jsonstr += ',\n\t\t\t\t"other_names" :'+str(task.other_names)
                if task.max_qty != None:       jsonstr += ',\n\t\t\t\t"max_qty" :'+str(task.max_qty)

                jsonstr += '\n\t\t\t}'
                c += 1
                if c < len(tasks):
                    jsonstr += '\n'
                    #jsonstr += ',\n'
                else:
                    jsonstr += '\n'
        jsonstr += "\t}\n}"
        return jsonstr

    @staticmethod
    def print_daymoment_task_probability(config, tasks):
        print
        head = "|"+''.join('%19s|' % 'Activity Name')+' '
        head += str(' '.join(('%17s|' % m) for m in config.tasker_config['day_timezone_ordered']))
        print ''.join('-' for i in range(1, len(head)))+"|"
        print head
        print ''.join('-' for i in range(1, len(head)))+"|"
        for task in tasks:
            print "|"+('%19s|' % task.name), ' '.join('          %.5f|' %
                   (config.daymoment_activity_probability[m][task.name])
                       for m in config.tasker_config['day_timezone_ordered'])
        print ''.join('-' for i in range(1, len(head)))+"|"
        foot = "|"+''.join('%19s|' % 'Total Probability')
        foot += str(''.join(('%18s|' %
                str(sum(config.daymoment_activity_probability[m][task.name] for task in tasks))
                       for m in config.tasker_config['day_timezone_ordered'])))
        print foot
        print ''.join('-' for i in range(1, len(head)))+"|"

    @staticmethod
    def print_one_day_tasks(config, tasks, temporal_slots):
        for task in tasks:
            print ('| %s - %s     | %40s |' % (task[1].strftime("%H:%M"),
                                               task[2].strftime("%H:%M"),
                                               task[0]))
        print
        print '\n|'+''.join('-' for i in range(1, 63))+'|'
        truncated = None
        last_moment = None
        for moment in config.tasker_config['day_timezone_ordered']:
            if temporal_slots[moment]['from'] < temporal_slots[moment]['to']:
                print '| '+''.join('%s  | %40s' % ('Start day moment', moment.replace('_', ' ').capitalize()))+' |'
                go_on = True
                for task in tasks:
                    if truncated != None and go_on:
                        if temporal_slots[moment]['from'] < truncated[2]:
                            print ('| %s - %s     | %40s |' % (temporal_slots[moment]['from'].strftime("%H:%M"),
                                                               truncated[2].strftime("%H:%M"),
                                                               truncated[0]))
                        else:
                            print ('| %s - %s     | %40s |' % (temporal_slots[last_moment]['to'].strftime("%H:%M"),
                                                               truncated[2].strftime("%H:%M"),
                                                               truncated[0]))
                        truncated = None
                        last_moment = None
                    if go_on:
                        if task[1] >= temporal_slots[moment]['from']:
                            if task[2] <= temporal_slots[moment]['to']:
                                print ('| %s - %s     | %40s |' % (task[1].strftime("%H:%M"),
                                                                   task[2].strftime("%H:%M"),
                                                                   task[0]))
                            else:
                                if task[1] < temporal_slots[moment]['to']:
                                    print ('| %s - %s     | %40s |' % (task[1].strftime("%H:%M"),
                                                                       temporal_slots[moment]['to'].strftime("%H:%M"),
                                                                       task[0]))
                                    truncated = task
                                    last_moment = moment
                                go_on = False
                print '| '+''.join('%s    | %40s' % ('End day moment',
                      moment.replace('_', ' ').capitalize()))+ \
                      ' |\n', '|'+''.join('-' for i in range(1, 63))+'|'
                if moment == 'late_morning':
                    # raw_input(moment)
                    # print '|'+''.join('-' for i in range(1, 41))+'|'
                    print ('| %s - %s     | %40s |' % (temporal_slots[moment]['to'].strftime("%H:%M"),
                                                       temporal_slots['early_afternoon']['from'].strftime("%H:%M"),
                                                       'Lunch'))
                    print '|'+''.join('-' for i in range(1, 63))+'|'
                if moment == 'late_afternoon':
                    # raw_input(moment)
                    # print '|'+''.join('-' for i in range(1, 41))+'|'
                    print ('| %s - %s     | %40s |' % (temporal_slots[moment]['to'].strftime("%H:%M"),
                                                       temporal_slots['early_evening']['from'].strftime("%H:%M"),
                                                       'Dinner'))
                    print '|'+''.join('-' for i in range(1, 63))+'|'
        print

    @staticmethod
    def print_temporal_slots(config, temporal_slots):
        """
        Print temporal slots
        :param temporal_slots: temporal slots with limitations
        :return:
        """
        print
        for ts in config.tasker_config['day_timezone_ordered']:
            if temporal_slots[ts]['from'] < temporal_slots[ts]['to']:
                print("%15s from %s to %s - Minutes: %s" %
                    (ts, temporal_slots[ts]['from'].strftime("%H:%M"), temporal_slots[ts]['to'].strftime("%H:%M"), \
                        (datetime.timedelta(minutes = int(((temporal_slots[ts]['to']-temporal_slots[ts]['from']).total_seconds()//60))))
                    )
                )
            if ts == "late_morning":
                print("\n%15s from %s to %s\n" % ("lunch", temporal_slots["late_morning"]['to'].strftime("%H:%M"), temporal_slots[config.tasker_config['day_timezone']['early_afternoon']]['from'].strftime("%H:%M")))
            if ts == "late_afternoon":
                print("\n%15s from %s to %s\n" % ("dinner", temporal_slots["late_afternoon"]['to'].strftime("%H:%M"), temporal_slots[config.tasker_config['day_timezone']['early_evening']]['from'].strftime("%H:%M")))

    @staticmethod
    def print_temporal_slots_table(config, temporal_slots):
        """
        Print temporal slots
        :param temporal_slots: temporal slots with limitations
        :return:
        """
        print
        print "|"+''.join('-' for i in range(1, 41))+"|"
        print ('|%30s %10s' % ('Day - Activities', '|'))
        print "|"+''.join('-' for i in range(1, 41))+"|"
        for ts in config.tasker_config['day_timezone_ordered']:
            if temporal_slots[ts]['from'] < temporal_slots[ts]['to']:
                print("| From %s to %s - Minutes: %s |" %
                    (temporal_slots[ts]['from'].strftime("%H:%M"), temporal_slots[ts]['to'].strftime("%H:%M"), \
                        (datetime.timedelta(minutes = int(((temporal_slots[ts]['to']-temporal_slots[ts]['from']).total_seconds()//60))))
                    )
                )
            if ts == "late_morning":
                print "|"+''.join('-' for i in range(1, 41))+"|"
                print("| From %s to %s - Lunch %12s" % (temporal_slots["late_morning"]['to'].strftime("%H:%M"), temporal_slots[config.tasker_config['day_timezone']['early_afternoon']]['from'].strftime("%H:%M"), "|"))
                print "|"+''.join('-' for i in range(1, 41))+"|"
            if ts == "late_afternoon":
                print "|"+''.join('-' for i in range(1, 41))+"|"
                print("| From %s to %s - Dinner %11s" % (temporal_slots["late_afternoon"]['to'].strftime("%H:%M"), temporal_slots[config.tasker_config['day_timezone']['early_evening']]['from'].strftime("%H:%M"), "|"))
                print "|"+''.join('-' for i in range(1, 41))+"|"
        print "|"+''.join('-' for i in range(1, 41))+"|\n"

    @staticmethod
    def get_daymoment_limit(config,
                            moment,
                            time_start_working_day,
                            time_start_lunch,
                            time_end_lunch,
                            time_end_working_day,
                            time_start_dinner,
                            time_end_dinner,
                            time_end_day,
                            early = None,
                            central = None,
                            late = None
                            ):
        """
        Builds the time limit of a day based on the various time limits:
        :param moment: day time name [config.tasker_config['day_timezone']['early_morning'], config.tasker_config['day_timezone']['morning'], "late_morning", config.tasker_config['day_timezone']['early_afternoon'],
                        config.tasker_config['day_timezone']['afternoon'], "late_afternoon", config.tasker_config['day_timezone']['early_evening'], config.tasker_config['day_timezone']['evening'], config.tasker_config['day_timezone']['late_evening']]
        :param time_start_working_day: daylight start time
        :param time_start_lunch: lunch start time
        :param time_end_lunch: lunch end time
        :param time_end_working_day: work time end time
        :param time_start_dinner: dinner start time
        :param time_end_dinner: dinner end time
        :param time_end_day: daylight end time
        :param early: portion compared to central and late in which the part of the day is splitted
        :param central: portion compared to early and late in which the part of the day is splitted
        :param late: portion compared to central and early in which the part of the day is splitted
        :return: tuple (from_datetime, to_datetime)
        """

        if early == None: early = config.default_early
        if central == None: central = config.default_central
        if late == None: late = config.default_late

        total = early + central + late
        early, central, late = early / total, central / total, late / total
        start, end, delta = 0, 0, 0
        if moment == config.tasker_config['day_timezone']['early_morning']:

            start = time_start_working_day
            delta = (datetime.timedelta(minutes = int(((time_start_lunch-time_start_working_day).total_seconds()//60)*early)))
            end   = start + delta

        elif moment == config.tasker_config['day_timezone']['morning']:

            start = Task.get_daymoment_limit(config, config.tasker_config['day_timezone']['early_morning'], time_start_working_day, time_start_lunch, time_end_lunch, time_end_working_day, time_start_dinner, time_end_dinner, time_end_day)[1];
            delta = (datetime.timedelta(minutes = int(((time_start_lunch-time_start_working_day).total_seconds()//60)*central)))
            end   = start + delta

        elif moment == "late_morning":

            start = Task.get_daymoment_limit(config, config.tasker_config['day_timezone']['morning'], time_start_working_day, time_start_lunch, time_end_lunch, time_end_working_day, time_start_dinner, time_end_dinner, time_end_day)[1];
            delta = (datetime.timedelta(minutes = int(((time_start_lunch-time_start_working_day).total_seconds()//60)*late)))
            end   = start + delta
            if end > time_start_lunch:
                end = time_start_lunch

        elif moment == config.tasker_config['day_timezone']['early_afternoon']:

            start = time_end_lunch
            delta = (datetime.timedelta(minutes = int(((time_start_dinner-time_end_lunch).total_seconds()//60)*early)))
            end   = start + delta

        elif moment == config.tasker_config['day_timezone']['afternoon']:

            start = Task.get_daymoment_limit(config, config.tasker_config['day_timezone']['early_afternoon'], time_start_working_day, time_start_lunch, time_end_lunch, time_end_working_day, time_start_dinner, time_end_dinner, time_end_day)[1]
            delta = (datetime.timedelta(minutes = int(((time_start_dinner-time_end_lunch).total_seconds()//60)*central)))
            end   = start + delta

        elif moment == "late_afternoon":

            start = Task.get_daymoment_limit(config, config.tasker_config['day_timezone']['afternoon'], time_start_working_day, time_start_lunch, time_end_lunch, time_end_working_day, time_start_dinner, time_end_dinner, time_end_day)[1]
            delta = (datetime.timedelta(minutes = int(((time_start_dinner-time_end_lunch).total_seconds()//60)*late)))
            end   = start + delta
            if end > time_start_dinner:
                end = time_start_dinner

        elif moment == config.tasker_config['day_timezone']['early_evening']:

            start = time_end_dinner
            delta = (datetime.timedelta(minutes = int(((time_end_day-time_end_dinner).total_seconds()//60)*early)))
            end   = time_end_dinner

        elif moment == config.tasker_config['day_timezone']['evening']:

            start = Task.get_daymoment_limit(config, config.tasker_config['day_timezone']['early_evening'], time_start_working_day, time_start_lunch, time_end_lunch, time_end_working_day, time_start_dinner, time_end_dinner, time_end_day)[1]
            delta = (datetime.timedelta(minutes = int(((time_end_day-time_end_dinner).total_seconds()//60)*central)))
            end   = start + delta

        elif moment == config.tasker_config['day_timezone']['late_evening']:

            start = Task.get_daymoment_limit(config, config.tasker_config['day_timezone']['evening'], time_start_working_day, time_start_lunch, time_end_lunch, time_end_working_day, time_start_dinner, time_end_dinner, time_end_day)[1]
            delta = (datetime.timedelta(minutes = int(((time_end_day-time_end_dinner).total_seconds()//60)*late)))
            end   = start + delta
            if end > time_end_day:
                end = time_end_day

        return start, end, delta

    @staticmethod
    def get_temporal_slots( config,
                            time_start_working_day,
                            time_start_lunch,
                            time_end_lunch,
                            time_end_working_day,
                            time_start_dinner,
                            time_end_dinner,
                            time_end_day
                            ):
        """
        Provide time slots for every part of the day
        :param time_start_working_day: daylight start time
        :param time_start_lunch: lunch start time
        :param time_end_lunch: lunch end time
        :param time_end_working_day: work time end time
        :param time_start_dinner: dinner start time
        :param time_end_dinner: dinner end time
        :param time_end_day: daylight end time
        :param early: portion compared to central and late in which the part of the day is splitted
        :param central: portion compared to early and late in which the part of the day is splitted
        :param late: portion compared to central and early in which the part of the day is splitted
        :return: list temporal_slots
        """

        early   = config.default_early
        central = config.default_central
        late    = config.default_late

        temporal_slots = {}
        ordered_slots = []

        for moment in config.tasker_config['day_timezone_ordered']:
            temporal_slots[moment] = {}
            couple = Task.get_daymoment_limit(config,
                                                moment,
                                                time_start_working_day,
                                                time_start_lunch,
                                                time_end_lunch,
                                                time_end_working_day,
                                                time_start_dinner,
                                                time_end_dinner,
                                                time_end_day,
                                                early,
                                                central,
                                                late)
            temporal_slots[moment]['from'], temporal_slots[moment]['to'], temporal_slots[moment]['delta'], = couple[0], couple[0]+couple[2], couple[2]

            if moment != config.tasker_config['day_timezone']['early_morning']:
                temporal_slots[moment]['from'] = temporal_slots[previous]['to']
                temporal_slots[moment]['to'] = temporal_slots[moment]['from']+temporal_slots[moment]['delta']
            if moment == config.tasker_config['day_timezone']['late_morning']:
                temporal_slots[moment]['to'] = time_start_lunch
            if moment == config.tasker_config['day_timezone']['early_afternoon']:
                temporal_slots[moment]['from'] = time_end_lunch
                temporal_slots[moment]['to'] = temporal_slots[moment]['from']+temporal_slots[moment]['delta']
            if moment == config.tasker_config['day_timezone']['late_afternoon']:
                temporal_slots[moment]['to'] = time_start_dinner
            if moment == config.tasker_config['day_timezone']['early_evening']:
                temporal_slots[moment]['from'] = time_end_dinner
                temporal_slots[moment]['to'] = temporal_slots[moment]['from']+temporal_slots[moment]['delta']

            ordered_slots.append(moment)
            previous = moment

        return temporal_slots

    @staticmethod
    def get_day_time(config, default_date = False, start_day=None):
        """
        Set deadline for the day
        :param default_date:
        :return: tuple with the hours of day for set limits
        """
        if not default_date:
            time_start_working_day   = str(raw_input("Start Day    %s: " % (config.default_time_start_working_day)))
            time_start_lunch         = str(raw_input("Start Lunch  %s: " % (config.default_time_start_lunch)))
            time_end_lunch           = str(raw_input("End Lunch    %s: " % (config.default_time_end_lunch)))
            time_end_working_day     = str(raw_input("End W Day    %s: " % (config.default_time_end_working_day)))
            time_start_dinner        = str(raw_input("Start Dinner %s: " % (config.default_time_start_dinner)))
            time_end_dinner          = str(raw_input("End Dinner   %s: " % (config.default_time_end_dinner)))
            time_end_day             = str(raw_input("End Day      %s: " % (config.default_time_end_day)))

            if len(time_start_working_day) == 0:   time_start_working_day   = config.default_time_start_working_day
            if len(time_start_lunch) == 0:         time_start_lunch         = config.default_time_start_lunch
            if len(time_end_lunch) == 0:           time_end_lunch           = config.default_time_end_lunch
            if len(time_end_working_day) == 0:     time_end_working_day     = config.default_time_end_working_day
            if len(time_start_dinner) == 0:        time_start_dinner        = config.default_time_start_dinner
            if len(time_end_dinner) == 0:          time_end_dinner          = config.default_time_end_dinner
            if len(time_end_day) == 0:             time_end_day             = config.default_time_end_day
        else:
            time_start_working_day   = config.default_time_start_working_day
            time_start_lunch         = config.default_time_start_lunch
            time_end_lunch           = config.default_time_end_lunch
            time_end_working_day     = config.default_time_end_working_day
            time_start_dinner        = config.default_time_start_dinner
            time_end_dinner          = config.default_time_end_dinner
            time_end_day             = config.default_time_end_day

        today = datetime.date.today().strftime("%d %B %Y")
        if start_day != None:
            today = start_day.strftime("%d %B %Y")

        time_start_working_day = datetime.datetime.strptime(today + " - " + time_start_working_day, "%d %B %Y - %H:%M")
        time_start_lunch = datetime.datetime.strptime(today + " - " + time_start_lunch, "%d %B %Y - %H:%M")
        time_end_lunch = datetime.datetime.strptime(today + " - " + time_end_lunch, "%d %B %Y - %H:%M")
        time_end_working_day = datetime.datetime.strptime(today + " - " + time_end_working_day, "%d %B %Y - %H:%M")
        time_start_dinner = datetime.datetime.strptime(today + " - " + time_start_dinner, "%d %B %Y - %H:%M")
        time_end_dinner = datetime.datetime.strptime(today + " - " + time_end_dinner, "%d %B %Y - %H:%M")
        time_end_day = datetime.datetime.strptime(today + " - " + time_end_day, "%d %B %Y - %H:%M")

        return time_start_working_day, time_start_lunch, time_end_lunch, time_end_working_day, time_start_dinner, time_end_dinner, time_end_day

    @staticmethod
    def get_tasks_statistics(config, tasks):

        tasks_list = config.task_list.values()

        tasks_name = sorted(list(set(task[0] for task in tasks)))
        tasks_name_dict = {}
        for task_name in tasks_name: tasks_name_dict[task_name] = datetime.timedelta(minutes = 0)
        total_time = 0.0
        for task in tasks:
            tasks_name_dict[task[0]] += datetime.timedelta(minutes = int(((task[2]-task[1]).total_seconds()//60)))
            total_time += int(((task[2]-task[1]).total_seconds()//60))

        for task_name in tasks_name:
            ty = Task.get_activity_from_array(task_name, tasks_list)
            if ty != None: ty = ty.task_type
            else: ty = -1
            print '%15s %2.0f%% | %39s' % (tasks_name_dict[task_name], \
                   float((tasks_name_dict[task_name].total_seconds()//60)/total_time)*100, task_name)
        print

    @staticmethod
    def get_task_type_statistics(config, tasks):

        tasks_list = config.task_list.values()

        tasks_name = []
        for task in tasks:
            act = Task.get_activity_from_array(task[0], tasks_list)
            if act != None: tasks_name.append(act.task_type)
        tasks_name = sorted(list(set(tasks_name)))
        tasks_name_dict = {}
        for task_name in tasks_name: tasks_name_dict[task_name] = datetime.timedelta(minutes = 0)
        total_time = 0.0
        for task in tasks:
            act = Task.get_activity_from_array(task[0], tasks_list)
            if act != None:
                tasks_name_dict[act.task_type] += datetime.timedelta(minutes = int(((task[2]-task[1]).total_seconds()//60)))
                total_time += int(((task[2]-task[1]).total_seconds()//60))

        for task_name in tasks_name:
            print '%15s %2.0f%% | %39s' % (tasks_name_dict[str(task_name)], \
                   float((tasks_name_dict[task_name].total_seconds()//60)/total_time)*100, config.task_type_code[str(task_name)])
        print

    @staticmethod
    def check_max_minute_constraint(self):
        pass

    @staticmethod
    def resolve_max_minute_conflict(self):
        pass

    @staticmethod
    def check_min_minute_constraint(self):
        pass

    @staticmethod
    def resolve_min_minute_conflict(self):
        pass

    @staticmethod
    def planning_moment(config, temporal_slots):

        tasks_list = config.task_list.values()

        tasks = {}
        for moment in config.tasker_config['day_timezone_ordered']:
            tasks[moment] = []
        goon = True
        while goon:
            for moment in config.tasker_config['day_timezone_ordered']:
                if temporal_slots[moment]['from'] < temporal_slots[moment]['to']:
                    all_possible_task = list(config.tasker_config['all_act_name'])
                    found = 0
                    while len(all_possible_task) > 0 and found == 0:
                        task = Task.get_activity_from_array(Task.weighted_random(config.daymoment_activity_probability[moment]), tasks_list)
                        if len(tasks[moment]) == 0:
                            starttime = temporal_slots[moment]['from']
                        else:
                            starttime = tasks[moment][-1][2]
                        endtime = starttime+datetime.timedelta(minutes = int(task.slot_duration))
                        reduced = starttime+datetime.timedelta(minutes = int(task.slot_duration * config.tasker_config['percentage_activity_slot']))
                        if endtime <= temporal_slots[moment]['to']:
                            tasks[moment].append([task.name, starttime, endtime])
                            found = 1
                        elif reduced <= temporal_slots[moment]['to']:
                            tasks[moment].append([task.name, starttime, reduced])
                            found = 1
                        else:
                            if task.name in all_possible_task:
                                all_possible_task.remove(task.name)
                            if len(all_possible_task) == 0: found = 2

                    if found == 2 and tasks[moment][-1][0] != 'FREE_TIME' and tasks[moment][-1][2] < temporal_slots[moment]['to']:
                        tasks[moment].append(['FREE_TIME', tasks[moment][-1][2], temporal_slots[moment]['to']])

            goon = Task.check_model(config, tasks, temporal_slots)

        tasks_list = []
        for moment in config.tasker_config['day_timezone_ordered']:
            if temporal_slots[moment]['from'] < temporal_slots[moment]['to']:
                for task in tasks[moment]:
                    tasks_list.append(task)
                    if tasks_list[-1][2] == temporal_slots['late_morning']['to']:
                        pass
                        #tasks_list.append(['Lunch', temporal_slots['late_morning']['to'], temporal_slots['early_afternoon']['from']])
                    if tasks_list[-1][2] == temporal_slots['late_afternoon']['to']:
                        pass
                        #tasks_list.append(['Dinner', temporal_slots['late_afternoon']['to'], temporal_slots['early_evening']['from']])

        return tasks_list

    @staticmethod
    def insert_involved_tasks(config, relevant_events, tasks, temporal_slots):
        # support variables
        task_start_index = 0
        task_end_index   = 0
        # for each event in the list to be entered
        for revent in relevant_events:
            # isolate parts of event 
            name      = revent[0]
            desc      = revent[1]
            starttime = revent[2]
            endtime   = revent[3]
            # if the start date is less than the end date of the last task in the schedule list
            if starttime < tasks[-1][2]:
                # print name, starttime, endtime
                # raw_input()
                # create a list of temporary tasks
                temporal_new_tasks = []
                # find the first task involved (later - looking to the start time - than the start time of the task to be entered)
                counter = 0
                for task in tasks:
                    if starttime >= task[1]:
                        task_start_index = counter
                    else:
                        break
                    counter += 1
                # print tasks[task_start_index]
                if tasks[task_start_index][2] > starttime:
                    tasks[task_start_index][2] = starttime
                # print tasks[task_start_index]
                # raw_input('Task_iniziale')

                # find the last task involved (such that the start date is after the date of the task to be entered)
                counter = task_start_index
                for task in tasks[task_start_index : -1]:
                    if endtime >= task[1]:
                        task_end_index   = counter
                    else:
                        break
                    counter += 1
                # print tasks[task_end_index]
                #
                # print tasks[task_start_index]
                if tasks[task_start_index][2] > starttime:
                    tasks[task_start_index][2] = starttime
                # print tasks[task_start_index]
                # raw_input('Task_finale')

                # if the task is the same
                if task_start_index == task_end_index:
                    # replace it with the event
                    tasks[task_start_index] = [revent[0], revent[2], revent[3], revent[1]]
                    # if the task is not the first
                    if task_start_index > 1:
                        # the previous task ends with the beginning of that entered
                        tasks[task_start_index-1][2] = tasks[task_start_index][1]
                    if task_start_index < len(tasks):
                        # the next task begins with the termination of the inserted one
                        tasks[task_start_index+1][1] = tasks[task_start_index][2]
                else:
                    for i in range(0, len(tasks)):
                        if i == task_end_index:
                            temporal_new_tasks.append([revent[0], revent[2], revent[3], revent[1]])
                        if i not in range(task_start_index, task_end_index):
                            temporal_new_tasks.append(tasks[i])
                    task_end_index = task_end_index - (task_end_index - task_start_index)
                    if task_end_index > 1:
                        temporal_new_tasks[task_end_index-1][2] = temporal_new_tasks[task_end_index][1]
                    if task_end_index < len(tasks):
                        temporal_new_tasks[task_end_index+1][1] = temporal_new_tasks[task_end_index][2]
                    tasks = temporal_new_tasks

        counter_moment = 0
        for moment in config.tasker_config['day_timezone_ordered']:
            if counter_moment == 0:
                if temporal_slots[moment]['from'] < temporal_slots[moment]['to']:
                    temporal_slots[moment]['from'] = tasks[0][1]
            counter_moment += 1

        # tasks = Task.fix_tasks_list(tasks)
        # if not Task.check_tasks_list(tasks): sys.exit(2)

        return tasks, temporal_slots

    @staticmethod
    def check_tasks_list(tasks):
        counter = 0
        for task in tasks[:-2]:
            if task[2] > tasks[counter+1][1]:
                return False
            counter += 1
        return True

    @staticmethod
    def fix_tasks_list(tasks):
        counter = 0
        for task in tasks[:-2]:
            if task[2] != tasks[counter+1][1]:
                task[2] = tasks[counter+1][1]
            counter += 1
        return tasks

    @staticmethod
    def check_model(config, tasks, temporal_slots):
        for moment in config.tasker_config['day_timezone_ordered']:
            if len(tasks[moment]) > 0:
                if tasks[moment][-1][2] < temporal_slots[moment]['to']:
                    return True
                elif tasks[moment][-1][2] > temporal_slots[moment]['to']:
                    sys.error('Last task bigger')
        return False

    @staticmethod
    def compress_tasks(tasks):
        """
        Comprises equivalent consecutive tasks in the same task
        :param tasks: tasks
        :return: compressed tasks
        """
        tasks_compress = [tasks[0]]
        for task in tasks[1:]:
            if tasks_compress[-1][0] == task[0]:
                tasks_compress[-1][2] = task[2]
            else:
                tasks_compress.append(task)
        return tasks_compress

    @staticmethod
    def get_activity_from_array(name, tasks):
        for task in tasks:
            if isinstance(task, list):
                if task[0] == name: return task
            else:
                if task.name == name: return task
        return None

    @staticmethod
    def weighted_random(weights):
        number = random.random() * sum(weights.values())
        for k, v in weights.iteritems():
            if number < v:
                break
            number -= v
        return k