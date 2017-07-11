#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Matteo'

import pprint
import time
import datetime
import argparse
from lib.task import Task
from googleapiclient.discovery import *
from httplib2 import Http
from oauth2client import file, client, tools

def get_service_obj(config):
    scopes = config.google_calendar_config['scopes']
    store = file.Storage(config.google_calendar_config['store'])
    creds = store.get()
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    flags = parser.parse_args()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(config.google_calendar_config['client_secret_file'], scopes)
        creds = tools.run_flow(flow, store, flags)
    service = build('calendar', 'v3', http=creds.authorize(Http()))
    return service

def get_cal_id(service, name):
    import sys
    reload(sys)
    sys.setdefaultencoding("utf-8")
    try:
        calendars_list = service.calendarList().list().execute()
        # pprint.pprint(calendars_list)
        for calendars_list_entry in calendars_list['items']:
            # print name, calendars_list_entry
            if 'summary' in calendars_list_entry.keys():
                # print calendars_list_entry['summary'], name
                if unicode(calendars_list_entry['summary']) == unicode(name):
                    # print "\t", str(calendars_list_entry['summary']), name
                    # print calendars_list_entry
                    return calendars_list_entry['id']
            if 'summaryOverride' in calendars_list_entry.keys():
                # print str(calendars_list_entry['summaryOverride']), name
                if unicode(calendars_list_entry['summaryOverride']) == unicode(name):
                    # print "\t", str(calendars_list_entry['summaryOverride']), name
                    # print calendars_list_entry
                    return calendars_list_entry['id']

    except Exception, e:
        print e
        return e.message

    return None

def create_gcal_event(service, calendar_id, json_event):

    try:
        task = service.events().insert(calendarId = calendar_id, body = json_event).execute()
        # print('Task %s created: %s' % (json_event['summary'], task.get('htmlLink')))
    except Exception, e:
        print e.message

def task_to_json(config, task, tasks):

    event = {}
    event['summary'] = task[0]
    event['start'] = {}
    event['start']['dateTime'] = task[1].strftime("%Y-%m-%dT%H:%M:%S")+config.google_calendar_config['gmt_off']
    event['end'] = {}
    event['end']['dateTime'] = task[2].strftime("%Y-%m-%dT%H:%M:%S")+config.google_calendar_config['gmt_off']

    if config.reminders[0]:
        event['reminders'] = {}
        event['reminders']['useDefault'] = False
        event['reminders']['overrides'] = []
        event['reminders']['overrides'].append({'method':'popup', 'minutes' : config.reminders[1]})

    actvity = Task.get_activity_from_array(task[0], tasks)
    if actvity != None and actvity.description != None:
        event['description'] = actvity.description
    elif len(task) > 3 and task[3] != None:
        event['description'] = task[3]

    # event = {
    #   'summary': 'Google I/O 2015',
    #   'location': '800 Howard St., San Francisco, CA 94103',
    #   'description': 'A chance to hear more about Google\'s developer products.',
    #   'start': {
    #     'dateTime': '2015-05-28T09:00:00-07:00',
    #     'timeZone': 'America/Los_Angeles',
    #   },
    #   'end': {
    #     'dateTime': '2015-05-28T17:00:00-07:00',
    #     'timeZone': 'America/Los_Angeles',
    #   },
    #   'recurrence': [
    #     'RRULE:FREQ=DAILY;COUNT=2'
    #   ],
    #   'attendees': [
    #     {'email': 'lpage@example.com'},
    #     {'email': 'sbrin@example.com'},
    #   ],
    #   'reminders': {
    #     'useDefault': False,
    #     'overrides': [
    #       {'method': 'email', 'minutes': 24 * 60},
    #       {'method': 'popup', 'minutes': 10},
    #     ],
    #   },
    # }

    return event

def get_calendar_events(config, service, calendar_ids, min, max):

    # now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    min = min.isoformat() + 'Z'
    max = max.isoformat() + 'Z'

    all_events = []
    for calendar_name, calendar_id in calendar_ids.iteritems():
        # print('Getting the upcoming %s events on %s' % (next, calendar_name))
        eventsResult = service.events().list(
            calendarId = calendar_id,
            timeMin = min,
            timeMax = max,
            singleEvents = True,
            orderBy = 'startTime').execute()
        events = eventsResult.get('items', [])

        if not events:
            pass
            # print('No upcoming events found.')
        for event in events:
            name  = event['summary']
            start = event['start'].get('dateTime', event['start'].get('date'))
            if len(start) < 11:
                start = start+"T00:00:00"
            else:
                start = start[:-7]
            start = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
            end   = event['end'].get('dateTime', event['end'].get('date'))
            if len(end) < 11:
                end = end+"T00:00:00"
            else:
                end = end[:-7]
            end   = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S')
            desc  = None
            if 'description' in event.keys(): desc = event['description']
            all_events.append([name, desc, start, end])
            # print start, end, name, desc

    all_events.sort(key = lambda event: event[2], reverse = False)
    # for event in all_events:
        # pass
        # print event[2], event[3], event[0], event[1]

    return all_events


def get_relevant_events(config, service, calendars_name, start_day, end_day):
    calendar_ids = {}
    for calendar_name in calendars_name:
        res = get_cal_id(service, calendar_name)
        if res != None: calendar_ids[calendar_name] = res
    # print calendar_ids
    return get_calendar_events(config, service, calendar_ids, start_day, end_day)