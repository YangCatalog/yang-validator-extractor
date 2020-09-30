from pyang.statements import *


class StatementsDefault:
    def __init__(self):
        self._validation_map = {
            ('init', 'module'): lambda ctx, s: v_init_module(ctx, s),
            ('init', 'submodule'): lambda ctx, s: v_init_module(ctx, s),
            ('init', '$extension'): lambda ctx, s: v_init_extension(ctx, s),
            ('init2', 'import'): lambda ctx, s: v_init_import(ctx, s),
            ('init2', '$has_children'): lambda ctx, s: v_init_has_children(ctx, s),
            ('init2', '*'): lambda ctx, s: v_init_stmt(ctx, s),

            ('grammar', 'module'): lambda ctx, s: v_grammar_module(ctx, s),
            ('grammar', 'submodule'): lambda ctx, s: v_grammar_module(ctx, s),
            ('grammar', 'typedef'): lambda ctx, s: v_grammar_typedef(ctx, s),
            ('grammar', '*'): lambda ctx, s: v_grammar_all(ctx, s),

            ('import', 'module'): lambda ctx, s: v_import_module(ctx, s),
            ('import', 'submodule'): lambda ctx, s: v_import_module(ctx, s),

            ('type', 'grouping'): lambda ctx, s: v_type_grouping(ctx, s),
            ('type', 'augment'): lambda ctx, s: v_type_augment(ctx, s),
            ('type', 'uses'): lambda ctx, s: v_type_uses(ctx, s),
            ('type', 'feature'): lambda ctx, s: v_type_feature(ctx, s),
            ('type', 'if-feature'): lambda ctx, s: v_type_if_feature(ctx, s),
            ('type', 'identity'): lambda ctx, s: v_type_identity(ctx, s),
            ('type', 'status'): lambda ctx, s: v_type_status(ctx, s),
            ('type', 'base'): lambda ctx, s: v_type_base(ctx, s),
            ('type', 'must'): lambda ctx, s: v_type_must(ctx, s),
            ('type', 'when'): lambda ctx, s: v_type_when(ctx, s),
            ('type', '$extension'): lambda ctx, s: v_type_extension(ctx, s),

            ('type_2', 'type'): lambda ctx, s: v_type_type(ctx, s),
            ('type_2', 'typedef'): lambda ctx, s: v_type_typedef(ctx, s),
            ('type_2', 'leaf'): lambda ctx, s: v_type_leaf(ctx, s),
            ('type_2', 'leaf-list'): lambda ctx, s: v_type_leaf_list(ctx, s),

            ('expand_1', 'module'): lambda ctx, s: v_expand_1_children(ctx, s),
            ('expand_1', 'submodule'): lambda ctx, s: v_expand_1_children(ctx, s),

            ('inherit_properties', 'module'): \
                lambda ctx, s: v_inherit_properties(ctx, s),
            ('inherit_properties', 'submodule'): \
                lambda ctx, s: v_inherit_properties(ctx, s),

            ('expand_2', 'augment'): lambda ctx, s: v_expand_2_augment(ctx, s),

            ('unique_name', 'module'): \
                lambda ctx, s: v_unique_name_defintions(ctx, s),
            ('unique_name', '$has_children'): \
                lambda ctx, s: v_unique_name_children(ctx, s),
            ('unique_name', 'leaf-list'): \
                lambda ctx, s: v_unique_name_leaf_list(ctx, s),

            ('reference_1', 'list'): lambda ctx, s: v_reference_list(ctx, s),
            ('reference_1', 'action'): lambda ctx, s: v_reference_action(ctx, s),
            ('reference_1', 'notification'): lambda ctx, s: v_reference_action(ctx, s),
            ('reference_1', 'choice'): lambda ctx, s: v_reference_choice(ctx, s),
            ('reference_2', 'leaf'): lambda ctx, s: v_reference_leaf_leafref(ctx, s),
            ('reference_2', 'leaf-list'): lambda ctx, s: v_reference_leaf_leafref(ctx, s),
            ('reference_2', 'must'): lambda ctx, s: v_reference_must(ctx, s),
            ('reference_2', 'when'): lambda ctx, s: v_reference_when(ctx, s),
            ## since we just check in reference_2, it means that we won't check
            ## xpaths in unused groupings.  the xpath is checked when the grouping is
            ## used.  the same is true for leafrefs
            #    ('reference_3', 'must'):lambda ctx, s:v_reference_must(ctx, s),
            #    ('reference_3', 'when'):lambda ctx, s:v_reference_when(ctx, s),
            ('reference_3', 'typedef'): lambda ctx, s: v_reference_leaf_leafref(ctx, s),
            ('reference_3', 'deviation'): lambda ctx, s: v_reference_deviation(ctx, s),
            ('reference_3', 'deviate'): lambda ctx, s: v_reference_deviate(ctx, s),
            ('reference_4', 'deviation'): lambda ctx, s: v_reference_deviation_4(ctx, s),

            ('unused', 'module'): lambda ctx, s: v_unused_module(ctx, s),
            ('unused', 'submodule'): lambda ctx, s: v_unused_module(ctx, s),
            ('unused', 'typedef'): lambda ctx, s: v_unused_typedef(ctx, s),
            ('unused', 'grouping'): lambda ctx, s: v_unused_grouping(ctx, s),
        }
        self.data_definition_keywords = ['container', 'leaf', 'leaf-list', 'list', 'case',
                                    'choice', 'anyxml', 'anydata', 'uses', 'augment']

        self._validation_phases = [
            # init phase:
            #   initalizes the module/submodule statement, and maps
            #   the prefix in all extensions to their modulename
            #   from this point, extensions will be validated just as the
            #   other statements
            'init',
            # second init phase initializes statements, including extensions
            'init2',

            # grammar phase:
            #   verifies that the statement hierarchy is correct
            #   and that all arguments are of correct type
            #   complex arguments are parsed and saved in statement-specific
            #   variables
            'grammar',

            # import and include phase:
            #   tries to load each imported and included (sub)module
            'import',

            # type and grouping phase:
            #   verifies all typedefs, types and groupings
            'type',
            'type_2',

            # expansion phases:
            #   first expansion: copy data definition stmts into i_children
            'expand_1',

            # inherit properties phase:
            #   set i_config
            'inherit_properties',

            #   second expansion: expand augmentations into i_children
            'expand_2',

            # unique name check phase:
            'unique_name',

            # reference phase:
            #   verifies all references; e.g. leafref, unique, key for config
            'reference_1',
            'reference_2',
            'reference_3',
            'reference_4',

            # unused definitions phase:
            #   add warnings for unused definitions
            'unused',

            # strict phase: check YANG strictness
            'strict',
        ]

        self._v_i_children = {
            'unique_name': True,
            'expand_2': True,
            'reference_1': True,
            'reference_2': True,
        }
        """Phases in this dict are run over the stmts which has i_children.
        Note that the tests are not run in grouping definitions."""

        self._v_i_children_keywords = {
            ('reference_2', 'when'): True,
            ('reference_2', 'must'): True,
        }
        """Keywords in this dict are iterated over in a phase in _v_i_children."""

        self._keyword_with_children = {
            'module':True,
            'submodule':True,
            'container':True,
            'list':True,
            'case':True,
            'choice':True,
            'grouping':True,
            'uses':True,
            'augment':True,
            'input':True,
            'output':True,
            'notification':True,
            'rpc':True,
            'action':True,
        }

        self.data_keywords = ['leaf', 'leaf-list', 'container', 'list', 'choice', 'case',
                            'anyxml', 'anydata', 'action', 'rpc', 'notification']

        self._keywords_with_no_explicit_config = ['action', 'rpc', 'notification']

        self._copy_uses_keywords = []

        self._copy_augment_keywords = []

        self._refinements = [
            # (<keyword>, <list of keywords for which <keyword> can be refined>,
            #  <merge>, <validation function>)
            ('description',
                ['container', 'leaf', 'leaf-list', 'list', 'choice', 'case',
                'anyxml', 'anydata'],
                False, None),
            ('reference',
                ['container', 'leaf', 'leaf-list', 'list', 'choice', 'case',
                'anyxml', 'anydata'],
                False, None),
            ('config',
                ['container', 'leaf', 'leaf-list', 'list', 'choice', 'anyxml', 'anydata'],
                False, None),
            ('presence', ['container'], False, None),
            ('must', ['container', 'leaf', 'leaf-list', 'list', 'anyxml', 'anydata'],
                True, None),
            ('default', ['leaf', ('$1.1', 'leaf-list'), 'choice'],
                False, lambda ctx, target, default: v_default(ctx, target, default)),
            ('mandatory', ['leaf', 'choice', 'anyxml', 'anydata'], False, None),
            ('min-elements', ['leaf-list', 'list'], False, None),
            ('max-elements', ['leaf-list', 'list'], False, None),
            ('if-feature',
                ['container', 'leaf', 'leaf-list', 'list', 'choice', 'case',
                'anyxml', 'anydata'],
                True, None),
        ]

        self._singleton_keywords = {
            'type': True,
            'units': True,
            'default': True,
            'config': True,
            'mandatory': True,
            'min-elements': True,
            'max-elements': True
        }

        self._deviate_delete_singleton_keywords = {
            'units': True,
            'default': True
        }

        self._valid_deviations = {
            'type': ['leaf', 'leaf-list'],
            'units': ['leaf', 'leaf-list'],
            'default': ['leaf', 'leaf-list', 'choice'],
            'config': ['leaf', 'choice', 'container', 'list', 'leaf-list'],
            'mandatory': ['leaf', 'choice'],
            'min-elements': ['leaf-list', 'list'],
            'max-elements': ['leaf-list', 'list'],
            'must': ['leaf', 'choice', 'container', 'list', 'leaf-list'],
            'unique': ['list'],
        }

        self.STMT_CLASS_FOR_KEYWD = {
            'module': ModSubmodStatement,
            'submodule': ModSubmodStatement,

            'augment': AugmentStatement,
            'base': BaseStatement,
            'bit': BitStatement,
            'choice': ChoiceStatement,
            'container': ContainerStatement,
            'deviation': DeviationStatement,
            'enum': EnumStatement,
            'grouping': GroupingStatement,
            'import': ImportStatement,
            'leaf': LeafLeaflistStatement,
            'leaf-list': LeafLeaflistStatement,
            'list': ListStatement,
            'type': TypeStatement,
            'typedef': TypedefStatement,
            'unique': UniqueStatement,
            'uses': UsesStatement,
            'must': MustStatement,
            'when': WhenStatement,
            '_comment': CommentStatement,
            # all other keywords can use generic Statement class
        }
