"""Bounded normal-return observations, independent of test skipping policy."""
import json

MAX_ARRAY_RESULT = 128


def normal_value(text):
    value = json.loads(text)
    if type(value) is int and -(2**63) <= value < 2**63:
        return value
    if isinstance(value, list) and len(value) <= MAX_ARRAY_RESULT and all(
            type(item) is int and -(2**31) <= item < 2**31 for item in value):
        return value
    raise ValueError('Only signed integer or bounded int-array normal results are supported')


def canonical(value):
    text = json.dumps(value, separators=(',', ':'), allow_nan=False)
    normal_value(text)
    return text


def instance_array_probe(original):
    """Extend the pinned probe without changing numeric output syntax."""
    original = original.replace('!Modifier.isPublic(method.getModifiers()) || !Modifier.isStatic(method.getModifiers())',
                                 '!Modifier.isPublic(method.getModifiers())')
    original = original.replace('method.getReturnType() != long.class)',
                                 'method.getReturnType() != long.class && method.getReturnType() != int[].class)')
    original = original.replace('long result = ((Number)method.invoke(null, values)).longValue();', '''
      Object receiver = Modifier.isStatic(method.getModifiers()) ? null : method.getDeclaringClass().getConstructor().newInstance();
      Object result = method.invoke(receiver, values);
      if (result instanceof int[]) {
        if (((int[])result).length > 128) throw new IllegalArgumentException("array result exceeds limit");
        System.out.println(args[3]+"value:"+java.util.Arrays.toString((int[])result).replace(" ",""));
        return;
      }
      long numericResult = ((Number)result).longValue();''')
    return original.replace('"value:" + result', '"value:" + numericResult')
