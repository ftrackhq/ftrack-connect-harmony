# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import harmony.ui.widget.array


class ComponentArray(harmony.ui.widget.array.Array):
    '''Display a list of configurable components.

    Supports drag and drop.

    '''

    def __init__(self, session, *args, **kw):
        '''Initialise with *session*.'''
        self._session = session
        super(ComponentArray, self).__init__(*args, **kw)

    def _postConstruction(self):
        '''Perform post-construction operations.'''
        super(ComponentArray, self)._postConstruction()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        '''Handle drag enter *event*.'''
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        '''Handle drop *event*.'''
        # TODO: Detect sequences.
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            row = self._itemList.rowCount()

            entry = self._session.instantiate(
                'harmony:/component',
                {'path': path}
            )

            self._addItem(row, value=entry)
            self._emitValueChanged()
