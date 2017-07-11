#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Matteo'

from lib.util import save_file, load_file, set_to_midnight
from lib.config import Config
from lib.gcal import *
from lib.task import *

# file di configurazione del tasker
config_file = './config/default_one_config.json'

# leggo e creo l'oggetto di configurazione dei task
task_file = './config/default_one_tasks.json'

# elenco di calendari dei quali tenere conto
# serve per poter decidere quali sono gli eventi da
# inserire nello scheduling
# calendars_name = ['Testing']

# nome del calendario dentro cui inserire lo scheduling della giornata
scheduling_calendar_name = 'Schedule'

# insert different timeout hours (launch, dinner, etc) for each day
intercative_hour_choices = False

# for debug
schedule_saving_path = './out'

# schedule this week, or the next one
this_week = True

from_tomorrow_to_friday = True


#################################################################################################
################ TASKE - PROGRAMM TO CREATE A WEEK SCHEDULE FOR THIS / NEXT WEEK ################
#################################################################################################

# creation of configuration object for tasker
config = Config(config_file, task_file)

# google calendar service instance creation
service = get_service_obj(config)

# find actual date, actual week monday, next week monday day
today = datetime.datetime.today()
# debug
# today = datetime.datetime(2015, 12, 10)
nextmonday = today + datetime.timedelta(days = -today.weekday(), weeks=1)
lastmonday = today - datetime.timedelta(days =  today.weekday())

# se è abilitata la richiesta della prossima settimana
if not this_week:
    lastmonday = nextmonday

if from_tomorrow_to_friday:
    lastmonday += datetime.timedelta(days = +1)

nextfriday = lastmonday
while nextfriday.weekday() != 4:
    nextfriday += datetime.timedelta(1)

# get calendar id to save scheduling
calendar_id = get_cal_id(service, scheduling_calendar_name)

all_tasks = []

go_on = 'j'

counter = lastmonday

# per 5 giorni della settimana
while counter <= nextfriday:

    # start and end time calculation
    end_day    = set_to_midnight(counter + datetime.timedelta(days = +1))
    start_day  = set_to_midnight(counter)

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
    temporal_slots = Task.get_temporal_slots(config, time_start_working_day, time_start_lunch, time_end_lunch, time_end_working_day,
                                                 time_start_dinner, time_end_dinner, time_end_day)

    # get list of relevant events
    relevant_events = get_relevant_events(config, service, calendars_name, start_day, end_day)

    # pause to let output visualization
    # go_on = raw_input('\nPress c to exit, any to print events of  %s.\n' % start_day.strftime("%d %B %Y"))
    if go_on == 'c':
        exit(1)

    # print events of start_day
    for event in relevant_events:
        print event[2].strftime("%d/%B/%Y - %H:%M"), event[3].strftime("%d %B %Y - %H:%M"), event[0], event[1]

    # pause to let output visualization
    if len(relevant_events) == 0:
        print "No relevant event in  %s." % start_day.strftime("%d %B %Y")

    # induce the likelihood of the activities to be included
    Task.induce_probabilities(config)
    # generated task compression
    tasks = Task.compress_tasks(Task.planning_moment(config, temporal_slots))

    # generated task saving
    save_file(tasks, filename = schedule_saving_path + (start_day.strftime("%d_%B_%Y")))
    # generated task loading
    tasks = load_file(filename = schedule_saving_path + (start_day.strftime("%d_%B_%Y")))

    # pause to let output visualization
    # go_on = raw_input('\nPress c to exit, any to print generated schedule for \n')
    if go_on == 'c':
        exit(1)

    # print generated tasks
    Task.print_one_day_tasks(config, tasks, temporal_slots)

    # if there are some events in provided calendars
    if len(relevant_events) > 0:

        # insert of events already present in calendars provided in the list above into generated tasks list
        tasks, temporal_slots = Task.insert_involved_tasks(config, relevant_events, tasks, temporal_slots)

        # pause to let output visualization
        # go_on = raw_input('\nPress c to exit, any to print generated schedule with events of calendar provided above.\n')
        if go_on == 'c':
            exit(1)

        # print list of tasks updated with event
        Task.print_one_day_tasks(config, tasks, temporal_slots)

    # print stats
    Task.get_tasks_statistics(config, tasks)

    # print stats
    Task.get_task_type_statistics(config, tasks)

    # pause to let output visualization
    go_on = raw_input('\nPress:\n- c to exit\n- y to insert generated schedule in calendar %s\n- n to create new schedule\n- j or empty to jump insert and go ahead to next day\n\n' % scheduling_calendar_name)

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
                json_task = task_to_json(config, task)
                # aggiungo l'evento al calendario sopra specificato
                create_gcal_event(service, calendar_id, json_task)
        counter += datetime.timedelta(1)

        for t in tasks:
            all_tasks.append(t)

    elif go_on == 'c':

        exit(1)

    elif go_on != 'n':

        counter += datetime.timedelta(1)

# print all_tasks

# print stats
Task.get_tasks_statistics(config, all_tasks)

# print stats
Task.get_task_type_statistics(config, all_tasks)
