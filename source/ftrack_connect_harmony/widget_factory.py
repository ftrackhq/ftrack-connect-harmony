# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import operator
from functools import partial

from harmony.ui.model.templated_dictionary_list import TemplatedDictionaryList
from harmony.ui.widget.enum import Enum
from harmony.ui.widget.container import Container
from harmony.ui.widget.factory import Factory as BaseFactory

from .widget.component_array import ComponentArray


class Factory(BaseFactory):
    '''Customised widget factory.'''

    def __call__(self, schema, options=None):
        '''Return an appropriate widget for *schema*.'''
        schema_type = schema.get('type')
        schema_title = schema.get('title')
        schema_description = schema.get('description')
        schema_id = schema.get('id', '')

        # IDs
        if schema_id == 'harmony:/user':
            user_model = TemplatedDictionaryList(
                u'{firstname} {lastname} ({username})',
                self._query_users()
            )

            return Enum(
                user_model,
                title=schema_title,
                description=schema_description
            )

        elif schema_id.startswith('harmony:/scope'):
            scope = schema_id[len('harmony:/scope/'):]
            items = self._query_scopes(scope)

            return Enum(
                TemplatedDictionaryList(u'{name}', items),
                title=schema_title,
                description=schema_description
            )

        # Primitives
        if schema_type == 'object':
            # Construct child for each property.
            children = []
            properties = schema.get('properties', {})

            def order(item):
                '''Order item by 'order' key else by name.'''
                return item[1].get('order', item[0])

            required = schema.get('required')
            hide = ['harmony_type']

            # Hide version field.
            if schema_id.startswith('harmony:/asset_version'):
                hide.append('version')

            disable = []

            for name, subschema in sorted(properties.items(), key=order):
                child_widget = self(subschema, options=options)
                if name in required:
                    child_widget.setRequired(True)

                if name in hide:
                    child_widget.setHidden(True)

                if name in disable:
                    child_widget.setDisabled(True)

                children.append({'name': name, 'widget': child_widget})

            # Determine columns in layout.
            columns = 1
            if schema_id in ('harmony:/user', 'harmony:/resolution'):
                columns = 2

            widget = Container(
                title=schema_title,
                description=schema_description,
                children=children,
                columns=columns
            )

            # Hide header for components in component array.
            # TODO: Should be handled in the array widget factory construction?
            if schema_id == 'harmony:/component':
                widget._titleLabel.hide()
                widget._errorIndicator.hide()

            if schema_id.startswith('harmony:/domain'):
                # Watch for changes to each child of the domain (assumed to be
                # scope) and update other children as appropriate.
                for child in widget.children:
                    if isinstance(child['widget'], Enum):
                        child['widget'].valueChanged.connect(
                            partial(
                                self.onDomainChanged, child['widget'], widget
                            )
                        )

            return widget

        if schema_type == 'array' and schema_title == 'components':
            items = schema.get('items', [])
            if isinstance(items, dict):
                additional_item = items
                items = []
            else:
                additional_item = schema.get('additionalItems', None)

            types = []
            for subschema in items:
                types.append({
                    'constructor': partial(self, subschema, options=options),
                    'value': self.session.instantiate(subschema)
                })

            additional_type = None
            if additional_item is not None:
                additional_type = {
                    'constructor': partial(self, additional_item,
                                           options=options),
                    'value': self.session.instantiate(additional_item)
                }

            return ComponentArray(
                self.session,
                title=schema_title,
                description=schema_description,
                types=types,
                additionalType=additional_type
            )

        return super(Factory, self).__call__(schema, options=options)

    def _query_users(self):
        '''Return a list of valid users.'''
        users = []
        for user in self.session.ftrack.getUsers():
            entry = {
                'id': user.getId(),
                'username': user.get('username'),
                'firstname': user.get('firstname'),
                'lastname': user.get('lastname')
            }
            email = user.get('email')
            if email:
                entry['email'] = email

            users.append(entry)

        users = sorted(users, key=operator.itemgetter('firstname', 'lastname'))
        return map(partial(self.session.instantiate, 'harmony:/user'), users)

    def _query_scopes(self, scope, domain=None):
        '''Return list of entries for *scope* using *domain*.'''
        scopes = []
        if domain is None:
            domain = {}

        # TODO: Caching of values.
        if scope == 'show':
            shows = self.session.ftrack.getShows()
            for show in shows:
                scopes.append({
                    'name': show.getFullName(),
                    'id': show.getId()
                })

        elif scope == 'scene':
            show_id = domain.get('show', {}).get('id')
            if show_id is not None:
                show = self.session.ftrack.Show(show_id)

                children = show.getSequences()
                for child in children:
                    scopes.append({
                        'name': child.getName(),
                        'id': child.getId()
                    })

        elif scope == 'shot':
            parent_id = domain.get('scene', {}).get('id')
            if parent_id is not None:
                task = self.session.ftrack.Task(parent_id)
                children = task.getShots()

                for child in children:
                    scopes.append({
                        'name': child.getName(),
                        'id': child.getId()
                    })

        elif scope == 'asset':
            show_id = domain.get('show', {}).get('id')
            if show_id is not None:
                show = self.session.ftrack.Show(show_id)
                children = show.getAssetBuilds()

                for child in children:
                    scopes.append({
                        'name': child.getName(),
                        'id': child.getId()
                    })

        # Sort scopes alphabetically by name.
        scopes = sorted(scopes, key=operator.itemgetter('name'))

        return map(
            partial(
                self.session.instantiate, 'harmony:/scope/{0}'.format(scope)
            ),
            scopes
        )

    def onDomainChanged(self, sender, container):
        '''Update scope widgets based on domain.

        *sender* is the scope widget whose value has changed.
        *container* is the domain container widget that holds the scope
        widgets.

        '''
        domain = container.value()
        if domain is None:
            domain = {}

        children_by_name = {}
        for child in container.children:
            children_by_name[child['name']] = child['widget']

        show = children_by_name.get('show')
        scene = children_by_name.get('scene')
        shot = children_by_name.get('shot')

        dependants = ()
        if sender == show:
            dependants = ('scene', 'shot', 'asset')
        elif sender == scene:
            dependants = ('shot', 'asset')
        elif sender == shot:
            dependants = ('asset',)

        for scope in dependants:
            widget = children_by_name.get(scope)

            if widget is not None:
                widget.setModel(
                    TemplatedDictionaryList(
                        u'{name}', self._query_scopes(scope, domain)
                    )
                )
                break
