from importlib import import_module
from kivy.factory import Factory, FactoryException

Factory.unregister('RecycleViewBehavior')
Factory.unregister('RecycleView')
Factory.register('RecycleViewBehavior', module='kivy.uix.recycleview')
Factory.register('RecycleView', module='kivy.uix.recycleview')


def __getattr__(name):
    classes = Factory.classes
    if name not in classes:
        if name[0] == name[0].lower():
            # if trying to access attributes like checking for `bind`
            # then raise AttributeError
            raise AttributeError
        raise FactoryException('Unknown class <%s>' % name)

    item = classes[name]
    cls = item['cls']

    # No class to return, import the module
    if cls is None:
        if item['module']:
            module = import_module(item['module'], package='.')
            if not hasattr(module, name):
                raise FactoryException(
                    'No class named <%s> in module <%s>' % (
                        name, item['module']))
            cls = item['cls'] = getattr(module, name)

        elif item['baseclasses']:
            rootwidgets = []
            for basecls in item['baseclasses'].split('+'):
                rootwidgets.append(Factory.get(basecls))
            cls = item['cls'] = type(str(name), tuple(rootwidgets), {})

        else:
            raise FactoryException('No information to create the class')

    return cls

Factory.__getattr__ = Factory.get = __getattr__
