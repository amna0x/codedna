package example;

/** Computes line prices and discounts. */
public class PriceCalculator {

    private final double discountRate;

    public PriceCalculator(double discountRate) {
        if (discountRate < 0.0 || discountRate > 1.0) {
            throw new IllegalArgumentException("discountRate must be between 0 and 1");
        }
        this.discountRate = discountRate;
    }

    public double linePrice(double unitPrice, int quantity) {
        if (quantity < 0) {
            throw new IllegalArgumentException("quantity must not be negative");
        }
        return unitPrice * quantity;
    }

    public double applyDiscount(double amount) {
        return amount * (1.0 - discountRate);
    }
}
