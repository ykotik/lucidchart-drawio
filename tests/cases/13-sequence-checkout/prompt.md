# Sequence Diagram – E-Commerce Checkout Flow

Create a sequence diagram showing the complete checkout flow for an e-commerce application with microservice architecture.

## Lifelines (Participants)

1. **Browser** – The customer's web browser
2. **API Gateway** – Central entry point and request router
3. **Cart Service** – Manages shopping cart state
4. **Order Service** – Handles order creation and lifecycle
5. **Payment Service** – Processes payments via external provider
6. **Inventory Service** – Tracks product stock levels
7. **Notification Service** – Sends emails and push notifications

## Message Flow

1. Browser → API Gateway: initiateCheckout()
2. API Gateway → Cart Service: getCart(userId)
3. Cart Service → API Gateway: cartDetails
4. API Gateway → Cart Service: validateCart(cartId)
5. Cart Service → Inventory Service: checkAvailability(items)
6. Inventory Service → Cart Service: availabilityResult
7. Cart Service → API Gateway: validationResult
8. API Gateway → Order Service: createOrder(cartDetails, shippingInfo)
9. Order Service → Inventory Service: reserveInventory(items)
10. Inventory Service → Order Service: reservationConfirmed
11. Order Service → API Gateway: orderCreated(orderId)
12. API Gateway → Payment Service: processPayment(orderId, paymentDetails)
13. Payment Service → API Gateway: paymentResult

### Alt Fragment: Payment Success / Failure

**[Payment Success]**
14. API Gateway → Order Service: confirmOrder(orderId)
15. Order Service → Inventory Service: commitReservation(orderId)
16. Inventory Service → Order Service: inventoryUpdated
17. Order Service → Notification Service: sendOrderConfirmation(orderId, email)
18. Notification Service → Order Service: notificationSent
19. Order Service → API Gateway: orderConfirmed
20. API Gateway → Browser: checkoutSuccess(orderSummary)

**[Payment Failure]**
21. API Gateway → Order Service: cancelOrder(orderId)
22. Order Service → Inventory Service: releaseReservation(orderId)
23. Inventory Service → Order Service: reservationReleased
24. Order Service → API Gateway: orderCancelled
25. API Gateway → Browser: checkoutFailed(errorDetails)

### Opt Fragment: Send Shipping Notification
26. Notification Service → Browser: pushNotification(shippingUpdate)

Show activation bars on each lifeline and clearly label the alt/opt fragments.
