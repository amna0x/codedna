import java.lang.reflect.*;
public final class CodeDNABehaviorProbe {
  public static void main(String[] args) throws Exception {
    try {
      String[] kinds = args.length > 4 ? args[4].split(",") : new String[]{"int"};
      String[] inputs = args[2].split(":", -1);
      if (kinds.length < 1 || kinds.length > 2 || inputs.length != kinds.length)
        throw new IllegalArgumentException("unsupported input arity");
      Class<?>[] types = new Class<?>[kinds.length];
      Object[] values = new Object[kinds.length];
      for (int i=0; i<kinds.length; i++) {
        switch (kinds[i]) {
          case "int": types[i]=int.class; values[i]=Integer.parseInt(inputs[i]); break;
          case "long": types[i]=long.class; values[i]=Long.parseLong(inputs[i]); break;
          case "int[]": case "int...": types[i]=int[].class;
            values[i]=inputs[i].isEmpty() ? new int[0] : java.util.Arrays.stream(inputs[i].split(",")).mapToInt(Integer::parseInt).toArray(); break;
          case "boolean": types[i]=boolean.class;
            if (!inputs[i].equals("true") && !inputs[i].equals("false")) throw new IllegalArgumentException("boolean");
            values[i]=Boolean.parseBoolean(inputs[i]); break;
          case "String": types[i]=String.class;
            values[i]=new String(java.util.Base64.getDecoder().decode(inputs[i]), java.nio.charset.StandardCharsets.UTF_8); break;
          default: throw new IllegalArgumentException("unsupported argument type");
        }
      }
      Method method = Class.forName(args[0]).getDeclaredMethod(args[1], types);
      if (!Modifier.isPublic(method.getModifiers())
          || (method.getReturnType() != int.class && method.getReturnType() != long.class && method.getReturnType() != int[].class)) throw new IllegalArgumentException("unsupported method");
      
      Object receiver = Modifier.isStatic(method.getModifiers()) ? null : method.getDeclaringClass().getConstructor().newInstance();
      Object result = method.invoke(receiver, values);
      if (result instanceof int[]) {
        if (((int[])result).length > 128) throw new IllegalArgumentException("array result exceeds limit");
        System.out.println(args[3]+"value:"+java.util.Arrays.toString((int[])result).replace(" ",""));
        return;
      }
      long numericResult = ((Number)result).longValue();
      System.out.println(args[3] + "value:" + numericResult);
    } catch (InvocationTargetException ex) {
      System.out.println(args[3] + "throw:" + ex.getCause().getClass().getName());
    }
  }
}
