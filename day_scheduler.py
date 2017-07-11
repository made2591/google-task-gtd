#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lib.util import set_to_midnight, save_file, load_file

__author__ = 'matteo'

from lib.task import Task
from lib.config import Config
from lib.gcal import *

# tasker's configuration files
config_file = './config/default_one_config.json'

# reading and creation of tasks' configuration object
task_file = './config/default_one_tasks.json'

# list of involved calendar to prevent collision in scheduling
# events already scheduled in this calendar will be inserted in scheduling without overlap
calendars_name = ['Testing']

# output calendar name
scheduling_calendar_name = 'Schedule'

# insert different timeout hours (launch, dinner, etc) for each day
intercative_hour_choices = False

# for debug
schedule_saving_path = './out'

#################################################################################################
################ TASKE - PROGRAMM TO CREATE A WEEK SCHEDULE FOR THIS / NEXT WEEK ################
#################################################################################################

# creation of configuration object for tasker
config = Config(config_file, task_file)

# google calendar service instance creation
service = get_service_obj(config)

# find actual date, actual week monday, next week monday day
today = datetime.datetime.today()
# today = datetime.datetime(2015, 11, 30)
# today = datetime.datetime(2015, 12, 1)
# today = datetime.datetime(2015, 12, 2)
# today = datetime.datetime(2015, 12, 3)
# today = datetime.datetime(2015, 12, 3)

# get calendar id to save scheduling
calendar_id = get_cal_id(service, scheduling_calendar_name)

r = 1
while r == 1:

    # start and end time calculation
    end_day    = set_to_midnight(today + datetime.timedelta(days = 1))
    start_day  = set_to_midnight(today)

    # Day scheduling 
    print "Day scheduling  %s." % start_day.strftime("%d %B %Y")

    # day time calculation
    time_start_working_day, \
    time_start_lunch, \
    time_end_lunch, \
    time_end_working_day, \
    time_start_dinner, \
    time_end_dinner, \
    time_end_day = Task.get_day_time(config, default_date = (not intercative_hour_choices), start_day = start_day)

    # temporal_slots calculation
    temporal_slots = Task.get_temporal_slots(config, \
                                             time_start_working_day, \
                                             time_start_lunch, \
                                             time_end_lunch, \
                                             time_end_working_day, \
                                             time_start_dinner, \
                                             time_end_dinner, \
                                             time_end_day)

    # get list of relevant events
    relevant_events = events = get_relevant_events(config, service, calendars_name, start_day, end_day)

    # pause to let output visualization
    go_on = raw_input('\nPress c to exit, any to print events of  %s.\n' % start_day.strftime("%d %B %Y"))
    if go_on == 'c':
        exit(1)

    # print events of start_day
    for event in relevant_events:
        print event[2].strftime("%H:%M"), event[3].strftime("%H:%M"), event[0], event[1]

    # pause to let output visualization
    if len(relevant_events) == 0:
        print "No relevant event in  %s." % start_day.strftime("%d %B %Y")

    # induce the likelihood of the activities to be included
    Task.induce_probabilities(config)

    # generated task compression
    tasks = Task.compress_tasks(Task.planning_moment(config, temporal_slots))

    # generated task saving
    # save_file(tasks, filename = schedule_saving_path + (start_day.strftime("%d_%B_%Y")))
    # generated task loading
    # tasks = load_file(filename = schedule_saving_path + (start_day.strftime("%d_%B_%Y")))

    # pause to let output visualization
    go_on = raw_input('\nPress c to exit, any to print generated schedule for \n')
    if go_on == 'c':
        exit(1)

    # print day time of the day
    Task.print_temporal_slots_table(config, temporal_slots)

    # print generated tasks
    Task.print_one_day_tasks(config, tasks, temporal_slots)

    # if there are some events in provided calendars
    if len(relevant_events) > 0:

        # insert of events already present in calendars provided in the list above into generated tasks list
        tasks, temporal_slots = Task.insert_involved_tasks(config, relevant_events, tasks, temporal_slots)

        # pause to let output visualization
        go_on = raw_input('\nPress c to exit, any to print generated schedule with events of calendar provided above.\n')
        if go_on == 'c':
            exit(1)

        # print list of tasks updated with event
        Task.print_one_day_tasks(config, tasks, temporal_slots)

    # print stats
    Task.get_tasks_statistics(config, tasks)

    # print stats
    Task.get_task_type_statistics(config, tasks)

    # pause to let output visualization
    go_on = raw_input('\nPress c to exit, y to insert generated schedule with events in calendar %s, n to create a new schedule.\n' % scheduling_calendar_name)

    # debug per debug
    go_on = 'c'

    if go_on == 'y':
        # for each task in task list
        for task in tasks:
            to_add = True
            for revent in relevant_events:
                if task[0] == revent[0]:
                    to_add = False
                    break
            if to_add:
                # creation of json event for insertion
                json_task = task_to_json(config, task, config.task_list)
                # aggiungo l'evento al calendario sopra specificato
                create_gcal_event(service, calendar_id, json_task)
        r = 0
    elif go_on == 'c':
        r = 0