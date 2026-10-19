package example;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;

class PriceCalculatorTest {

    @Test
    void linePriceMultipliesUnitPriceByQuantity() {
        assertEquals(30.0, new PriceCalculator(0.0).linePrice(10.0, 3), 1e-9);
    }

    @Test
    void negativeQuantityIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new PriceCalculator(0.0).linePrice(10.0, -1));
    }

    @Test
    void discountIsApplied() {
        assertEquals(90.0, new PriceCalculator(0.1).applyDiscount(100.0), 1e-9);
    }

    @Test
    void invalidDiscountRateIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new PriceCalculator(1.5));
    }
}
