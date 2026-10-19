package example;

import java.util.ArrayList;
import java.util.List;

/** Holds order lines and computes the order total using a PriceCalculator. */
public class OrderService {

    private final PriceCalculator calculator;
    private final List<double[]> lines = new ArrayList<>();

    public OrderService(PriceCalculator calculator) {
        this.calculator = calculator;
    }

    public void addLine(double unitPrice, int quantity) {
        lines.add(new double[] {unitPrice, quantity});
    }

    public int lineCount() {
        return lines.size();
    }

    public double total() {
        double subtotal = 0.0;
        for (double[] line : lines) {
            subtotal += calculator.linePrice(line[0], (int) line[1]);
        }
        return calculator.applyDiscount(subtotal);
    }
}
