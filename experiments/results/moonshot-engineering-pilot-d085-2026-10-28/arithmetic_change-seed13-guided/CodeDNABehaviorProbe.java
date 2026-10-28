import java.lang.reflect.*;
public final class CodeDNABehaviorProbe {
  public static void main(String[] args) throws Exception {
    try {
      Method method = Class.forName(args[0]).getDeclaredMethod(args[1], int.class);
      if (!Modifier.isPublic(method.getModifiers()) || !Modifier.isStatic(method.getModifiers())
          || method.getReturnType() != int.class) throw new IllegalArgumentException("unsupported method");
      int result = (Integer)method.invoke(null, Integer.parseInt(args[2]));
      System.out.println(args[3] + "value:" + result);
    } catch (InvocationTargetException ex) {
      System.out.println(args[3] + "throw:" + ex.getCause().getClass().getName());
    }
  }
}
