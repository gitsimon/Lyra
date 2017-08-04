from z3 import ArithRef, Const, IntSort

class ClassNode:
    """
    Class representing a node in a tree where each node represents a class, and has
    references to the base class and subclasses.
    """

    def __init__(self, name, parent_node, type_sort):
        self.name = name
        self.parent_node = parent_node
        self.children = []
        self.type_sort = type_sort
        self._qf = None

    def find(self, name):
        """
        Looks a class with the given name in the tree starting at this node. If there is
        no such class, returns None.
        """
        if name == self.name:
            return self
        for c in self.children:
            res = c.find(name)
            if res:
                return res

    def __str__(self):
        return str(self.name)

    def all_children(self):
        """
        Returns all transitive child nodes.
        """
        result = [self]
        for c in self.children:
            result += c.all_children()
        return result

    def all_super(self):
        """
        Returns all transitive parent nodes.
        """
        result = [self]
        if self.parent_node:
            result += self.parent_node.all_super()
        return result

    def get_literal(self, transformer = None):
        """
        Creates a Z3 expression representing this type. If this is a generic type,
        will use the variables from self.quantified() as the type arguments.
        """
        if isinstance(self.name, str):
            return getattr(self.type_sort, self.name)
        else:
            constr = getattr(self.type_sort, self.name[0])
            args = self.quantified()
            if transformer:
                args = [transformer(a) if not isinstance(a, ArithRef) else a for a in args]
            return constr(*args)

    def get_literal_with_args(self, var):
        """
        Creates a Z3 expression representing this type. If this is a generic type, will
        use the accessor methods for the type arguments and apply them to the given
        variable argument to get the arguments.
        """
        if isinstance(self.name, str):
            return getattr(self.type_sort, self.name)
        else:
            constr = getattr(self.type_sort, self.name[0])
            args = []
            for arg in self.name[1:]:
                args.append(getattr(self.type_sort, arg)(var))
            return constr(*args)

    def quantified(self):
        """
        Returns a list of Z3 variables, one for each parameter of this type.
        """
        if self._qf is not None:
            return self._qf
        res = []
        if isinstance(self.name, tuple):
            for i, arg in enumerate(self.name[1:]):
                sort = self.type_sort if not arg.endswith('defaults_args') else IntSort()
                cur = Const("y" + str(i), sort)
                res.append(cur)
        self._qf = res
        return res