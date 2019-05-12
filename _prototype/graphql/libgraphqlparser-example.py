import sys

from graphql_parser import GraphQLAstVisitor, GraphQLParser

class Visitor(GraphQLAstVisitor.GraphQLAstVisitor):

    def __init__(self):
        self.level = 0

    def visit_document(self, node):
        print "\n--{}--".format('visit_document')
        print('document start')
        print 'node.get_definitions_size = ',node.get_definitions_size()
        return 1

    def visit_operation_definition(self, node):
        print "\n--{}--".format('visit_operation_definition')
        print 'node.get_directives_size = ', node.get_directives_size()
        if node.get_name() is not None:
            print 'node.get_name().get_value = ', node.get_name().get_value()
        else:
            print 'node.get_name = ', node.get_name()
        print 'node.get_operation = ', node.get_operation()
        print 'node.get_selection_set().get_selections_size = ', node.get_selection_set().get_selections_size()
        print 'node.get_variable_definitions_size = ', node.get_variable_definitions_size()
        return 1

    def visit_named_type(self, node):
        print "\n--{}--".format('visit_named_type')
        print 'node.get_name().get_value = ', node.get_name().get_value()
        return 1

    def visit_non_null_type(self, node):
        print(node.__class__)
        print dir(node)
        return 1

    def visit_variable_definition(self, node):
        print "\n--{}--".format('visit_variable_definition')
        print 'node.get_variable().get_name().get_value = ', node.get_variable().get_name().get_value()
        return 1

    def visit_selection_set(self, node):
        print "\n--{}--".format('visit_selection_set')
        print 'node.get_selections_size = ', node.get_selections_size()
        return 1

    def visit_selection(self, node):
        print(node.__class__)
        print dir(node)
        return 1

    def visit_field(self, node):
        print "\n--{}--".format('visit_field')
        if node.get_alias() is not None:
            print 'node.get_alias().get_value = ', node.get_alias().get_value()
        else:
            print 'node.get_alias = ', node.get_alias()
        print 'get_arguments_size = ', node.get_arguments_size()
        print 'get_directives_size = ', node.get_directives_size()
        if node.get_name() is not None:
            print 'node.get_name().get_value = ', node.get_name().get_value()
        else:
            print 'node.get_name = ', node.get_name()
        if node.get_selection_set() is not None:
            print 'node.get_selection_set().get_selections_size = ', node.get_selection_set().get_selections_size()
        else:
            print 'node.get_selection_set = ', node.get_selection_set()
        return 1

    def visit_argument(self, node):
        print "\n--{}--".format('visit_argument')
        print 'node.get_name().get_value = ', node.get_name().get_value()
        return 1

    def visit_fragment_spread(self, node):
        print "\n--{}--".format('visit_fragment_spread')
        print 'node.get_name().get_value = ', node.get_name().get_value()
        return 1

    def visit_inline_fragment(self, node):
        print "\n--{}--".format('visit_inline_fragment')
        print 'node.get_name().get_value = ', node.get_name().get_value()
        return 1

    def visit_fragment_definition(self, node):
        print "\n--{}--".format('visit_fragment_definition')
        print 'node.get_name().get_value = ', node.get_name().get_value()
        return 1

    def visit_variable(self, node):
        print "\n--{}--".format('visit_variable')
        print 'node.get_name().get_value = ', node.get_name().get_value()
        return 1

    def visit_object_field(self, node):
        print "\n--{}--".format('visit_object_field')
        print 'node.get_name().get_value = ', node.get_name().get_value()
        return 1

    def visit_directive(self, node):
        print "\n--{}--".format('visit_directive')
        print 'node.get_name().get_value = ', node.get_name().get_value()
        return 1

    def visit_int_value(self, node):
        print "\n--{}--".format('visit_int_value')
        print 'node.get_value = ', node.get_value()
        return 1

    def visit_string_value(self, node):
        print "\n--{}--".format('visit_string_value')
        print 'node.get_value = ', node.get_value()
        return 1

    # schema parser
    def visit_schema_definition(self, node):
        print(node.__class__)
        print dir(node)
        return 1

    def visit_scalar_type_definition(self, node):
        print(node.__class__)
        print dir(node)
        return 1

    def visit_enum_type_definition(self, node):
        print(node.__class__)
        print dir(node)
        return 1


if __name__ == '__main__':
    querys = [
        '''
        query FetchSomeIDQuery($someId: String!) {
          human(id: $someId) {
            name
          }
        }
        ''',
        '''
        mutation TestMutation {
          first: immediatelyChangeTheNumber(newNumber: 1) {
            theNumber
          }
        }
        ''',
        '''
        {
          luke: human(id: "1000") {
            name
            homePlanet
          }
          leia: human(id: "1003") {
            name
            homePlanet
          }
        }
        ''',
        '''
        {
          luke: human(id: "1000") {
            ...HumanFragment
          }
          leia: human(id: "1003") {
            ...HumanFragment
          }
        }
        fragment HumanFragment on Human {
          name
          homePlanet
        }
        ''',
        '''
        {
          luke: human(id: 1000) {
            bla
            bla2: blabla(id: 100){
                blax
                blay
                bla3: blablabla(id:10){
                 bb
                 bc
                }
            }
          }
        }
        ''',
        '''
        query Hero($episode: Episode, $withFriends: Boolean!) {
          hero(episode: $episode) {
            name
            friends @include(if: $withFriends) {
              name
            }
          }
        }
        ''',
        '''
        type Character {
          name: String!
          appearsIn: [Episode!]!
        }
        type Episode {
          name: String!
        }
        '''
    ]
    for query in querys:
        print query
        gp_ = GraphQLParser
        gp_.enableSchema = True
        node = gp_.graphql_parse_string(query)
        Visitor().visit_node(node)
