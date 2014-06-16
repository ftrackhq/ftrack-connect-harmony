# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import json
import pprint

from PySide import QtCore
import harmony.ui.publisher
import jsonpointer


class Publisher(harmony.ui.publisher.Publisher):
    '''Publisher.'''

    HARMONY_PUBLISH_ENTITY = 'AssetVersion'

    valueChanged = QtCore.Signal()

    def _postConstruction(self):
        '''Perform post-construction operations.'''
        super(Publisher, self)._postConstruction()
        self.setWindowTitle('ftrack publisher')

    def setValue(self, value):
        '''Set *value*.'''
        widget = self._schemaDetailsArea.widget()
        if widget:
            widget.setValue(value)

    def value(self):
        '''Return current value.'''
        widget = self._schemaDetailsArea.widget()
        if widget:
            return widget.value()
        else:
            return None

    def _onValueChanged(self):
        '''Handle change in value.'''
        super(Publisher, self)._onValueChanged()
        self.valueChanged.emit()

    def _filterSchemas(self, schemas):
        '''Return a list of *schemas* to display as options in the selector.'''
        filtered = []
        for schema in schemas:
            if schema.get('id', '').startswith('harmony:/asset_version/'):
                filtered.append(schema)

        return filtered

    def selectSchema(self, schema):
        '''Set *schema* as active schema.'''
        index = self._schemaSelector.findText(schema)
        self._schemaSelector.setCurrentIndex(index)

    def _onSelectSchema(self, index):
        '''Handle schema selection.'''
        currentValue = self.value()
        super(Publisher, self)._onSelectSchema(index)

        # Reset reusable values.
        if currentValue:
            newValue = self.value()
            newValue.setdefault('author', currentValue.get('author'))
            self.setValue(newValue)

        # Hide redundant outermost container widget details.
        schemaDetails = self._schemaDetailsArea.widget()
        if schemaDetails:
            schemaDetails._titleLabel.hide()
            schemaDetails._errorIndicator.hide()

    def _publish(self, instance):
        '''Publish *instance*.'''
        schema = self._schemaSelector.itemData(
            self._schemaSelector.currentIndex()
        )

        schemaReference = instance.get('harmony_type')
        if not schemaReference:
            raise ValueError(
                'Cannot publish instance with missing "harmony_type" reference.'
            )

        if not schemaReference.startswith('harmony:/asset_version/'):
            raise ValueError(
                'Cannot publish instance whose "schema" reference does not '
                'start with "harmony:/asset_version/": {0}'
                .format(schemaReference)
            )

        publishType = schemaReference[len('harmony:/asset_version/'):]

        # Determine ftrack parent for asset.
        parent = self._session.ftrack.Task(
            instance['domain']['asset']['id']
        )

        # Construct unique asset name from identifiers.
        identifiers = schema.get('identifiers', ['/asset_name'])
        assetName = []
        for identifier in identifiers:
            if identifier.startswith('/domain'):
                continue

            assetName.append(jsonpointer.resolve_pointer(instance, identifier))

        assetName = '-'.join(assetName).lower().replace(' ', '_')

        # Ensure asset exists.
        asset = parent.createAsset(
            name=assetName,
            assetType=publishType
        )

        # Publish new version under asset.
        version = asset.createVersion(
            comment=instance['comment']
        )

        # Store all Harmony data as metadata for reference.
        metadata = json.dumps(instance)
        version.setMeta('harmony', metadata)

        # Set publish flag so version visible.
        asset.publish()

        # Create components.
        for component in instance['components']:
            version.createComponent(
                name=component['label'],
                path=component['path']
            )

    def _postPublish(self, instance, published):
        '''Post publish.'''
        super(Publisher, self)._postPublish(instance, published)
        pprint.pprint(published)
