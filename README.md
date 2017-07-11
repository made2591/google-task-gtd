# GoogleTask

GoogleTask is a python utility to generate schedules based on a JSON dictionary with typical activities, in accordance with the commitments already taken during the day in specified calendars.

Run on Python v2. It has following dependencies:

- google-api-python-client==1.6.2
- httplib2==0.10.3
- oauth2client==4.1.2
- pyasn1==0.2.3
- pyasn1-modules==0.0.9
- rsa==3.4.2
- six==1.10.0
- uritemplate==3.0.0

After cloning, run the following (eventually in virtualenv):

```shell
pip install -r requirements.txt
```

### Idea

I started this project some years ago after buying a Pebble Smartwatch (v2): it had a Timeline interface synced with my iPhone calendar so I create this lib to help me find motivations to carry out different projects without lose priorities (my thesis work). After a few months Google Goal came out so...you know :-). The idea is: using configuration file (look at default\_one\_tasks.json), create random task and try to fill the day with activities you want to carry on without overlap events already defined in your calendar.

### Task

All the lib is defined around Task concept. The Task (class defined in lib package) represents an Activity: it has a name, a type, an importance, a list of daytimes in which it is more appropriate, a description that contains a count for several daytime slots in which the activity will be replicated during the day. It may also contain constraints.

### Core

The idea is simple: first, split the day using parameters defined in configuration files. Second, randomly generate tasks and try to fit all timeslots. Each task is defined also in term of "minimum number of minutes" before discard, probabilities for generation, etc (look at default\_one\_tasks.json)

### Merge

The lib provide API to save scheduling to a Google calendar, also considering events in one or more calendar (to fill the day without overlaps events you manually created outside the use of library).

### Main

You can try the lib using this:

```shell
python day_scheduler.py
```

as a main. It provides a good start point to test the library and google calendar integration.

### Features:
- high parametric support to split each part of day in snapshot;
- high parametric support to define task properties (type, priorities, even in each part of day);
- pretty print of schedule for linux user (crontab job to see a proposal for each in your desktop);
- print statistics to test configuration setup for each task;
- google calendar integration to create schedule in defined calendar;

### Todo:
- improve errors handling;
- improve algorithm to fill days;
- add theaters / wheater forecast / tvshow support to provide better proposal based on day;
- porting of logging (see project ****);

### Improvements
- parametric printing;
- logic control;