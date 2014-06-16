# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import argparse
import logging
import sys
import getpass

import ftrack
from PySide import QtGui

from ftrack_connect_harmony.widget_factory import Factory
from ftrack_connect_harmony.publisher import Publisher
from ftrack_connect_harmony.session import Session


def main(arguments=None):
    '''ftrack connect harmony.'''
    if arguments is None:
        arguments = []

    parser = argparse.ArgumentParser()

    # Allow setting of logging level from arguments.
    loggingLevels = {}
    for level in (
        logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING,
        logging.ERROR, logging.CRITICAL
    ):
        loggingLevels[logging.getLevelName(level).lower()] = level

    parser.add_argument(
        '-v', '--verbosity',
        help='Set the logging output verbosity.',
        choices=loggingLevels.keys(),
        default='info'
    )

    namespace = parser.parse_args(arguments)

    logging.basicConfig(level=loggingLevels[namespace.verbosity])
    ftrack.setup()

    log = logging.getLogger('ftrack-connect-harmony.main')

    application = QtGui.QApplication('ftrack-connect-harmony')

    session = Session()
    factory = Factory(session)
    publisher = Publisher(session, factory)

    configure(publisher)

    publisher.resize(600, 800)
    publisher.show()

    return application.exec_()


def configure(publisher):
    '''Configure *publisher*.'''
    # TODO: Move to publisher as initial data?
    instance = publisher.value()

    users = publisher._factory._query_users()
    current_user = getpass.getuser()
    for user in users:
        if user.get('username') == current_user:
            instance['author'] = user
            break

    publisher.setValue(instance)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
