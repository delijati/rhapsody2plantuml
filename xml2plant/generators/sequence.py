#!/bin/env python2
import logging
from common import quote_if_space

from parsers.parser import PartType
from parsers.parser import EventType
from parsers.parser import MessageType


def find_nearest_lifeline(lifelines, position):

    # Start with large diff and unknown participant
    smallest_dist = 99999999
    smallest_part = None

    for key, part in sorted(lifelines.iteritems(), key=lambda kvt: kvt[1].position.top_left_x):
        if smallest_part == None:
            smallest_part = part

        dist = abs(part.position.get_center_x() - position.get_center_x())
        logging.debug("Nearest lifeline: Check: %s against %s", dist, smallest_dist)

        if smallest_dist < dist:
            return smallest_part
        else:
            smallest_part = part
            smallest_dist = dist

    assert smallest_part != None
    return smallest_part

def generate_plantuml_sequence(lifelines, chartdata):
    result = []

    result.append("@startuml")
    result.append("hide footbox")
    result.append("title %s" % chartdata["name"])
    result.append("")

    # Print order of participants
    for key, part in sorted(lifelines.iteritems(), key=lambda kvt: kvt[1].position.top_left_x):
        color = ""
        if part.fillstyle != 0:
            color = "#F5F5F5"

        if part.type == PartType.ACTOR:
            result.append('actor %s %s' % (quote_if_space(part.name), color))
        else:
            result.append('participant %s %s' % (quote_if_space(part.name), color))

        logging.debug("Position: %s", part.position)
    result.append("")

    # Print all events(messages/conditions and more)
    for event in sorted(chartdata["events"], key=lambda x: x.position.top_left_y):
        logging.debug("Print events: %s", event)

        # Handle messsage arrows
        if event.type == EventType.MESSAGE:
            arrow = "->"
            if event.type == MessageType.REPLY:
                arrow = "-->"
                
            result.append('%s %s %s : %s(%s)' % (quote_if_space(lifelines[event.sender].name),
                                                 arrow,
                                                 quote_if_space(lifelines[event.receiver].name),
                                                 event.name, event.args))

        elif event.type == EventType.COND_START:
            result.append("%s %s" % (event.cond, event.text))

        elif event.type == EventType.COND_ELSE:
            result.append("%s %s" % (event.cond, event.text))

        elif event.type == EventType.COND_END:
            result.append("end")

# TODO: span over many lifelines
        elif event.type == EventType.NOTE:
            text = event.text
            if len(lifelines) > 0:
                participant = find_nearest_lifeline(lifelines, event.position)
                if '\n' in text:
                    # Handle multiline notes
                    result.append('note over %s' % (quote_if_space(participant.name)))
                    result.append(text)
                    result.append('end note')
                else:
                    result.append('note over %s: %s' % (quote_if_space(participant.name), text))
            else:
                result.append('note top: %s' % (text))

# TODO: span over many lifelines
        elif event.type == EventType.REF:
            text = event.text
            if len(lifelines) > 0:
                participant = find_nearest_lifeline(lifelines, event.position)
                if '\n' in text:
                    # Handle multiline reference
                    result.append('ref over %s' % (quote_if_space(participant.name)))
                    result.append(text)
                    result.append('end ref')
                else:
                    result.append('ref over %s : %s' % (quote_if_space(participant.name), text))
            else:
                result.append('note top: %s' % (text))

        elif event.type == EventType.DIVIDER:
            result.append("== %s ==" % event.text)

        logging.debug("Position: %s", event.position)

    result.append("@enduml")
    return result
