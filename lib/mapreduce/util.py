#!/usr/bin/env python
#
# Copyright 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility functions for use with the mapreduce library."""

# pylint: disable=g-bad-name



__all__ = [
    "create_datastore_write_config",
    "for_name",
    "get_short_name",
    "handler_for_name",
    "is_generator",
    "parse_bool",
    "total_seconds",
    "try_serialize_handler",
    "try_deserialize_handler",
    ]

import inspect
import pickle
import types

from google.appengine.datastore import datastore_rpc


def _enum(**enums):
  """Helper to create enum."""
  return type("Enum", (), enums)


def total_seconds(td):
  """convert a timedelta to seconds.

  This is patterned after timedelta.total_seconds, which is only
  available in python 27.

  Args:
    td: a timedelta object.

  Returns:
    total seconds within a timedelta. Rounded up to seconds.
  """
  secs = td.seconds + td.days * 24 * 3600
  if td.microseconds:
    secs += 1
  return secs


def for_name(fq_name, recursive=False):
  """Find class/function/method specified by its fully qualified name.

  Fully qualified can be specified as:
    * <module_name>.<class_name>
    * <module_name>.<function_name>
    * <module_name>.<class_name>.<method_name> (an unbound method will be
      returned in this case).

  for_name works by doing __import__ for <module_name>, and looks for
  <class_name>/<function_name> in module's __dict__/attrs. If fully qualified
  name doesn't contain '.', the current module will be used.

  Args:
    fq_name: fully qualified name of something to find

  Returns:
    class object.

  Raises:
    ImportError: when specified module could not be loaded or the class
    was not found in the module.
  """
#  if "." not in fq_name:
#    raise ImportError("'%s' is not a full-qualified name" % fq_name)

  fq_name = str(fq_name)
  module_name = __name__
  short_name = fq_name

  if fq_name.rfind(".") >= 0:
    (module_name, short_name) = (fq_name[:fq_name.rfind(".")],
                                 fq_name[fq_name.rfind(".") + 1:])

  try:
    result = __import__(module_name, None, None, [short_name])
    return result.__dict__[short_name]
  except KeyError:
    # If we're recursively inside a for_name() chain, then we want to raise
    # this error as a key error so we can report the actual source of the
    # problem. If we're *not* recursively being called, that means the
    # module was found and the specific item could not be loaded, and thus
    # we want to raise an ImportError directly.
    if recursive:
      raise
    else:
      raise ImportError("Could not find '%s' on path '%s'" % (
                        short_name, module_name))
  except ImportError:
    # module_name is not actually a module. Try for_name for it to figure
    # out what's this.
    try:
      module = for_name(module_name, recursive=True)
      if hasattr(module, short_name):
        return getattr(module, short_name)
      else:
        # The module was found, but the function component is missing.
        raise KeyError()
    except KeyError:
      raise ImportError("Could not find '%s' on path '%s'" % (
                        short_name, module_name))
    except ImportError:
      # This means recursive import attempts failed, thus we will raise the
      # first ImportError we encountered, since it's likely the most accurate.
      pass
    # Raise the original import error that caused all of this, since it is
    # likely the real cause of the overall problem.
    raise


def handler_for_name(fq_name):
  """Resolves and instantiates handler by fully qualified name.

  First resolves the name using for_name call. Then if it resolves to a class,
  instantiates a class, if it resolves to a method - instantiates the class and
  binds method to the instance.

  Args:
    fq_name: fully qualified name of something to find.

  Returns:
    handler instance which is ready to be called.
  """
  resolved_name = for_name(fq_name)
  if isinstance(resolved_name, (type, types.ClassType)):
    # create new instance if this is type
    return resolved_name()
  elif isinstance(resolved_name, types.MethodType):
    # bind the method
    return getattr(resolved_name.im_class(), resolved_name.__name__)
  else:
    return resolved_name


def try_serialize_handler(handler):
  """Try to serialize map/reduce handler.

  Args:
    handler: handler function/instance. Handler can be a function or an
      instance of a callable class. In the latter case, the handler will
      be serialized across slices to allow users to save states.

  Returns:
    serialized handler string or None.
  """
  if (isinstance(handler, types.InstanceType) or  # old style class
      (isinstance(handler, object) and  # new style class
       not inspect.isfunction(handler) and
       not inspect.ismethod(handler)) and
      hasattr(handler, "__call__")):
    return pickle.dumps(handler)
  return None


def try_deserialize_handler(serialized_handler):
  """Reverse function of try_serialize_handler.

  Args:
    serialized_handler: serialized handler str or None.

  Returns:
    handler instance or None.
  """
  if serialized_handler:
    return pickle.loads(serialized_handler)


def is_generator(obj):
  """Return true if the object is generator or generator function.

  Generator function objects provides same attributes as functions.
  See isfunction.__doc__ for attributes listing.

  Adapted from Python 2.6.

  Args:
    obj: an object to test.

  Returns:
    true if the object is generator function.
  """
  if isinstance(obj, types.GeneratorType):
    return True

  CO_GENERATOR = 0x20
  return bool(((inspect.isfunction(obj) or inspect.ismethod(obj)) and
               obj.func_code.co_flags & CO_GENERATOR))


def get_short_name(fq_name):
  """Returns the last component of the name."""
  return fq_name.split(".")[-1:][0]


def parse_bool(obj):
  """Return true if the object represents a truth value, false otherwise.

  For bool and numeric objects, uses Python's built-in bool function.  For
  str objects, checks string against a list of possible truth values.

  Args:
    obj: object to determine boolean value of; expected

  Returns:
    Boolean value according to 5.1 of Python docs if object is not a str
      object.  For str objects, return True if str is in TRUTH_VALUE_SET
      and False otherwise.
    http://docs.python.org/library/stdtypes.html
  """
  if type(obj) is str:
    TRUTH_VALUE_SET = ["true", "1", "yes", "t", "on"]
    return obj.lower() in TRUTH_VALUE_SET
  else:
    return bool(obj)


def create_datastore_write_config(mapreduce_spec):
  """Creates datastore config to use in write operations.

  Args:
    mapreduce_spec: current mapreduce specification as MapreduceSpec.

  Returns:
    an instance of datastore_rpc.Configuration to use for all write
    operations in the mapreduce.
  """
  force_writes = parse_bool(mapreduce_spec.params.get("force_writes", "false"))
  if force_writes:
    return datastore_rpc.Configuration(force_writes=force_writes)
  else:
    # dev server doesn't support force_writes.
    return datastore_rpc.Configuration()
