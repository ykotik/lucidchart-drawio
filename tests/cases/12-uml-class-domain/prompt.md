# UML Class Diagram – E-Commerce Domain Model

Create a UML class diagram for an e-commerce domain model showing inheritance, composition, aggregation, and association relationships.

## Classes

1. **Person** (abstract) – id: Long, firstName: String, lastName: String, email: String, phone: String
2. **Customer** (extends Person) – loyaltyPoints: Int, registeredAt: Date, getFullName(): String
3. **Employee** (extends Person) – employeeId: String, department: String, hireDate: Date, salary: Double
4. **Order** – orderId: Long, orderDate: Date, status: OrderStatus, totalAmount: Double, place(): void, cancel(): void
5. **OrderLine** – lineId: Long, quantity: Int, unitPrice: Double, getSubtotal(): Double
6. **Product** – productId: Long, name: String, description: String, sku: String, price: Double, weight: Double
7. **Category** – categoryId: Long, name: String, description: String, parentCategory: Category
8. **Payment** – paymentId: Long, amount: Double, method: PaymentMethod, status: PaymentStatus, processedAt: Date
9. **Shipment** – shipmentId: Long, trackingNumber: String, carrier: String, shippedAt: Date, deliveredAt: Date
10. **Address** – addressId: Long, street: String, city: String, state: String, zipCode: String, country: String
11. **Review** – reviewId: Long, rating: Int, comment: String, createdAt: Date
12. **Discount** – discountId: Long, code: String, percentage: Double, validFrom: Date, validTo: Date, isValid(): Boolean
13. **Inventory** – inventoryId: Long, quantity: Int, warehouseLocation: String, reorderLevel: Int, restock(): void
14. **Supplier** – supplierId: Long, companyName: String, contactName: String, contactEmail: String

## Relationships

- Customer ──▷ Person (inheritance / generalization)
- Employee ──▷ Person (inheritance / generalization)
- Customer "1" ──── "0..*" Order (association: places)
- Order "1" ◆── "1..*" OrderLine (composition: contains)
- OrderLine "0..*" ──── "1" Product (association: references)
- Product "0..*" ──── "1..*" Category (association: belongs to)
- Category "0..1" ──── "0..*" Category (self-association: parent)
- Order "1" ──── "0..1" Payment (association: paid by)
- Order "1" ──── "0..1" Shipment (association: shipped via)
- Order "1" ◇── "1" Address (aggregation: shipping address)
- Customer "1" ◇── "1..*" Address (aggregation: has addresses)
- Customer "1" ──── "0..*" Review (association: writes)
- Review "0..*" ──── "1" Product (association: reviews)
- Order "0..*" ──── "0..1" Discount (association: applies)
- Product "1" ──── "1" Inventory (association: tracked by)
- Supplier "1" ──── "0..*" Product (association: supplies)
- Employee "0..*" ──── "0..*" Order (association: manages)
- Shipment "1" ◇── "1" Address (aggregation: destination)
- Employee "1" ◇── "1" Address (aggregation: work address)
- Payment "1" ──── "1" Order (association: for order)

Arrange with Person hierarchy at top, Order cluster in the center, and Product/Supplier/Inventory on the right.
