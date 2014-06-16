# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os

import harmony.session


class Session(harmony.session.Session):
    '''Session.'''

    DEFAULT_SCHEMA_PATH = os.environ.get(
        'FTRACK_SCHEMA_PATH',
        os.path.join(
            os.path.dirname(__file__), '..', '..', 'resource', 'schema'
        )
    )

    def __init__(self, *args, **kw):
        '''Initialise session.'''
        ftrack = kw.pop('ftrack', None)
        self.ftrack = ftrack
        if self.ftrack is None:
            # Note: Late import to allow configuring of ftrack credentials.
            import ftrack
            self.ftrack = ftrack

        super(Session, self).__init__(*args, **kw)
