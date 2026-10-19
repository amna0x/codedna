package example;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class OrderServiceTest {

    @Test
    void emptyOrderTotalsZero() {
        assertEquals(0.0, new OrderService(new PriceCalculator(0.0)).total(), 1e-9);
    }

    @Test
    void totalSumsLinesAndAppliesDiscount() {
        OrderService orders = new OrderService(new PriceCalculator(0.5));
        orders.addLine(10.0, 2);
        orders.addLine(5.0, 4);
        assertEquals(2, orders.lineCount());
        assertEquals(20.0, orders.total(), 1e-9);
    }
}
